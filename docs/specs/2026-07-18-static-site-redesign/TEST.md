# TEST: Static Site Visual Redesign

## 1. Build Verification

```bash
cd news-getter
source .venv/bin/activate
python3 build_site.py
```

- No Python errors; `index.html` and every `history/*/*.html` are
  regenerated.
- `git diff --stat` shows only `build_site.py` changed in source, plus the
  regenerated `index.html` / `history/**/*.html` as build artifacts (do not
  hand-edit those).

## 2. Manual Browser Verification

Serve the repo root (`python3 -m http.server`) or open `index.html`
directly, and check:

- **Light/dark mode**: toggle switches theme immediately; reload preserves
  the choice (`localStorage`); with no stored choice, matches the OS theme
  (`prefers-color-scheme`).
- **Category color coding**: sidebar dots, category card left borders, and
  history chips for the same category all use the same hue.
- **Sidebar filter**: typing a category keyword narrows both the sidebar
  list and the visible content cards; clearing the input restores
  everything; a query matching nothing shows the "no results" message.
- **Scrollspy**: scrolling the content area highlights the sidebar item for
  the section currently in view, without clicking.
- **Mobile (`<900px` via devtools)**: sidebar is collapsed by default
  behind a menu button; toggling the button shows/hides it; content is
  visible without scrolling past the nav first.
- **Back-to-top**: button appears only after scrolling down, and returns to
  the top on click.
- **Per-category archive page** (e.g. `history/2026-06-18_10-53/AI.html`):
  same typography/colors/theme-toggle as the homepage; "back to digest"
  link returns to `index.html`.
- **Reduced motion**: with `prefers-reduced-motion: reduce` simulated in
  devtools, smooth-scroll and transitions are disabled.

## 3. Regression Checks

- `rss.xml` is still valid RSS/XML and unaffected in content
  (`python3 -c "from build_site import build_rss; build_rss()"` or just
  re-run the full script).
- `./run_pipeline.sh` completes without error end-to-end.
- `.github/workflows/daily-news.yml` needs no changes — no new environment
  variables or dependencies are introduced (Google Fonts is fetched
  client-side by the browser, not at build time).
