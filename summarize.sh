#!/bin/bash

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# 嘗試定位 gemini 指令
GEMINI_BIN=$(which gemini)
if [ -z "$GEMINI_BIN" ]; then
    GEMINI_BIN="/opt/homebrew/bin/gemini"
fi

# 定義 Prompt
PROMPT="你是一位專業且嚴謹的新聞編輯。請將以下從 RSS 抓取的文章內容進行分類總結。
每個主題下列出關鍵要點，且每個重點最後必須附上對應的原文連結。
輸出為適合電子紙閱讀的 Markdown 格式。"

# 呼叫 Gemini CLI (使用 -p 進入非互動模式)
echo "正在使用 Gemini CLI 進行新聞總結..."
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" > summary_raw.md

# 清理輸出（移除 MCP 警告、提示訊息或空行等雜訊）
# 這裡使用更精確的過濾，只保留 Markdown 內容
sed -n '/^#/,/^---/p; /^[*-]/p' summary_raw.md | grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" > summary.md

# 如果 summary.md 還是空的（表示 sed 沒抓到），就做基本的過濾
if [ ! -s "summary.md" ]; then
    grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
fi

rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "成功生成總結報告: summary.md"
else
    echo "錯誤: 生成的總結報告內容為空。"
    exit 1
fi
