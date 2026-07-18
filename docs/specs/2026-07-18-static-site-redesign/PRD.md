# PRD: Static Site Visual Redesign

## 1. Problem

`build_site.py`'s output (`index.html` and per-category deep-dive archive
pages) has several usability problems:

- Dark mode is hardcoded off (the `@media (prefers-color-scheme: dark)`
  block is an empty comment) — jarring for night reading.
- Default sans-serif typography with no real hierarchy makes long-form
  zh-TW analytical reports tiring to read.
- The sidebar is a plain text list: no search, no indication of which
  section is currently in view. With ~10 categories this makes navigation
  slow.
- On mobile (`<900px`) the entire sidebar table of contents is pushed above
  the content, so users have to scroll past it to reach anything.
- History archive (`history/`) category chips are all the same color, so
  there's no quick way to tell which category a given entry belongs to.

The user asked about adopting `vercel/ai`. On investigation it's a
React/Next.js SDK built for streaming chat UIs, incompatible with this
project's architecture (Python generates plain static HTML, no build step,
a self-hosted runner commits the artifacts directly). Adopting it would mean
introducing an entire frontend framework and build pipeline just for
styling — disproportionate to the actual need.

## 2. Goals

1. Ship a working dark mode (follows system `prefers-color-scheme` by
   default, toggleable via a button, choice persisted).
2. Introduce deterministic per-category colors (`category_hue()`, hashed
   from the category name) applied consistently to sidebar dots, category
   card left-borders, and history chips — so users can scan a dense page by
   color.
3. Give the sidebar a live text filter that narrows both the nav list and
   matching content sections; highlight the nav item for whichever section
   is currently in view while scrolling (scrollspy).
4. Collapse the sidebar behind a menu button on mobile instead of pushing
   it above the content.
5. Unify the visual language between the homepage and per-category archive
   pages (shared CSS/JS) — serif headings, more generous line-height, a
   capped reading width for long-form content.

## 3. Non-Goals

- No `vercel/ai`, React, Next.js, or any frontend framework/build step; the
  output stays plain static HTML written directly by `build_site.py`.
- No changes to `fetch.py`/`summarizer.py`/`scoring.py`'s data formats or to
  the `summary.md`/`history/<ts>/*.md` source content — this spec only
  changes how that existing Markdown is turned into HTML.
- No full-text semantic search; the filter box does client-side substring
  matching only (category name + section text).
- No changes to `.github/workflows/daily-news.yml` or the deployment model;
  `run_pipeline.sh`'s last step is still `python3 build_site.py`.
- No external JS libraries (no npm, no CDN framework). The only external
  network request is the Google Fonts `Noto Serif TC` import, with a system
  serif fallback.

## 4. User Value

- Reading the digest at night no longer means a blinding white page; dark
  mode is an actual usable theme, not dead CSS.
- With ~10 categories on one long page, color + search + scroll-highlight
  let users find the section they want without scanning the whole page by
  eye.
- Opening the site on mobile shows content first, not a wall of navigation.

## 5. Acceptance Criteria

- Opening `index.html` and clicking the theme toggle changes the theme
  immediately; reloading the page preserves the choice (`localStorage`);
  with no manual choice made, it follows the system theme.
- Typing a category keyword into the sidebar filter box on `index.html`
  leaves only matching sidebar items and content cards visible; clearing
  the box restores everything.
- Scrolling the content area marks the corresponding sidebar item as active
  without any click.
- At `<900px` viewport width, the sidebar is collapsed by default behind a
  menu button that expands/collapses it.
- Opening any `history/<ts>/<Category>.html` shows the same typography,
  color system, and theme toggle as the homepage, and its "back to digest"
  link correctly returns to `index.html`.
- `rss.xml` content is unaffected (`build_rss()` logic is untouched).
