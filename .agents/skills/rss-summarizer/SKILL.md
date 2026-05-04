# RSS Summarizer Skill

這個技能專為「news-getter」專案設計，負責自動化抓取 RSS 訂閱源，並使用本地 `gemini` CLI 工具進行新聞總結。

## 核心職責 (Core Responsibilities)
1. **抓取 (Fetching)**: 從 `feeds.yaml` 中讀取訂閱清單，並抓取最新的文章內容。
2. **預處理 (Preprocessing)**: 提取文章標題、內容片段與原始連結。
3. **AI 總結 (AI Summarization)**: 呼叫本地 `gemini` 指令，並透過嚴格的 Prompt 確保每個重點都附上來源連結 (Fact-checking)。
4. **輸出 (Outputting)**: 產出適合電子紙閱讀的極簡 HTML 與 RSS feed。

## 使用工具 (Tools used)
* `gemini`: 本地 Gemini CLI 工具。
* `python`: 執行抓取與格式轉換腳本。

## 關鍵 Prompt 規範
在進行總結時，必須遵循以下規則：
* 必須保留並附上每條摘要資訊的原始 URL 連結。
* 總結內容應精簡，適合電子紙顯示。
* 禁止生成任何未包含在原始 RSS 內容中的資訊。
