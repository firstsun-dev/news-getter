# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

An automated AI news aggregation pipeline that fetches RSS feeds, scores stories deterministically by source tier/corroboration, runs AI-powered summarization via the local Gemini CLI only on stories that clear the evidence gate, and publishes results as an Astro-built static site (GitHub Pages) and RSS feed. The data-fetch pipeline runs twice daily via a **self-hosted macOS GitHub Actions runner**; a separate build-deploy workflow builds Astro on `ubuntu-latest` and deploys `dist/` to Pages. See `docs/specs/2026-07-19-astro-site-redesign/` for the current design.

## Running the Pipeline

```bash
# Full pipeline (fetch → summarize → data JSON → Astro build → dist/)
./run_pipeline.sh

# Python only (no Astro build) — used by the data-fetch CI workflow
./run_pipeline.sh data-only

# Individual steps
source .venv/bin/activate
PYTHONPATH=. python3 src/fetch.py           # outputs data/raw_data.json, upserts data/news.db
PYTHONPATH=. python3 src/summarizer.py      # outputs summary.md + history/<timestamp>/*.md
PYTHONPATH=. python3 src/build_site.py      # outputs data/site_data.json, data/history_index.json, data/YYYY/MM/*.json

# Astro build (reads data/, bakes HTML into dist/)
cd astro-src && npm ci && npm run build

# Unit tests
PYTHONPATH=. python3 -m unittest discover -s test -v
```

The pipeline auto-creates `.venv` on first run.

## Architecture: Three Stages + Astro Build

**Stage 1 — `src/fetch.py`**: Reads `config/feeds.yaml` (each source has `tier` 1-4 and `role`), fetches each RSS feed (15-hour lookback window), resolves relative links against the feed URL, strips HTML, truncates content to 1200 chars. Every article is upserted into `data/news.db` (SQLite, via `src/store.py`) keyed by a title/URL fingerprint, accumulating `seen_count` and distinct `sources`. Writes the enriched articles (with `tier`/`role`/`seen_count`/`sources`) to `data/raw_data.json` as `{category: [articles]}`.

**Stage 2 — `src/summarizer.py`**: Reads `data/raw_data.json`, groups articles per category by fingerprint into stories, and scores each with `scoring.score_story()` (deterministic — tier authority + distinct sources + seen_count; see `src/scoring.py`). Only stories with `confidence >= 60` or `heat >= 60` are sent to Gemini, one call per qualifying story, with a fixed input allowlist (title/URL/category/cleaned content/accumulated tier+source evidence). Gemini must return pure JSON matching `StoryDigest` (`fact_summary`, `judgment`, `used_source_urls`); `src/summarizer.py` validates it with Pydantic — schema bounds, placeholder-word regex, and `used_source_urls` must be a subset of the story's own input URLs. Any failure discards that story (logged, doesn't stop others) and it falls back to the headline-only "觀察中" list. Categories with zero qualifying stories skip Gemini entirely. Output: `history/<timestamp>/<Category>.md` per category, `summary.md` across all categories.

The Gemini binary is located via PATH, a hardcoded list of known paths, then a filesystem search as a last resort.

**Stage 3 — `src/build_site.py`** (data-prep only): Parses `summary.md` and `history/*/*.md` into JSON under `data/`: `data/site_data.json` (current run's categories/stories/watchlist), `data/history_index.json` (date → runs → category names), and `data/YYYY/MM/YYYY-MM-DD.json` (per-day full content). It no longer emits any HTML or RSS — that is Astro's job. RSS moved to `@astrojs/rss` inside Astro.

**Stage 4 — Astro build** (`astro-src/`): Reads `data/*.json` and `data/YYYY/MM/*.json` at build time and bakes all content into static HTML under `dist/`: `index.html` (homepage with sidebar, category cards, faceted archive browser), `history/<date>_<time>/index.html` (one per run), and `rss.xml`. No runtime JSON fetch for primary content — the archive index is serialized into the `ArchiveBrowser` island as baked props. Build output `dist/` is gitignored and deployed as a CI artifact, never committed.

## Key Files

| File | Purpose |
|------|---------|
| `config/feeds.yaml` | RSS source list with `tier`/`role` — edit here to add/remove feeds or change categories/tiering |
| `src/store.py` | SQLite persistence (`data/news.db`, gitignored) — `upsert_story`/`stories_since` for dedup and evidence accumulation |
| `src/scoring.py` | Deterministic `score_story()` confidence/heat formula and the deep-analysis threshold |
| `src/summarizer.py` | Gemini prompts, `StoryDigest` Pydantic schema, and the validation gate — edit here to change summarization style or schema |
| `src/build_site.py` | Data-prep only — parses `summary.md`/`history/*.md` into `data/*.json`; emits no HTML |
| `data/raw_data.json` | Intermediate artifact for this run's fetch; not the source of truth for dedup (that's `data/news.db`) |
| `data/site_data.json` | Current run's full content — read by Astro `index.astro` at build time (pushed to `main`) |
| `data/history_index.json` | Date→runs→category-names index — baked into the `ArchiveBrowser` island as props (pushed to `main`) |
| `data/YYYY/MM/*.json` | Per-day full content — read by `[run]/index.astro` via `getStaticPaths` (pushed to `main`) |
| `summary.md` | Main summary, parsed by `build_site.py`; also read by `rss.xml.ts` |
| `history/<timestamp>/*.md` | Per-run archive of per-category deep analysis (only `*.md` remain; HTML templates removed) |
| `astro-src/` | Astro project: pages, components, layouts, lib, global CSS. `astro.config.mjs` sets `outDir: '../dist'`, `base: '/news-getter'` |

## Deployment (two workflows)

- **`data-fetch.yml`** (`.github/workflows/data-fetch.yml`): cron UTC 00:00 + 12:00 on the **self-hosted macOS runner** (needs the Gemini binary). Runs `./run_pipeline.sh data-only`, then commits `data/`, `summary.md`, `history/` to `main` and pushes. No-op commit when nothing changed.
- **`build-deploy.yml`** (`.github/workflows/build-deploy.yml`): triggers on `push` to `main` touching `data/**` or `astro-src/**`. Runs on `ubuntu-latest`: `npm ci && npm run build` in `astro-src/`, then `actions/upload-pages-artifact` on `dist/` and `actions/deploy-pages` to publish. `dist/` is never committed.
- **GitHub Pages source must be set to "GitHub Actions"** (Settings → Pages → Source), not a branch.

The hardcoded Gemini binary paths in `src/summarizer.py` are macOS paths (`/Users/tianyao/...`). If running on a different machine, `gemini` must be in PATH or these paths updated.

## Adding New Feed Categories

1. Add entries to `config/feeds.yaml` with the new `category` value.
2. If the category should appear in a specific order, add it to the `cat_order` list in `src/summarizer.py:72`.
