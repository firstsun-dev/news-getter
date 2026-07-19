# TEST: Astro Site Redesign

## 1. Build verification

### 1.1 Python data layer

```bash
cd news-getter
source .venv/bin/activate
python3 src/build_site.py
```

- No Python errors.
- `data/site_data.json`, `data/history_index.json`, and
  `data/YYYY/MM/YYYY-MM-DD.json` are (re)written.
- **No `index.html` is written anywhere by Python.** Specifically:
  - `ls history/*/index.html` returns nothing (no copied templates).
  - `ls index.html` at repo root returns nothing (Astro owns this now).
- `git diff --stat` shows only `data/**` changes (if any) from the Python
  run; no HTML/CSS/JS artifacts.

### 1.2 Astro build

```bash
cd astro-src
npm ci
npm run build
```

- No errors; `npm run build` exits 0.
- `dist/` contains:
  - `index.html` (homepage, content baked in)
  - `rss.xml`
  - `history/<date>_<time>/index.html` for every run found under
    `data/YYYY/MM/*.json`
- `grep -c "fetch(" dist/index.html` returns 0 (no runtime JSON fetch for
  primary content). The archive index is baked as serialized props inside
  the `ArchiveBrowser` island.

### 1.3 Full pipeline (local)

```bash
./run_pipeline.sh
```

- Python stages run, then `cd astro-src && npm ci && npm run build` runs.
- `dist/` is regenerated and reflects the latest `data/`.
- `./run_pipeline.sh data-only` runs only the Python stages and does NOT
  touch `dist/`.

## 2. Manual browser verification

Serve `dist/` (e.g. `npx serve dist` or `python3 -m http.server -d dist`)
and check each item. Test in both light and dark mode unless noted.

### 2.1 Rendering & data
- [ ] Homepage shows the full briefing (all categories, all stories) with
      no spinner or "loading" state; content is in the HTML on first paint.
- [ ] Opening `dist/index.html` via `file://` (offline) shows the full
      briefing; only Google Fonts fails gracefully to system fallbacks.
- [ ] Per-run archive page
      `dist/history/<date>_<time>/index.html` renders all categories for
      that run with story content baked in.

### 2.2 Search (the core user requirement)
- [ ] Archive browser has a search input, a row of month pills, and a row
      of category pills.
- [ ] Typing a query into the search input narrows the visible date rows
      (matches date string or category name); a live result count updates;
      clearing the input restores all rows.
- [ ] A no-results state appears when nothing matches, with a "clear
      filters" button that resets month + category + query.
- [ ] Selecting a month pill shows only rows from that month.
- [ ] Selecting a category pill shows only rows containing that category;
      non-matching chips within a row are hidden, and rows with zero
      matching chips are hidden.
- [ ] Month + category + text compose with AND: selecting `2026-07` +
      `AI` + typing `Tech` shows only July rows that contain AI and where
      some category name matches "Tech".
- [ ] The URL hash updates on every filter change (`#month=...&cat=...&q=...`)
      and reloading the page with that hash restores the exact filtered
      view.
- [ ] Date rows show **dates only** (no `00:00` / `12:00` labels).
- [ ] Clicking a category chip navigates to that day's latest run for that
      category: `history/<date>_<latest-time>/index.html#<cat>`.

### 2.3 Category navigation
- [ ] Sidebar lists categories with colored dots; the dot color matches the
      card's left-border color and the archive chip color for the same
      category.
- [ ] Clicking a sidebar item smooth-scrolls to that category section.
- [ ] Scrolling the content area moves a sliding active indicator along
      the sidebar to the currently-visible category (scrollspy), without
      repainting background colors.
- [ ] The sidebar filter input narrows both the nav list and the visible
      category cards (substring on category name); clearing restores both.
- [ ] `j` / `k` keys cycle the active category and scroll to it.

### 2.4 Theme & motion
- [ ] Theme toggle switches light/dark immediately; reload preserves the
      choice (`localStorage`); with no stored choice, it follows
      `prefers-color-scheme`.
- [ ] With `prefers-reduced-motion: reduce` simulated in devtools:
  - No staggered card reveal (cards are visible immediately).
  - No hero count-up (final values shown instantly).
  - No sliding sidebar indicator (active item uses a static highlight).
  - No filter fade/FLIP (rows appear/disappear instantly).
  - No scroll progress bar.
  - Smooth-scroll on nav clicks is replaced by instant jumps.
- [ ] With `prefers-reduced-motion: no-preference` (default):
  - Cards stagger-reveal as you scroll into them.
  - Hero stats count up from 0 on load.
  - Scroll progress bar is visible at the top while scrolling.
  - Filtering the archive animates row re-flow (FLIP) and fade-out.

### 2.5 Per-category archive page
- [ ] Typography, colors, theme toggle, and per-category hues match the
      homepage exactly.
- [ ] "Back to Brief" link returns to `../../index.html`.
- [ ] In-page category nav jumps to `#<category>` anchors; an existing
      deep link like `history/<ts>/index.html#AI` scrolls to the AI section
      on load.
- [ ] Theme choice persists across navigation between homepage and archive
      pages.

### 2.6 Mobile (devtools < 900px)
- [ ] Sidebar is hidden by default; a hamburger button in the topbar
      toggles it with a spring slide-in and a tappable backdrop overlay.
- [ ] Content is full-width; category cards stack vertically.
- [ ] Archive browser pills become horizontal-scroll; touch targets are
      >= 44px tall.
- [ ] No horizontal page scroll at any width down to 360px.

### 2.7 Accessibility
- [ ] Keyboard-only navigation works: tab through sidebar, filter input,
      theme toggle, archive pills, story links; visible `:focus-visible`
      ring on every interactive element.
- [ ] Heading hierarchy is correct: one `h1` (hero date), `h2` per
      category, `h3` per story (the old site's `h4` skip is fixed).
- [ ] `lang` attribute on root is `zh-TW`; mixed-language story titles are
      acceptable (no per-span lang tagging required).
- [ ] Theme toggle has `aria-pressed` reflecting state.
- [ ] Watchlist toggle has `aria-expanded` and `aria-controls`.
- [ ] Color contrast passes WCAG AA in both themes (body text, button
      labels, score badges, chip text).

## 3. Regression checks

### 3.1 RSS
- [ ] `dist/rss.xml` is valid RSS 2.0 (validate with
      `python3 -c "import xml.dom.minidom; xml.dom.minidom.parse('dist/rss.xml')"`
      or an online validator).
- [ ] Channel `link` is `https://firstsun-dev.github.io/news-getter/`.
- [ ] Channel `language` is `zh-TW`.
- [ ] Entry content is the current run's summary rendered as HTML, with
      `./history/` paths rewritten to the public URL and `.md` links
      rewritten to `.html`.

### 3.2 Data integrity
- [ ] `data/site_data.json` shape is unchanged from the pre-redesign output
      (same keys: `meta.timestamp`, `meta.generated`, `meta.deep_count`,
      `meta.watch_count`, `meta.cat_count`, `categories[]` with
      `name/anchor/archive_url/stories/watchlist/no_signal/deep_count/watch_count`).
- [ ] `data/history_index.json` shape is unchanged.
- [ ] `data/YYYY/MM/*.json` shape is unchanged.

### 3.3 Performance
- [ ] Lighthouse (mobile) on `dist/index.html`: LCP < 2.5s, CLS < 0.1,
      INP < 200ms. The homepage does not make a JSON fetch for primary
      content.
- [ ] No `window.addEventListener('scroll', ...)` in the shipped JS (grep
      `dist/**/*.js`).
- [ ] Total JS shipped is small (target < 20KB gzipped across all islands).

### 3.4 Pipeline end-to-end
- [ ] `./run_pipeline.sh` completes without error from fetch through
      `npm run build`.
- [ ] `.github/workflows/data-fetch.yml` and `build-deploy.yml` are valid
      YAML (`python3 -c "import yaml; yaml.safe_load(open('.github/workflows/data-fetch.yml'))"`
      and same for `build-deploy.yml`).
- [ ] No new Python dependencies; no new system-level dependencies beyond
      Node 20 for the build step.

## 4. Cleanup verification

- [ ] `ls index.html styles.css app.js history.html history.js rss.xml`
      at repo root returns "No such file" for each.
- [ ] `find history -name 'index.html'` returns nothing (only `*.md`
      remain under `history/`).
- [ ] `git check-ignore data/site_data.json` returns non-zero (NOT ignored).
- [ ] `git check-ignore dist/index.html` returns 0 (IS ignored).
- [ ] `git check-ignore data/news.db` returns 0 (IS ignored, unchanged).