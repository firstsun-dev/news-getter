# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

An automated AI news aggregation pipeline that fetches RSS feeds, scores stories deterministically by source tier/corroboration, runs AI-powered summarization via the local Gemini CLI only on stories that clear the evidence gate, and publishes results as a static website (GitHub Pages) and RSS feed. The pipeline runs twice daily via a **self-hosted macOS GitHub Actions runner**. See `docs/specs/2026-07-18-source-tiering-and-evidence-gate/` for the design.

## Running the Pipeline

```bash
# Full pipeline (fetch → summarize → build site)
./run_pipeline.sh

# Individual steps
source .venv/bin/activate
PYTHONPATH=. python3 src/fetch.py           # outputs data/raw_data.json, upserts data/news.db
PYTHONPATH=. python3 src/summarizer.py      # outputs summary.md + history/<timestamp>/*.md
PYTHONPATH=. python3 src/build_site.py      # outputs index.html, rss.xml, history/*/*.html

# Unit tests
PYTHONPATH=. python3 -m unittest discover -s test -v
```

The pipeline auto-creates `.venv` on first run.

## Architecture: Three-Stage Pipeline

**Stage 1 — `src/fetch.py`**: Reads `config/feeds.yaml` (each source has `tier` 1-4 and `role`), fetches each RSS feed (15-hour lookback window), resolves relative links against the feed URL, strips HTML, truncates content to 1200 chars. Every article is upserted into `data/news.db` (SQLite, via `src/store.py`) keyed by a title/URL fingerprint, accumulating `seen_count` and distinct `sources`. Writes the enriched articles (with `tier`/`role`/`seen_count`/`sources`) to `data/raw_data.json` as `{category: [articles]}`.

**Stage 2 — `src/summarizer.py`**: Reads `data/raw_data.json`, groups articles per category by fingerprint into stories, and scores each with `scoring.score_story()` (deterministic — tier authority + distinct sources + seen_count; see `src/scoring.py`). Only stories with `confidence >= 60` or `heat >= 60` are sent to Gemini, one call per qualifying story, with a fixed input allowlist (title/URL/category/cleaned content/accumulated tier+source evidence). Gemini must return pure JSON matching `StoryDigest` (`fact_summary`, `judgment`, `used_source_urls`); `src/summarizer.py` validates it with Pydantic — schema bounds, placeholder-word regex, and `used_source_urls` must be a subset of the story's own input URLs. Any failure discards that story (logged, doesn't stop others) and it falls back to the headline-only "觀察中" list. Categories with zero qualifying stories skip Gemini entirely. Output: `history/<timestamp>/<Category>.md` per category, `summary.md` across all categories.

The Gemini binary is located via PATH, a hardcoded list of known paths, then a filesystem search as a last resort.

**Stage 3 — `src/build_site.py`**: Converts all `history/*/*.md` to HTML, parses `summary.md` to build a sidebar-nav `index.html` (rendering the fact/judgment blocks and confidence/heat badges as raw HTML embedded in the Markdown), and generates `rss.xml` pointing to `https://firstsun-dev.github.io/news-getter/`.

## Key Files

| File | Purpose |
|------|---------|
| `config/feeds.yaml` | RSS source list with `tier`/`role` — edit here to add/remove feeds or change categories/tiering |
| `src/store.py` | SQLite persistence (`data/news.db`, gitignored) — `upsert_story`/`stories_since` for dedup and evidence accumulation |
| `src/scoring.py` | Deterministic `score_story()` confidence/heat formula and the deep-analysis threshold |
| `src/summarizer.py` | Gemini prompts, `StoryDigest` Pydantic schema, and the validation gate — edit here to change summarization style or schema |
| `data/raw_data.json` | Intermediate artifact for this run's fetch; not the source of truth for dedup (that's `data/news.db`) |
| `summary.md` | Main output consumed by `build_site.py` for `index.html` |
| `history/<timestamp>/` | Per-run archive of per-category deep analysis |

## Deployment

GitHub Actions workflow (`.github/workflows/daily-news.yml`) runs on a **self-hosted macOS runner** at UTC 00:00 and 12:00. It commits `index.html`, `rss.xml`, `summary.md`, `history/`, `app.js`, `history.js`, `history.html`, `styles.css`, `data/site_data.json`, `data/history_index.json`, and `data/2026/` back to `main`, which serves as the GitHub Pages source.

The hardcoded Gemini binary paths in `src/summarizer.py` are macOS paths (`/Users/tianyao/...`). If running on a different machine, `gemini` must be in PATH or these paths updated.

## Adding New Feed Categories

1. Add entries to `config/feeds.yaml` with the new `category` value.
2. If the category should appear in a specific order, add it to the `cat_order` list in `src/summarizer.py:72`.
