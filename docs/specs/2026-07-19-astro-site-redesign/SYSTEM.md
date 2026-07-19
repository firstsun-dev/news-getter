# SYSTEM: Astro Site Redesign

## 1. Architecture

```text
Python pipeline (unchanged)            Astro build (new)
────────────────────────────────       ──────────────────────────────
fetch.py                               astro-src/src/pages/index.astro
summarizer.py                          astro-src/src/pages/history/[run]/index.astro
build_site.py (slimmed to data-prep)         │
  summary.md / history/*.md  ──┐        │ reads data/ at build time
  data/site_data.json ◄────────┘        │ bakes content into HTML
  data/history_index.json                ↓
  data/YYYY/MM/YYYY-MM-DD.json     dist/  ── actions/deploy-pages ── GitHub Pages
```

`build_site.py` keeps its data-parsing role (`parse_category_content`,
`build_day_json`, `build_history_index`, and a slimmed `build_site` that
only emits `data/site_data.json`). It loses `build_rss()` and all
template-copying (`shutil.copy2`). RSS moves to `@astrojs/rss` inside Astro.

`fetch.py`, `summarizer.py`, `scoring.py`, `store.py`, `feeds.yaml`, and
`.github/workflows`'s fetch stage are unchanged in behavior. Only the
rendering and deploy stages change.

## 2. Project layout

```text
news-getter/
├── .github/workflows/
│   ├── data-fetch.yml              # cron → pipeline → commit data/ → push
│   └── build-deploy.yml            # data/** or astro-src/** → npm build → deploy dist/
├── src/                            # Python pipeline (unchanged)
│   ├── fetch.py
│   ├── summarizer.py
│   ├── scoring.py
│   ├── store.py
│   └── build_site.py               # slimmed: data-prep only
├── config/feeds.yaml
├── docs/                           # specs (this file lives here)
├── data/                           # PUSHED to main; Astro reads at build time
│   ├── site_data.json
│   ├── history_index.json
│   └── 2026/07/*.json
├── history/                        # only *.md source files remain
│   └── <ts>/*.md
├── astro-src/                      # Astro project (new)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.astro
│   │   │   ├── rss.xml.ts          # @astrojs/rss endpoint
│   │   │   └── history/[run]/index.astro
│   │   ├── components/
│   │   │   ├── Topbar.astro
│   │   │   ├── Sidebar.astro
│   │   │   ├── CategoryCard.astro
│   │   │   ├── StoryCard.astro
│   │   │   ├── FactBlock.astro
│   │   │   ├── JudgmentBlock.astro
│   │   │   ├── Watchlist.astro
│   │   │   ├── ArchiveBrowser.astro    # client island
│   │   │   └── BackToTop.astro
│   │   ├── layouts/
│   │   │   └── Base.astro
│   │   ├── lib/
│   │   │   ├── categoryHue.ts
│   │   │   └── data.ts
│   │   └── styles/
│   │       └── global.css
│   ├── public/
│   │   └── favicon.svg
│   ├── astro.config.mjs
│   ├── package.json                # astro >=7.0, @astrojs/rss >=4.0
│   └── tsconfig.json
├── run_pipeline.sh                 # adds: cd astro-src && npm ci && npm run build
├── AGENTS.md                       # updated to describe the new flow
└── .gitignore                      # adds dist/, node_modules/, .astro/
```

`astro.config.mjs` sets `outDir: '../dist'` (relative to `astro-src/`) and
`publicDir: 'public'`. Astro reads JSON from `../data/` (repo root) via
`node:fs` in frontmatter / `getStaticPaths`; the data is NOT copied into
`public/` (it is baked into HTML, not served as files).

## 3. Design system

### 3.1 Aesthetic

An "intelligence dossier" look, executed cool and modern (not the warm
cream + terracotta + blue AI-default of the old site). Slate-based neutral
palette with a single restrained accent, plus per-category hues.

### 3.2 Dials

```text
DESIGN_VARIANCE: 7     # asymmetric sidebar + content, varied card rhythm
MOTION_INTENSITY: 6    # motivated CSS motion, no JS animation runtime
VISUAL_DENSITY: 4      # readable, airy, content-focused
```

### 3.3 Color tokens

CSS custom properties on `:root` (light) and `[data-theme="dark"]` (dark).
No pure `#000` / `#fff`; off-black and off-white throughout.

```css
:root {
  --bg: #f8fafc;            /* slate-50  */
  --bg-elevated: #ffffff;   /* card surface (off-white) */
  --bg-sunken: #f1f5f9;     /* slate-100, fact/judgment wells */
  --text: #0f172a;          /* slate-900 */
  --text-muted: #64748b;    /* slate-500 */
  --border: #e2e8f0;        /* slate-200 */
  --accent: #2563eb;        /* blue-600, single page accent */
  --accent-soft: #dbeafe;   /* blue-100 */
  --shadow: 0 1px 3px rgba(15,23,42,.08);
  /* per-category hue is set inline per element via --h (0-360) */
  --cat-s: 65%;             /* category color saturation, light */
  --cat-l: 45%;             /* category color lightness, light */
}
[data-theme="dark"] {
  --bg: #0b1220;
  --bg-elevated: #111a2e;
  --bg-sunken: #070d1a;
  --text: #e6edf7;
  --text-muted: #94a3b8;
  --border: #1f2a44;
  --accent: #60a5fa;
  --accent-soft: #1e3a5f;
  --shadow: 0 1px 3px rgba(0,0,0,.4);
  --cat-s: 70%;
  --cat-l: 60%;
}
```

The category color is computed from `--h` (set inline per element) plus the
theme-level `--cat-s` / `--cat-l`, so a single hue renders correctly in both
themes without per-category dark variants:

```css
.cat-dot { background: hsl(var(--h) var(--cat-s) var(--cat-l)); }
.cat-card { border-left: 3px solid hsl(var(--h) var(--cat-s) var(--cat-l)); }
```

### 3.4 Per-category hue

Golden-angle hash (deterministic, no fixed color table):

```ts
// astro-src/src/lib/categoryHue.ts
export function categoryHue(name: string): number {
  let h = 0;
  for (const ch of name) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return Math.round(((h * 0.6180339887) % 1) * 360);
}
```

Emitted as `style="--h: <n>"` on the category card, sidebar dot, and
archive chip. The same category always gets the same hue across pages and
runs.

### 3.5 Typography

| Role | Stack | Source |
|---|---|---|
| Headings | `'Noto Serif TC', 'Newsreader', Georgia, serif` | Google Fonts (Noto Serif TC 500/700) |
| Body | `-apple-system, 'Noto Sans TC', 'PingFang TC', 'Microsoft JhengHei', sans-serif` | system |
| Metadata, scores, nav | `'JetBrains Mono', ui-monospace, 'SF Mono', Menlo, monospace` | Google Fonts (JetBrains Mono 400/500) |

Google Fonts loaded via `<link rel="preconnect">` + a single
`css2` request with `display=swap`. System serif/sans/mono fallbacks
prevent layout breakage offline. No `Inter` (AI-default tell). Body text
uses the system sans stack only, zero external font weight for body.

Reading measure capped at `max-width: 68ch` for long-form story content.

### 3.6 Radii, shadows, borders

- One radius scale: cards `12px`, inputs/buttons `8px`, pills `999px`
  (full). Applied consistently (Shape Consistency Lock).
- Shadows tinted to the slate hue (`rgba(15,23,42,*)` light,
  `rgba(0,0,0,*)` dark). No pure-black drop shadows.
- Dividers: `1px solid var(--border)`. The fact/judgment blocks keep the
  `3px` left-border accent (now using `--accent` for FACT and `--heat` for
  JUDGMENT, both tokenized).

## 4. Interaction catalog

Every entry below is motivated (one sentence each) and gated by
`prefers-reduced-motion: reduce` (collapses to static/instant).

| Interaction | Motivation | Mechanism |
|---|---|---|
| Category cards stagger-reveal on scroll | hierarchy: guide the eye down the page | `animation-timeline: view()` with `animation-delay` cascade; IntersectionObserver fallback for browsers without scroll-driven animations |
| Theme toggle smooth color transition | state-transition feedback, no flash | `transition: background-color .2s, color .2s` on tokens |
| Filtered cards fade-and-slide out | feedback: show what got filtered | `transition: opacity .2s, transform .2s; .filtered-out { opacity:0; transform: translateY(-8px); }` |
| Sidebar active indicator slides | continuity: "you are here" without repaint | absolutely-positioned highlight, `transform: translateY()` tracks active item |
| Archive results re-flow on filter change | feedback: results move, not jump | FLIP (record old rect → reflow → transform back → clear) |
| Hero stat count-up on load | storytelling: emphasize today's output | animate from 0 to value via rAF; reduced-motion shows final value instantly |
| Card hover lift | tactile feedback | `transform: translateY(-2px)` + tinted shadow on `:hover` |
| Top scroll-progress bar | long-page position | `animation-timeline: scroll(root)` width 0→100% |
| `Cmd/Ctrl+K` focuses archive search | power-user shortcut | `keydown` listener, focuses the search input |
| Filter state in URL hash | shareable/bookmarkable filtered views | `history.replaceState`, `#month=...&cat=...&q=...`; restored on load |
| `j` / `k` jumps between categories | keyboard navigation | `keydown` cycles active category, smooth-scrolls |
| Mobile sidebar spring-in | responsive feel | `transition: transform .25s cubic-bezier(.16,1,.3,1)` + backdrop overlay tap-to-close |

Forbidden animation patterns (per the taste skill): `window.addEventListener('scroll')`, React-style state for continuous scroll values, rAF loops that touch component state. Use CSS scroll-driven animations, `IntersectionObserver`, and `useScroll`-equivalent vanilla helpers only.

## 5. Page structure

### 5.1 Homepage (`src/pages/index.astro`)

```text
Topbar: brand "The Brief" | theme toggle | mobile menu button
┌────────────┬─────────────────────────────────────────────┐
│ Sidebar    │ Main                                        │
│ 240px      │                                             │
│            │ Hero: date + stats (deep/watch/cat counts)  │
│ [filter]   │                                             │
│            │ CategoryCard × N (per-category --h)         │
│ ● AI       │   title + deep count                        │
│ ● Tech     │   StoryCard × M                             │
│ ● Finance  │     title, confidence/heat scores           │
│ ● ...      │     FactBlock (blue left border)            │
│            │     JudgmentBlock (heat left border)        │
│            │   Watchlist (collapsible)                   │
│            │                                             │
│            │ ArchiveBrowser (client island)              │
│            │   [search input]  result count              │
│            │   month pills: [全部] [2026-07] [2026-06]…  │
│            │   cat pills:   [全部] [AI] [Tech] …         │
│            │   date list (dates only, no times):         │
│            │     2026-07-18  [AI][Tech][Finance]         │
│            │     2026-07-17  [AI][World]                 │
│            │                                             │
│            │ Footer: pipeline attribution + generated at │
└────────────┴─────────────────────────────────────────────┘
BackToTop button (visible after scrollY > 500)
Scroll progress bar (top, full width)
```

### 5.2 Per-run archive page (`src/pages/history/[run]/index.astro`)

- `getStaticPaths()` globs `../data/*/*/*.json`, emits one path per run
  with `params.run = '<date>_<time>'` (e.g. `2026-07-18_10-53`).
- URL: `history/<date>_<time>/index.html` (matches existing deep links and
  RSS entries).
- Topbar: `← Back to Brief` (to `../../index.html`) + theme toggle.
- In-page category nav with scrollspy; category sections carry
  `id="<category>"` anchors matching existing `#<category>` deep links.
- Same design system, same per-category hues, same theme tokens.

## 6. Three search dimensions

All composable (AND). State lives in the URL hash.

| Dimension | UI | Scope | Match |
|---|---|---|---|
| 領域 (category) | homepage sidebar filter box + nav | current run | substring on category name |
| 月份 (month) | archive browser month pills | all history | exact month (`YYYY-MM`) |
| 日期 (date) | archive browser date list | within selected month | chronological, newest first, **no times shown** |
| text | archive browser search input | all history | substring on date + category name |

Date list semantics: a day with multiple runs shows the **union** of its
categories as chips. A chip links to that day's **latest** run containing
that category (`history/<date>_<latest-time>/index.html#<category>`).

URL hash format: `#month=YYYY-MM&cat=<cat>&q=<query>`. Omitted keys mean
"all". Restored on page load; updated on every filter change via
`history.replaceState`.

## 7. Data flow

| File | Writer | Reader | Pushed? |
|---|---|---|---|
| `data/site_data.json` | `build_site.py` | Astro `index.astro` at build time | yes |
| `data/history_index.json` | `build_site.py` | Astro `ArchiveBrowser.astro` (baked as island props) | yes |
| `data/YYYY/MM/YYYY-MM-DD.json` | `build_site.py` (`build_day_json`) | Astro `[run]/index.astro` via `getStaticPaths` | yes |
| `data/news.db` | `store.py` | pipeline only | **no** (gitignored) |
| `history/<ts>/*.md` | `summarizer.py` | `build_site.py` only | yes (existing) |
| `summary.md` | `summarizer.py` | `build_site.py` only | yes (existing) |
| `dist/**` | `npm run build` | GitHub Pages deploy action | **no** (gitignored, deployed as artifact) |

Astro never fetches JSON at runtime for primary content. The
`ArchiveBrowser` island receives `history_index.json` as serialized props
baked into the HTML at build time, so even the interactive archive works
offline.

## 8. Deploy flow (two workflows)

### 8.1 `data-fetch.yml` (cron)

```yaml
on:
  schedule: [{ cron: "0 0 * * *" }, { cron: "0 12 * * *" }]
  workflow_dispatch: {}
jobs:
  fetch:
    runs-on: [self-hosted, macOS]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: ./run_pipeline.sh data-only   # fetch + summarize + build_site.py
      - run: |
          git add data/ summary.md history/
          git diff --staged --quiet || git commit -m "data: $(date -u +%Y-%m-%dT%H:%M)"
          git push
```

`run_pipeline.sh data-only` runs only the Python stages (no npm build); the
build happens in the second workflow. This keeps the Gemini-dependent step
on the macOS runner and the Node build off it.

### 8.2 `build-deploy.yml` (triggered)

```yaml
on:
  push:
    branches: [main]
    paths:
      - "data/**"
      - "astro-src/**"
      - "package.json"
      - ".github/workflows/build-deploy.yml"
  workflow_dispatch: {}
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20", cache: "npm", cache-dependency-path: "astro-src/package-lock.json" }
      - working-directory: astro-src
        run: npm ci
      - working-directory: astro-src
        run: npm run build    # → ../dist
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - uses: actions/deploy-pages@v4
```

GitHub Pages source: **"GitHub Actions"** (Settings → Pages → Source).
`dist/` is never committed.

## 9. Cleanup plan (delete these)

| Path | Why |
|---|---|
| `index.html` | Astro emits `dist/index.html` |
| `styles.css` | replaced by `astro-src/src/styles/global.css` + scoped CSS |
| `app.js` | replaced by Astro islands |
| `history.html` | replaced by `astro-src/src/pages/history/[run]/index.astro` |
| `history.js` | replaced by Astro islands |
| `rss.xml` | replaced by `astro-src/src/pages/rss.xml.ts` |
| `history/<ts>/index.html` (every run dir) | Astro emits `dist/history/<ts>/index.html` |
| `build_site.py:build_rss()` | RSS moves to `@astrojs/rss` |
| `build_site.py:shutil.copy2(template_src, dest)` | no template copying |
| `build_site.py` HTML-emission logic in `build_site()` | only emit `data/site_data.json` |

Keep: `history/<ts>/*.md` (pipeline source), `data/*.json` + `data/YYYY/`
(pushed data), `src/*.py` (pipeline), `config/`, `docs/`, `.github/`.

## 10. `.gitignore` additions

```gitignore
# existing
data/news.db
.venv/
__pycache__/

# new
dist/
node_modules/
.astro/
astro-src/package-lock.json   # optional: keep if you prefer committed lockfile
```

`data/*.json` and `data/YYYY/` are explicitly NOT ignored (they are the
pushed data source).

## 11. Failure modes / rollback

- **Google Fonts blocked (offline viewing):** system serif/sans/mono
  fallbacks render; layout intact, typeface less distinctive.
- **Astro build fails in CI:** `build-deploy` job fails, Pages keeps the
  last successful deploy. The `data-fetch` push to `main` still landed, so
  data is not lost; a re-run of `build-deploy` fixes it once the build is
  green.
- **`data/` push has no changes (quiet day):** `git diff --staged --quiet`
  short-circuits the commit; `build-deploy` is not triggered. Acceptable.
- **Rollback:** `git revert` the offending commit on `main`. If it was a
  data change, the next `build-deploy` reverts the site. If it was a source
  change, same. No data-format migration to unwind because `build_site.py`'s
  JSON shapes are unchanged from today.