# News Getter

**Deterministic news filtering with evidence-gated AI analysis and a static published digest.**

News Getter is a lightweight pipeline for SRE and technical-leadership news monitoring. It collects selected RSS feeds, applies deterministic confidence and heat scoring, sends only stories that pass the evidence threshold to a local Gemini CLI for deeper analysis, validates the structured output, and publishes the result as a static Astro site and RSS feed.

[繁體中文](./README.zh-TW.md)

## Architecture

```text
Python pipeline                           Astro build
─────────────────────────────             ─────────────────────────────
fetch.py       → data/raw_data.json       astro-src/ (Astro 7.1)
summarizer.py  → summary.md                 │ reads data/ at build time
                 history/<ts>/*.md          │ bakes content into HTML
build_site.py  → data/site_data.json        ↓
                 data/history_index.json  dist/  ── deploy-pages ── GitHub Pages
                 data/YYYY/MM/*.json
```

`data/` is the source of truth committed to `main`. `dist/` is a disposable CI artifact deployed through GitHub Pages and is not committed.

## Pipeline

### 1. Collect — `src/fetch.py`

Reads `config/feeds.yaml`, where each source has a `tier` from 1–4 and a `role`. It fetches articles from the previous 15 hours, cleans HTML, truncates content to 1200 characters, and upserts stories through `src/store.py` into the gitignored `data/news.db` SQLite database for deduplication and evidence accumulation such as `seen_count` and independent-source tracking.

Output: `data/raw_data.json`.

### 2. Score and analyze — `src/summarizer.py`

`src/scoring.py` assigns deterministic `confidence` and `heat` scores. Only stories with `confidence ≥ 60` or `heat ≥ 60` are sent to the local `gemini` CLI for deeper analysis; the rest remain in the watch list.

Gemini returns structured JSON using the `StoryDigest` model (`fact_summary`, `judgment`, `used_source_urls`). Pydantic validates the schema, placeholder content, and that every `used_source_urls` entry is a subset of the input evidence links. Invalid output is discarded rather than published.

Outputs: `summary.md` and `history/<timestamp>/*.md`.

### 3. Prepare publication data — `src/build_site.py`

Parses the current and historical summaries into JSON:

- `data/site_data.json` — categories, stories, and watch-list items for the current run
- `data/history_index.json` — date → run → category index
- `data/YYYY/MM/YYYY-MM-DD.json` — complete daily content

This stage produces data only; it does not render HTML or RSS.

### 4. Build the Astro site — `astro-src/`

Astro reads `data/*.json` and `data/YYYY/MM/*.json` at build time and writes static output to `dist/`:

- `index.html` — current digest, sidebar, category cards, and faceted archive browser
- `history/<date>_<time>/index.html` — one page per run
- `rss.xml` — published RSS feed

Primary content does not depend on runtime JSON fetching. The archive index is serialized into the `ArchiveBrowser` island at build time.

The UI includes light/dark themes, category hue hashing, scrollspy navigation, month/category/text faceted search with AND semantics and URL-hash synchronization, and reduced-motion support.

## GitHub Actions

Two workflows separate data collection from static publication:

- **`data-fetch.yml`** — runs at UTC 00:00 and 12:00 on a self-hosted macOS runner because it needs the local Gemini binary. It executes `./run_pipeline.sh data-only` and commits changed `data/`, `summary.md`, and `history/` content to `main`. No changes means no commit.
- **`build-deploy.yml`** — runs on `ubuntu-latest` when `data/**` or `astro-src/**` changes on `main`. It builds the Astro site and deploys the `dist/` artifact through GitHub Pages.

GitHub Pages must use **GitHub Actions** as its source rather than a branch.

## Run locally

```bash
# Full pipeline: fetch → summarize → data JSON → Astro build → dist/
./run_pipeline.sh

# Python/data stages only
./run_pipeline.sh data-only

# Astro build only
cd astro-src && npm ci && npm run build

# Tests
PYTHONPATH=. python3 -m unittest discover -s test -v
cd astro-src && npm test
```

## Customize

- **Feeds and source tiers** — edit `config/feeds.yaml`.
- **Analysis prompt / evidence gate** — edit the prompt and `StoryDigest` schema in `src/summarizer.py`; scoring thresholds live in `src/scoring.py`.
- **Fetch schedule** — edit the cron expression in `.github/workflows/data-fetch.yml`.
- **Site presentation** — edit `astro-src/src/styles/global.css` and the Astro components.

## Requirements

- [Gemini CLI](https://github.com/google/gemini-cli), installed and authenticated for the data-analysis stage
- Python 3.10+
- Node.js 22.12+ for the Astro build

## Design documents

- `docs/specs/2026-07-19-astro-site-redesign/` — Astro site redesign PRD / system / test / task documents
- `docs/specs/2026-07-18-source-tiering-and-evidence-gate/` — source-tiering and evidence-gate design
- `AGENTS.md` — detailed architecture guidance for coding agents

## Firstsun Dev

News Getter is a supporting Firstsun Dev project for solving a real information-filtering problem with explicit scoring, evidence gating, output validation, and a reproducible publication pipeline.

> Build useful things. Operate them well. Share what we learn.
