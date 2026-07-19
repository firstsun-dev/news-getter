# SYSTEM: Static Site Visual Redesign

## 1. Current vs. Target

```text
Current: build_site.py -> per-page inline f-string HTML + <style> block
         (duplicated between index template and convert_md_to_html)
         -> dark mode disabled, plain sidebar list, no scroll/filter behavior

Target:  build_site.py -> shared THEME_CSS / THEME_JS constants
         -> render_topbar() helper reused by both templates
         -> category_hue(name) drives per-category color everywhere
         -> index template: sidebar nav + filter + scrollspy + card sections
         -> convert_md_to_html(): same design system, capped reading width
```

Only `build_site.py` changes. `fetch.py`, `summarizer.py`, `scoring.py`,
`feeds.yaml`, and `.github/workflows/daily-news.yml` are untouched — this is
purely a rendering-layer change consumed by the existing pipeline
(`run_pipeline.sh`'s last stage is still `python3 build_site.py`).

## 2. Design System

**Aesthetic**: an "intelligence dossier" look — deliberately not the
generic AI-default look (no cream+terracotta, no near-black+neon accent, no
newspaper-hairline grid).

- **Type**: `Noto Serif TC` (weight 700/900, via a Google Fonts `<link>`
  with `font-display: swap`, falling back to a system serif) for all
  headings — editorial/report feel. Body text stays system sans
  (`-apple-system, "PingFang TC", "Noto Sans TC", ...`) for long-form
  readability. Metadata, timestamps, and category tags use
  `ui-monospace/"SF Mono"/Menlo` — a "log entry" feel for the archive
  sections.
- **Signature element — deterministic per-category color**:

  ```python
  def category_hue(name):
      h = 0
      for ch in name:
          h = (h * 31 + ord(ch)) & 0xFFFFFFFF
      return round((h * 0.6180339887) % 1 * 360)
  ```

  Golden-angle hashing gives a well-spread hue per category name without
  maintaining a fixed color table as `feeds.yaml` categories change. The hue
  is emitted as an inline `style="--h: <n>"` and consumed by CSS wherever
  that category appears: sidebar nav dot + active state, category section's
  left border + tag chip, and history archive chips.
- **Color system**: CSS custom properties cover both themes (`--bg`,
  `--bg-elevated`, `--bg-sunken`, `--text`, `--text-muted`, `--border`,
  `--ink`, `--shadow`). `--cat-s`/`--cat-l` are theme-level (not
  per-category) and get overridden by the dark theme, so the same `--h`
  value renders correctly in both themes without per-category dark
  variants.
- **Dark mode**: `[data-theme="dark"]` attribute on `<html>`. A
  `theme-toggle` button flips it and persists the choice to
  `localStorage`; with no stored choice, `@media (prefers-color-scheme:
  dark)` decides.

## 3. Shared Template Structure

`THEME_CSS` and `THEME_JS` are module-level string constants in
`build_site.py`, injected into both `convert_md_to_html()`'s per-category
page template and `build_site()`'s index template, so the two page types
cannot visually drift apart.

`render_topbar(brand_html, back_html="")` builds the shared sticky top bar
(brand/title, mobile nav-toggle button, theme-toggle button, optional back
link) used by both templates.

`THEME_JS` (vanilla JS, no dependencies) covers:

- theme toggle (`localStorage` + `prefers-color-scheme` fallback)
- back-to-top button (visible after `scrollY > 500`)
- mobile sidebar collapse (`.sidebar.collapsed` toggled by the menu button)
- filter box: substring match against `data-cat` on sidebar links and
  `.cat-section` content, hides non-matching nav items/sections
- scrollspy: `IntersectionObserver` over `.cat-section[id]` elements,
  toggles `.active` on the matching sidebar link

## 4. Index Page (`build_site()`)

- Existing parsing logic for `summary.md` (title/intro extraction, category
  block extraction, fallback-fill from the matching `history/<ts>/` dir) is
  unchanged — only the HTML each category renders into changes.
- Each category becomes `<section class="cat-section" id="{anchor}"
  data-cat="{cat}" style="--h: {hue}">` — a card with rounded corners,
  subtle shadow, colored left border, and a small monospace tag chip next
  to the heading.
- Sidebar nav items carry `data-cat="{cat}"` and the same `--h` value for
  the filter box and colored dot.
- History archive keeps its existing day-grouped structure
  (`daily_groups`, `history_links` construction is unchanged) — only the
  chip styling is recolored per category via `category_hue()`.

## 5. Per-Category Article Pages (`convert_md_to_html()`)

- Same shared top bar, theme toggle, back-to-top button, plus a "back to
  digest" link to `../../index.html`.
- Reading column capped at `740px` for long-form readability.
- `md_to_html_util()` (existing markdown-to-HTML conversion, with `tables`,
  `fenced_code`, `toc`, `sane_lists` extensions) is unchanged.

## 6. Failure Modes / Rollback

- If the Google Fonts request fails or is blocked (e.g. offline viewing),
  headings fall back to the system serif stack — no layout breakage, just a
  less distinctive typeface.
- All JS is progressive enhancement: if JS fails to run, the page is still
  fully readable static HTML (sidebar list, category sections, history
  archive) — only filter/scrollspy/theme-toggle/mobile-collapse behavior is
  lost.
- Rollback is a plain `git revert` of the `build_site.py` commit; there is
  no data-format change to unwind since `summary.md`/`history/*.md` inputs
  are untouched.
