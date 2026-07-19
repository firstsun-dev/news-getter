# PRD: Astro Site Redesign

## 1. Problem

The current site (root `index.html` + `styles.css` + `app.js` + copied
`history.html` templates) has accumulated usability and maintainability
problems:

- **No real interactivity.** The homepage fetches `data/site_data.json` at
  runtime and renders with vanilla JS, but there is no faceted search across
  the archive. With ~10 categories and a growing daily archive, finding
  articles from a specific month, date, or category requires visual scanning
  of a flat timeline.
- **No dark mode.** The `@media (prefers-color-scheme: dark)` block does not
  exist. Night reading is a blinding white page.
- **No per-category color.** All categories share the same neutral palette;
  there is no quick visual way to tell "Technology" from "Finance" at a
  glance.
- **Cream + terracotta + blue is an AI-default palette.** `#FAF9F7` bg,
  `#C2410C` heat, `#1E40AF` signal. The superseded spec's SYSTEM.md called
  this out as the look to avoid, yet the shipped site is exactly that.
- **Mobile nav is always visible.** The sticky category nav takes vertical
  space on phones and has sub-44px touch targets.
- **Duplicated CSS.** `history.html` inlines a `<style>` block that
  duplicates rules from `styles.css`.
- **Runtime JSON fetch.** `app.js` fetches `data/site_data.json` and
  `data/history_index.json` on every visit, adding a round trip before
  content renders and breaking offline viewing.
- **The user explicitly wants a frontend framework** and a `dist/` build
  output, which the superseded spec forbade.

## 2. Goals

1. **Rebuild on Astro.** Content baked into static HTML at build time; no
   runtime JSON fetch for the primary content. Build output to `dist/`.
2. **Faceted archive search.** Users can filter the archive by month, by
   date, and by category, with the three filters composable (AND). A text
   search box narrows results further. Filter state is reflected in the URL
   hash so views are shareable.
3. **Dates only in the archive.** The archive lists dates without per-run
   times. A day with multiple runs shows the union of its categories; a
   category chip links to that day's latest run for that category.
4. **Dark mode.** Follows `prefers-color-scheme` by default, toggleable via
   a button, choice persisted in `localStorage`.
5. **Per-category color.** Deterministic golden-angle hue hash
   (`category_hue(name)`) applied consistently to sidebar dots, category
   card left borders, and archive chips, in both light and dark themes.
6. **Motivated, light motion.** Scroll-reveal on cards, animated theme
   transition, filter fade-out, sliding sidebar active indicator, hero
   count-up, scroll progress bar. All CSS-driven, all gated by
   `prefers-reduced-motion`.
7. **`data/` is the single source of truth, pushed to `main`.** The Python
   pipeline writes JSON into `data/`; `data/*.json` and `data/YYYY/` are
   committed. `data/news.db` stays gitignored.
8. **Two-workflow deploy.** `data-fetch` (cron, macOS runner with Gemini)
   pushes `data/`; `build-deploy` (triggered by `data/**` or `src/**`)
   builds Astro and deploys `dist/` to GitHub Pages via artifact.
9. **Delete old static-site artifacts.** Root `index.html`, `styles.css`,
   `app.js`, `history.html`, `history.js`, `rss.xml`, and the copied
   `history/<ts>/index.html` templates are removed.

## 3. Non-Goals

- No changes to `fetch.py`, `summarizer.py`, `scoring.py`, `store.py`, or
  `feeds.yaml`. The pipeline's data formats are unchanged.
- No changes to `summary.md` or `history/*.md` content formats.
  `build_site.py` still reads them; it just stops emitting HTML.
- No full-text semantic search. The archive filter does client-side
  substring matching only (date strings + category names).
- No React, Vue, Svelte, or Solid runtime in the shipped bundle.
  Interactivity is vanilla-JS Astro islands. (Astro itself is a build tool,
  not a runtime framework.)
- No Tailwind. Styling is global CSS + Astro scoped CSS, to avoid extra
  build complexity.
- No client-side router. The site is a small set of static pages; full
  page loads are fine.
- No change to the Python pipeline's schedule (twice daily, UTC 00:00 and
  12:00) or to the self-hosted macOS runner requirement for the fetch step.
- No per-run time display in the archive UI. Times remain in the data and
  in URLs (`history/<date>_<time>/index.html`); they are just not shown in
  the archive list.

## 4. User Value

- **Find any article by month, date, or category in a few clicks.** The
  faceted archive browser replaces visual scanning of a flat timeline.
- **Read at night without eye strain.** Dark mode is a real theme, not dead
  CSS.
- **Scan a dense page by color.** Each category has a stable hue across
  sidebar dots, card borders, and archive chips.
- **Fast first paint.** Content is in the HTML; no JSON round trip before
  the page renders.
- **Shareable filtered views.** A URL like
  `/#month=2026-07&cat=AI` opens the archive pre-filtered.
- **Smooth, responsive feel** without a heavy JS bundle or motion that
  ignores accessibility settings.

## 5. Acceptance Criteria

### Rendering & data
- [ ] `python3 src/build_site.py` runs clean against existing `summary.md`
      and `history/` data and produces only `data/site_data.json`,
      `data/history_index.json`, and `data/YYYY/MM/*.json`. It no longer
      writes any HTML or copies any template.
- [ ] `astro-src/package.json` pins `astro` to `>=7.0` (latest stable line,
      currently `7.1.1`) and `@astrojs/rss` to `>=4.0`.
- [ ] `npm run build` (in `astro-src/`) reads `data/` and emits `dist/`
      containing `index.html`, `rss.xml`, and one
      `history/<date>_<time>/index.html` per run, with all story content
      baked into the HTML (no runtime JSON fetch for primary content).
- [ ] Opening `dist/index.html` directly (file://) shows the full briefing
      with all categories and stories, without any network request beyond
      Google Fonts.

### Search (the core user requirement)
- [ ] The homepage archive browser has a text search box, a row of month
      pills, and a row of category pills.
- [ ] Typing a query narrows the visible archive entries (date + category
      name substring match); a live result count is shown; clearing the box
      restores everything; a no-results state shows a "clear filters"
      button.
- [ ] Selecting a month pill shows only entries from that month; selecting a
      category pill shows only entries containing that category; both
      combine with the text search (AND).
- [ ] The current filter state is written to the URL hash
      (`#month=...&cat=...&q=...`) and restored on load, so filtered views
      are shareable and bookmarkable.
- [ ] The archive list shows dates only (no `00:00` / `12:00` labels); each
      date row lists its category chips; clicking a chip navigates to that
      day's latest run for that category.

### Category navigation
- [ ] The homepage sidebar lists categories with colored dots; clicking one
      smooth-scrolls to that category section; scrolling the content
      highlights the active sidebar item (scrollspy) via a sliding
      indicator.
- [ ] A filter box in the sidebar narrows both the nav list and the visible
      category cards (substring match on category name).

### Theme & motion
- [ ] The theme toggle switches light/dark immediately; reload preserves the
      choice (`localStorage`); with no stored choice, it follows
      `prefers-color-scheme`.
- [ ] With `prefers-reduced-motion: reduce` simulated in devtools, all
      motion (scroll reveal, count-up, sliding indicator, filter fade,
      scroll progress bar) collapses to static/instant.
- [ ] A scroll progress bar is visible at the top of the page while
      scrolling; it is absent under reduced motion.

### Per-category archive page
- [ ] Opening any `dist/history/<date>_<time>/index.html` shows the same
      typography, color system, and theme toggle as the homepage, with a
      "back to brief" link to `../../index.html` and in-page category
      anchors (`#<category>`) that match existing deep links.

### RSS
- [ ] `dist/rss.xml` is valid RSS, points at
      `https://firstsun-dev.github.io/news-getter/`, and its entry content
      matches the current run's summary. (Generated by `@astrojs/rss`, not
      by Python.)

### Cleanup
- [ ] Root `index.html`, `styles.css`, `app.js`, `history.html`,
      `history.js`, and `rss.xml` are deleted from the repo.
- [ ] Every `history/<ts>/index.html` copied template is deleted; only
      `history/<ts>/*.md` files remain under `history/`.
- [ ] `dist/`, `node_modules/`, and `.astro/` are listed in `.gitignore`.
      `data/*.json` and `data/YYYY/` are NOT gitignored.

### Deploy
- [ ] `.github/workflows/data-fetch.yml` runs on schedule (UTC 00:00 and
      12:00) on the self-hosted macOS runner, runs the Python pipeline, and
      commits `data/` changes to `main`.
- [ ] `.github/workflows/build-deploy.yml` triggers on pushes to `main`
      touching `data/**` or `astro-src/**`, runs `npm ci && npm run build`
      on `ubuntu-latest`, and deploys `dist/` to GitHub Pages via
      `actions/deploy-pages`.
- [ ] GitHub Pages source is set to "GitHub Actions" (not a branch).