#!/bin/bash

# 啟用嚴格模式
set -euo pipefail

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# --- 智慧路徑搜尋 ---
echo "正在搜尋 gemini 指令..."

# 嘗試從 PATH 中直接尋找
GEMINI_BIN=$(command -v gemini || true)

if [ -z "$GEMINI_BIN" ]; then
    # 手動指定多個可能的安裝路徑
    SEARCH_LOCATIONS=(
        "/opt/homebrew/bin/gemini"
        "/usr/local/bin/gemini"
        "/Users/claudia.fang/.nvm/versions/node/v22.21.1/bin/gemini"
        "/Users/tianyao/.nvm/versions/node/v22.21.1/bin/gemini"
        "$HOME/.nvm/versions/node/*/bin/gemini"
        "$HOME/.npm-global/bin/gemini"
        "$HOME/bin/gemini"
    )
    
    for loc in "${SEARCH_LOCATIONS[@]}"; do
        # 處理通配符
        for found in $loc; do
            if [ -x "$found" ]; then
                GEMINI_BIN="$found"
                break 2
            fi
        done
    done
fi

if [ -z "$GEMINI_BIN" ]; then
    echo "❌ 錯誤: 找不到 gemini 指令。"
    echo "目前的 PATH 為: $PATH"
    exit 1
fi

echo "✅ 確認使用 gemini 路徑: $GEMINI_BIN"

# 定義 Prompt
PROMPT="你是一位專業且嚴謹的新聞編輯。請將以下從 RSS 抓取的文章內容進行分類總結。
每個主題下列出關鍵要點，且每個重點最後必須附上對應的原文連結。
輸出為適合電子紙閱讀的 Markdown 格式。"

# 呼叫 Gemini CLI
echo "正在呼叫 AI 進行總結..."
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" > summary_raw.md

# 清理輸出 (移除系統警告雜訊)
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "✅ 成功生成總結報告: summary.md"
else
    echo "❌ 錯誤: 生成的總結內容為空。"
    exit 1
fi
