#!/bin/bash

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# 定義 Prompt 並讀取內容
PROMPT="你是一位專業且嚴謹的新聞編輯。請將以下從 RSS 抓取的文章內容進行分類總結。
每個主題下列出關鍵要點，且每個重點最後必須附上對應的原文連結。
輸出為適合電子紙閱讀的 Markdown 格式。"

# 呼叫 Gemini CLI
echo "正在使用 Gemini CLI 進行新聞總結..."
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | gemini > summary_raw.md

# 清理輸出（移除 MCP 警告或 Ripgrep 提示等雜訊）
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ $? -eq 0 ]; then
    echo "成功生成總結報告: summary.md"
else
    echo "Gemini CLI 總結失敗。"
    exit 1
fi
