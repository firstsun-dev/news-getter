# TASKS: Static Site Visual Redesign

Only check off once code, and a real run's evidence, are both in place.

## 1. Spec

- [x] Review current `build_site.py` output and identify usability problems
- [x] Define the design system (typography, category color hashing, theme
      variables) and shared template structure
- [x] Write PRD/SYSTEM/TEST docs

## 2. Implementation

- [ ] Add `category_hue(name)` to `build_site.py`
- [ ] Add `THEME_CSS` / `THEME_JS` shared constants
- [ ] Add `render_topbar()` helper
- [ ] Rewrite `convert_md_to_html()` to use the shared design system
- [ ] Rewrite the `index_template` in `build_site()`: sidebar filter box +
      `data-cat` attributes, scrollspy anchors (`id` + `scroll-margin-top`),
      colored category cards, recolored history chips
- [ ] Confirm `build_rss()` requires no changes

## 3. Verification

- [ ] `python3 build_site.py` runs clean against existing `summary.md` +
      `history/` data
- [ ] Manual browser check of all items in `TEST.md` section 2 (light/dark,
      filter, scrollspy, mobile collapse, back-to-top, article page parity,
      reduced motion)
- [ ] `rss.xml` regression check
- [ ] `./run_pipeline.sh` full run with no errors
