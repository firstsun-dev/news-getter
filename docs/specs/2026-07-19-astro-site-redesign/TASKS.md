# TASKS: Astro Site Redesign

Only check off once code AND a real verification run's evidence are both in
place. Items are ordered so that each step's prerequisites are already
done.

## 1. Spec

- [x] Audit current site (root `index.html` / `styles.css` / `app.js` /
      `history.html` / `history.js`) and document gaps
- [x] Decide framework (Astro >=7.0), build target (`dist/`), data home
      (`data/`, pushed to `main`)
- [x] Define design system (slate palette, per-category hue hash, dark
      mode tokens, motivated motion catalog, dials 7/6/4)
- [x] Define deploy flow (two workflows: `data-fetch` cron + `build-deploy`
      on `data/**` and `astro-src/**`)
- [x] Write PRD/SYSTEM/TEST docs (this folder)

## 2. Astro project scaffold

- [ ] Create `astro-src/` with `package.json` pinning `astro` `>=7.0`
      (latest stable, currently `7.1.1`), `@astrojs/rss` `>=4.0`,
      `@astrojs/check`, `typescript` `>=5`
- [ ] `astro.config.mjs` with `outDir: '../dist'`, `publicDir: 'public'`,
      `site: 'https://firstsun-dev.github.io/news-getter'`,
      `base: '/news-getter'`
- [ ] `tsconfig.json` extends `astro/tsconfigs/strict`
- [ ] `npm install` runs clean; `npm run build` emits an empty `dist/`
- [ ] `src/lib/categoryHue.ts` with the golden-angle hash, unit-tested by
      hand (same name → same hue across calls)

## 3. Slim `build_site.py` to data-prep only

- [ ] Remove `build_rss()` and the `build_rss()` call in `__main__`
- [ ] Remove `shutil.copy2(template_src, dest)` from `build_day_json()`
- [ ] Remove any HTML-emission logic from `build_site()`; keep only the
      `data/site_data.json` write
- [ ] Confirm `python3 src/build_site.py` still produces
      `data/site_data.json`, `data/history_index.json`, and
      `data/YYYY/MM/*.json` identical to before (byte-equivalent JSON
      shapes; content unchanged)
- [ ] Confirm `build_day_json` no longer creates any `index.html` under
      `history/<ts>/`

## 4. Delete old static-site artifacts

- [ ] `git rm index.html styles.css app.js history.html history.js rss.xml`
- [ ] `git rm history/*/index.html` (every copied template; keep `*.md`)
- [ ] Update `.gitignore`: add `dist/`, `node_modules/`, `.astro/`; confirm
      `data/*.json` and `data/YYYY/` are NOT ignored
- [ ] `git status` shows only intended deletions + `.gitignore` change

## 5. Design system: global CSS + Base layout

- [ ] `src/styles/global.css`: color tokens (light + `[data-theme="dark"]`),
      typography stacks, radius scale, shadow tokens, `--cat-s`/`--cat-l`,
      reset, focus-visible, `prefers-reduced-motion` block
- [ ] `src/layouts/Base.astro`: `<html>` shell, Google Fonts `<link>` with
      `preconnect`, inline theme-init script (sets `data-theme` from
      `localStorage` or `prefers-color-scheme` before paint to avoid FOUC),
      slot for content
- [ ] Theme toggle button with `aria-pressed`, persisted to `localStorage`,
      smooth `background-color`/`color` transition

## 6. Homepage: content components

- [ ] `Topbar.astro`: brand, theme toggle, mobile menu button (hamburger)
- [ ] `Sidebar.astro`: filter input, category nav with colored dots
      (`--h`), sliding active indicator, scrollspy via `IntersectionObserver`
- [ ] `CategoryCard.astro`: `style="--h: <hue>"`, colored left border,
      title + deep count, slot for stories
- [ ] `StoryCard.astro`: title (`h3`), confidence/heat score badges,
      `FactBlock`, `JudgmentBlock`
- [ ] `FactBlock.astro` / `JudgmentBlock.astro`: left-border accent wells,
      monospace "FACT" / "JUDGMENT" label
- [ ] `Watchlist.astro`: collapsible list with `aria-expanded` +
      `aria-controls`, rotating arrow
- [ ] `BackToTop.astro`: visible after `scrollY > 500`, smooth scroll to top
- [ ] Scroll progress bar: `animation-timeline: scroll(root)`, hidden under
      reduced motion
- [ ] `index.astro`: reads `data/site_data.json`, renders Hero + Sidebar +
      CategoryCards + ArchiveBrowser + Footer; two-column layout collapses
      to single column under 900px

## 7. Homepage: ArchiveBrowser island (the core search UX)

- [ ] `ArchiveBrowser.astro`: receives `history_index.json` as baked props
- [ ] Search input with live result count and no-results state (with
      "clear filters" button)
- [ ] Month pills derived from the index (unique `YYYY-MM`, newest first),
      default "全部"
- [ ] Category pills derived from the index (unique category names), with
      per-category `--h` dots, default "全部"
- [ ] Date list: dates only (no times), newest first; each date shows the
      union of its categories as chips; a chip links to that day's latest
      run for that category (`history/<date>_<latest-time>/index.html#<cat>`)
- [ ] Filters compose with AND (month ∩ category ∩ text)
- [ ] URL hash sync: `#month=...&cat=...&q=...` via `history.replaceState`,
      restored on load
- [ ] FLIP animation on result re-flow; filtered-out rows fade out
- [ ] `Cmd/Ctrl+K` focuses the search input
- [ ] Mobile: pills become horizontal-scroll; touch targets >= 44px

## 8. Per-run archive page

- [ ] `src/pages/history/[run]/index.astro` with `getStaticPaths()` globbing
      `../data/*/*/*.json`, `params.run = '<date>_<time>'`
- [ ] Topbar with `← Back to Brief` (`../../index.html`) + theme toggle
- [ ] In-page category nav with scrollspy + `id="<category>"` anchors
      matching existing deep links
- [ ] Same `Base.astro` layout, same design tokens, same per-category hues
- [ ] Verify an existing deep link like
      `history/2026-07-18_10-53/index.html#AI` resolves to the AI section

## 9. RSS

- [ ] `src/pages/rss.xml.ts` using `@astrojs/rss`, pointing at
      `https://firstsun-dev.github.io/news-getter/`, one entry for the
      current run with HTML content from the summary
- [ ] `dist/rss.xml` validates as RSS 2.0
- [ ] Content matches what the old Python `build_rss()` produced (same
      base URL, same language `zh-TW`, same entry structure)

## 10. Workflows

- [ ] `.github/workflows/data-fetch.yml`: schedule UTC 00:00 + 12:00 on
      `self-hosted` macOS, runs Python pipeline (fetch + summarize +
      `build_site.py`), commits `data/` + `summary.md` + `history/*.md` to
      `main`, pushes. No-op commit when nothing changed.
- [ ] `.github/workflows/build-deploy.yml`: triggers on `push` to `main`
      touching `data/**` or `astro-src/**`; `ubuntu-latest`; `npm ci` +
      `npm run build` in `astro-src/`; `actions/upload-pages-artifact` on
      `dist/`; `actions/deploy-pages` to publish.
- [ ] GitHub repo Pages setting: Source = "GitHub Actions"
- [ ] `run_pipeline.sh`: add a `data-only` mode that skips the npm build
      (used by `data-fetch`), and a default mode that also runs
      `cd astro-src && npm ci && npm run build` for local full runs

## 11. Docs & harness

- [ ] Update `AGENTS.md` to describe the new architecture (Astro rendering,
      `data/` as source of truth, two-workflow deploy, `dist/` output)
- [ ] Update `run_pipeline.sh` header comment
- [ ] Mark `docs/specs/2026-07-18-static-site-redesign/README.md` as
      superseded by this spec

## 12. Verification (see TEST.md)

- [ ] `python3 src/build_site.py` runs clean; only JSON under `data/` is
      written; no HTML anywhere outside `dist/`
- [ ] `cd astro-src && npm run build` emits `dist/` with `index.html`,
      `rss.xml`, and `history/<ts>/index.html` per run
- [ ] Manual browser pass of every item in TEST.md section 2
- [ ] `dist/rss.xml` regression check
- [ ] `./run_pipeline.sh` full run with no errors
- [ ] Lighthouse: LCP < 2.5s, CLS < 0.1 on the homepage (no runtime JSON
      fetch for primary content)
- [ ] `prefers-reduced-motion: reduce` collapses all motion
- [ ] `prefers-color-scheme: dark` applies dark theme with no manual choice