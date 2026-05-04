# News Getter: 個人化 AI 新聞摘要系統

這是一個為 SRE 與技術領導者設計的輕量級工具，能自動抓取感興趣的 RSS 來源，透過本地 Gemini CLI 進行重點總結，並產出適合電子紙閱讀的 RSS Feed。

## 三大核心工作流程 (The Three Workflows)

### 1. 新聞抓取流程 (Fetching Workflow) - `fetch.py`
*   **功能**: 讀取 `feeds.yaml` 中的訂閱清單。
*   **邏輯**: 抓取過去 24 小時內的文章，並清理 HTML 標籤，僅保留純文字與原文連結。
*   **產出**: `raw_content.txt` (中間暫存檔)。

### 2. AI 摘要流程 (Summarization Workflow) - `summarize.sh`
*   **功能**: 將抓取到的新聞餵給本地 `gemini` CLI。
*   **邏輯**: 使用專屬 Prompt 進行主題分類總結，並**強制要求在每個重點末尾附上原文查證連結**。
*   **產出**: `summary.md` (Markdown 格式的摘要報告)。

### 3. 發布與訂閱流程 (Publishing Workflow) - `build_site.py`
*   **功能**: 將 Markdown 報告轉化為多種輸出格式。
*   **邏輯**: 
    *   生成 `index.html`: 高對比、簡約排版，適合電子紙瀏覽。
    *   生成 `rss.xml`: 標準 RSS Feed，供電子紙裝置直接訂閱。
*   **發布**: 透過 GitHub Actions 自動更新至 GitHub Pages。

---

## 如何客製化
*   **修改訂閱源**: 編輯 `feeds.yaml`。
*   **調整摘要風格**: 編輯 `summarize.sh` 中的 `PROMPT` 變數。
*   **更改抓取頻率**: 修改 `.github/workflows/daily-news.yml` 中的 `cron` 設定。

## 執行需求
*   已安裝並登入的 [Gemini CLI](https://github.com/google/gemini-cli)。
*   Python 3.10+ 環境。
