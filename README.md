# News Getter: 個人化 AI 新聞摘要系統

為 SRE 與技術領導者設計的輕量級工具：自動抓取感興趣的 RSS 來源、用確定性評分篩出達標故事、只對通過證據門檻者呼叫本地 Gemini CLI 做深度分析，最終由 [Astro](https://astro.build) 烘焙成靜態網站與 RSS Feed，部署到 GitHub Pages。

## 架構總覽

```text
Python pipeline                           Astro build
─────────────────────────────             ─────────────────────────────
fetch.py       → data/raw_data.json       astro-src/ (Astro 7.1)
summarizer.py  → summary.md                 │ reads data/ at build time
                 history/<ts>/*.md          │ bakes content into HTML
build_site.py  → data/site_data.json        ↓
                 data/history_index.json  dist/  ── deploy-pages ── GitHub Pages
                 data/YYYY/MM/*.json
```

`data/` 是單一資料來源，push 到 `main`；`dist/` 是 CI 一次性產物，用 artifact 部署，不進 git。

## 四個階段

### 1. 抓取 — `src/fetch.py`
讀取 `config/feeds.yaml`（每個來源標有 `tier` 1-4 與 `role`），抓過去 15 小時的文章，清理 HTML、截斷至 1200 字，用 `src/store.py` 把每篇 upsert 進 `data/news.db`（SQLite，gitignored）做去重與證據累積（`seen_count`、獨立來源清單）。產出 `data/raw_data.json`。

### 2. AI 摘要 — `src/summarizer.py`
用 `src/scoring.py` 對每則新聞算出確定性的 `confidence`/`heat` 分數，只有 `confidence ≥ 60` 或 `heat ≥ 60` 才送本地 `gemini` CLI 做深度分析，其餘只進「觀察中」速報清單。Gemini 每則回傳純 JSON（`StoryDigest`：`fact_summary`/`judgment`/`used_source_urls`），用 Pydantic 校驗 schema、佔位詞、與 `used_source_urls` 是否為輸入連結子集，沒過就整條丟棄。產出 `summary.md` 與 `history/<timestamp>/*.md`。

### 3. 資料準備 — `src/build_site.py`
解析 `summary.md` 與 `history/*/*.md` 成 JSON：`data/site_data.json`（本次 run 的類別/故事/觀察清單）、`data/history_index.json`（日期→runs→類別索引）、`data/YYYY/MM/YYYY-MM-DD.json`（每日完整內容）。**只產 JSON，不寫 HTML/RSS**。

### 4. Astro 烘焙 — `astro-src/`
讀 `data/*.json` 與 `data/YYYY/MM/*.json`，在 build time 把所有內容烘進靜態 HTML 到 `dist/`：`index.html`（首頁：側邊欄、類別卡、 faceted archive 瀏覽器）、`history/<date>_<time>/index.html`（每 run 一頁）、`rss.xml`。主要內容不做 runtime JSON fetch；archive 索引以序列化 props 烘進 `ArchiveBrowser` island。

特色：深淺色主題（`prefers-color-scheme` + `localStorage`）、每類別金色角度 hue hash、scrollspy 側邊欄、month/cat/text 三維 faceted 搜尋（AND，URL hash 同步）、CSS 動畫全數尊重 `prefers-reduced-motion`。

## 兩個 GitHub Actions workflow

- **`data-fetch.yml`** — cron UTC 00:00 + 12:00，跑在 **self-hosted macOS runner**（需要 Gemini binary）。執行 `./run_pipeline.sh data-only`，commit `data/`+`summary.md`+`history/` 到 `main`。無變更時 no-op。
- **`build-deploy.yml`** — push 到 `main` 觸碰 `data/**` 或 `astro-src/**` 時觸發，跑在 `ubuntu-latest`：`npm ci && npm run build`，再以 `actions/upload-pages-artifact` + `actions/deploy-pages` 部署 `dist/`。`dist/` 永不進 git。
- **GitHub Pages Source 須設為「GitHub Actions」**（Settings → Pages → Source），不是分支。

## 本地執行

```bash
# 完整流程：fetch → summarize → data JSON → Astro build → dist/
./run_pipeline.sh

# 只跑 Python（CI 的 data-fetch 用）
./run_pipeline.sh data-only

# 單獨跑 Astro build
cd astro-src && npm ci && npm run build

# 測試
PYTHONPATH=. python3 -m unittest discover -s test -v   # Python
cd astro-src && npm test                                # categoryHue (Node --test)
```

## 如何客製化

- **訂閱源與分級** — 編輯 `config/feeds.yaml`（標註 `tier`/`role`）。
- **摘要風格或收斂門禁** — 編輯 `src/summarizer.py` 的 prompt 與 `StoryDigest` schema；分數門檻改 `src/scoring.py`。
- **抓取頻率** — 改 `.github/workflows/data-fetch.yml` 的 `cron`。
- **網站外觀/動畫** — 改 `astro-src/src/styles/global.css` 與各 `.astro` 元件。

## 執行需求

- [Gemini CLI](https://github.com/google/gemini-cli) 已安裝並登入（資料抓取階段）。
- Python 3.10+。
- Node ≥ 22.12（Astro build 階段）。

## 設計文件

- `docs/specs/2026-07-19-astro-site-redesign/` — Astro 站點重設計（PRD/SYSTEM/TEST/TASKS）。
- `docs/specs/2026-07-18-source-tiering-and-evidence-gate/` — 來源分級與證據門檻設計。
- `AGENTS.md` — 給 AI coding agent 的完整架構說明。