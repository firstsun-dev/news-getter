# News Getter: 個人化 AI 新聞摘要系統

這是一個為 SRE 與技術領導者設計的輕量級工具，能自動抓取感興趣的 RSS 來源，透過本地 Gemini CLI 進行重點總結，並產出適合電子紙閱讀的 RSS Feed。

## 三大核心工作流程 (The Three Workflows)

### 1. 新聞抓取流程 (Fetching Workflow) - `fetch.py`
*   **功能**: 讀取 `feeds.yaml` 中的訂閱清單（每個來源標有 `tier` 1-4 與 `role`）。
*   **邏輯**: 抓取過去 15 小時內的文章，清理 HTML 標籤，並用 `store.py` 把每篇文章 upsert 進本機 `news.db`（SQLite）做去重與證據累積（`seen_count`、獨立來源清單）。
*   **產出**: `raw_data.json`（含 tier/role/seen_count/sources 的結構化文章清單）。

### 2. AI 摘要流程 (Summarization Workflow) - `summarizer.py`
*   **功能**: 用 `scoring.py` 對每則新聞算出確定性的 `confidence`/`heat` 分數，只有達門檻（≥60）的新聞才送進本地 `gemini` CLI 做深度分析，其餘只出現在「觀察中」速報清單。
*   **邏輯**: Gemini 每則新聞回傳一則純 JSON（`StoryDigest`：`fact_summary`/`judgment`/`used_source_urls`），本機用 Pydantic 校驗 schema、佔位詞、以及 `used_source_urls` 是否為輸入連結的子集，沒通過就整條丟棄不寫入。
*   **產出**: `summary.md`（事實/判斷雙區塊 + confidence/heat 標籤）與 `history/<timestamp>/*.md`。

### 3. 發布與訂閱流程 (Publishing Workflow) - `build_site.py`
*   **功能**: 將 Markdown 報告轉化為多種輸出格式。
*   **邏輯**: 
    *   生成 `index.html`: 高對比、簡約排版，適合電子紙瀏覽。
    *   生成 `rss.xml`: 標準 RSS Feed，供電子紙裝置直接訂閱。
*   **發布**: 透過 GitHub Actions 自動更新至 GitHub Pages。

---

## 如何客製化
*   **修改訂閱源與分級**: 編輯 `feeds.yaml`（新增/移除來源時記得標註 `tier`/`role`）。
*   **調整摘要風格或收斂門禁**: 編輯 `summarizer.py` 中的 prompt 與 `StoryDigest` schema；調整分數門檻請改 `scoring.py`。
*   **更改抓取頻率**: 修改 `.github/workflows/daily-news.yml` 中的 `cron` 設定。

## 執行需求
*   已安裝並登入的 [Gemini CLI](https://github.com/google/gemini-cli)。
*   Python 3.10+ 環境。
