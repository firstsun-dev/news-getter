# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

An automated AI news aggregation pipeline that fetches RSS feeds, runs AI-powered summarization via the local Gemini CLI, and publishes results as a static website (GitHub Pages) and RSS feed. The pipeline runs twice daily via a **self-hosted macOS GitHub Actions runner**.

## Running the Pipeline

```bash
# Full pipeline (fetch → summarize → build site)
./run_pipeline.sh

# Individual steps
source .venv/bin/activate
python3 fetch.py           # outputs raw_data.json
python3 summarizer.py      # outputs summary.md + history/<timestamp>/*.md
python3 build_site.py      # outputs index.html, rss.xml, history/*/*.html
```

The pipeline auto-creates `.venv` on first run. There is no test suite.

## Architecture: Three-Stage Pipeline

**Stage 1 — `fetch.py`**: Reads `feeds.yaml`, fetches each RSS feed (15-hour lookback window), strips HTML, truncates content to 1200 chars, and writes structured output to `raw_data.json` as `{category: [articles]}`.

**Stage 2 — `summarizer.py`**: Reads `raw_data.json`, calls the local `gemini` CLI twice per category:
1. Deep analysis prompt per category → `history/<timestamp>/<Category>.md`
2. Executive summary prompt across all categories → `summary.md`

The Gemini binary is located via PATH, a hardcoded list of known paths, then a filesystem search as a last resort.

**Stage 3 — `build_site.py`**: Converts all `history/*/*.md` to HTML, parses `summary.md` to build a sidebar-nav `index.html`, and generates `rss.xml` pointing to `https://firstsun-dev.github.io/news-getter/`.

## Key Files

| File | Purpose |
|------|---------|
| `feeds.yaml` | RSS source list — edit here to add/remove feeds or change categories |
| `summarizer.py` | Contains the Gemini prompts — edit here to change summarization style |
| `raw_data.json` | Intermediate artifact; deleted if no new articles found |
| `summary.md` | Main output consumed by `build_site.py` for `index.html` |
| `history/<timestamp>/` | Per-run archive of per-category deep analysis |

## Deployment

GitHub Actions workflow (`.github/workflows/daily-news.yml`) runs on a **self-hosted macOS runner** at UTC 00:00 and 12:00. It commits `index.html`, `rss.xml`, `summary.md`, and `history/` back to `main`, which serves as the GitHub Pages source.

The hardcoded Gemini binary paths in `summarizer.py` and `summarize.sh` are macOS paths (`/Users/tianyao/...`). If running on a different machine, `gemini` must be in PATH or these paths updated.

## Adding New Feed Categories

1. Add entries to `feeds.yaml` with the new `category` value.
2. If the category should appear in a specific order, add it to the `cat_order` list in `summarizer.py:72`.
