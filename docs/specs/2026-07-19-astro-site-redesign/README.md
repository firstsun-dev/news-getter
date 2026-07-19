# Astro Site Redesign

- Status: Draft
- Date: 2026-07-19
- Target version: Unreleased
- Supersedes: [2026-07-18-static-site-redesign](../2026-07-18-static-site-redesign/README.md)
  (that spec mandated "no frontend framework"; this one adopts Astro and a
  build step, with the user's explicit approval)
- Prerequisite specs: [source-tiering-and-evidence-gate](../2026-07-18-source-tiering-and-evidence-gate/README.md)
  (only shares `build_site.py` as the data-prep layer; data formats are unchanged)

The site is rebuilt on [Astro](https://astro.build): static-first, content
baked into HTML at build time, small vanilla-JS islands for interactivity.
Build output goes to `dist/`. The Python pipeline keeps producing JSON data
into `data/`, which is pushed to `main`; changes under `data/` trigger a
separate build-and-deploy workflow that publishes `dist/` to GitHub Pages.

## Documents

- [PRD](PRD.md): problem, goals, non-goals, user value, acceptance criteria
- [SYSTEM](SYSTEM.md): architecture, design system, interaction catalog,
  page structure, data/deploy flow, cleanup plan
- [TEST](TEST.md): how to verify
- [TASKS](TASKS.md): implementation and acceptance checklist

## Core Principles

1. **Astro is the rendering layer.** `build_site.py` stops generating HTML;
   it only parses `summary.md` / `history/*.md` into JSON under `data/`.
   Astro reads that JSON at build time and bakes content into static HTML.
2. **`data/` is the single source of truth and is version-controlled.**
   `data/*.json` and `data/YYYY/` are pushed to `main`; `data/news.db`
   stays gitignored.
3. **Two workflows, separated by concern.** `data-fetch` (cron, needs the
   Gemini binary on the self-hosted macOS runner) writes `data/` and pushes.
   `build-deploy` (triggered by `data/**` or `src/**` changes) runs
   `npm run build` on a standard ubuntu runner and deploys `dist/` to Pages.
4. **Dynamic but light.** Motion is CSS-driven (scroll-driven animations,
   transitions, IntersectionObserver) plus tiny vanilla-JS islands. No
   React/Motion runtime. Every animation must be motivated and must honor
   `prefers-reduced-motion`.
5. **Old static-site artifacts are deleted.** Root `index.html`,
   `styles.css`, `app.js`, `history.html`, `history.js`, `rss.xml`, and the
   copied `history/<ts>/index.html` templates are removed; the `.md` source
   files under `history/` remain.

## What changed vs. the superseded spec

| Aspect | Old spec (2026-07-18) | This spec (2026-07-19) |
|---|---|---|
| Framework | None, pure static HTML | Astro |
| Build step | None | `npm run build` → `dist/` |
| Rendering | `build_site.py` writes HTML inline | Astro reads JSON, bakes HTML |
| CSS/JS | Separate static files | Astro scoped CSS + vanilla-JS islands |
| RSS | `build_site.py` `build_rss()` | `@astrojs/rss` at build time |
| Deploy | Commit artifacts to `main` | `actions/deploy-pages` artifact from `dist/` |
| Motion | Minimal (`MOTION_INTENSITY` 1-2) | Motivated CSS motion (`MOTION_INTENSITY` 6) |

## User-facing requirement

> 使用者可以容易搜尋不同月份、日期、領域的文章

Three search dimensions, all composable (AND):

- **領域 (category):** sidebar filter box + scrollspy nav on the homepage.
- **月份 (month):** month pills in the archive browser.
- **日期 (date):** date list under the selected month; **dates only, no
  per-run times** are displayed.