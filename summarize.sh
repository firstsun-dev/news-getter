#!/bin/bash

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# --- 智慧路徑搜尋 ---
# 1. 檢查目前的 PATH
GEMINI_BIN=$(which gemini)

# 2. 如果找不到，嘗試常見的路徑 (Homebrew, NVM, Local bin)
if [ -z "$GEMINI_BIN" ]; then
    POTENTIAL_PATHS=(
        "/opt/homebrew/bin/gemini"
        "/usr/local/bin/gemini"
        "$HOME/.nvm/versions/node/*/bin/gemini"
        "$HOME/.local/bin/gemini"
        "/Users/tianyao/.nvm/versions/node/v22.21.1/bin/gemini" # 使用者提供的路徑
    )
    
    for p in "${POTENTIAL_PATHS[@]}"; do
        # 展開通配符並檢查
        resolved_p=$(ls $p 2>/dev/null | head -n 1)
        if [ -n "$resolved_p" ] && [ -x "$resolved_p" ]; then
            GEMINI_BIN="$resolved_p"
            break
        fi
    done
fi

# 3. 最後檢查
if [ -z "$GEMINI_BIN" ]; then
    echo "錯誤: 找不到 gemini 指令。請確保已安裝並在 PATH 中。"
    exit 1
fi

echo "使用 gemini 路徑: $GEMINI_BIN"

# 定義 Prompt
PROMPT="你是一位專業且嚴謹的新聞編輯。請將以下從 RSS 抓取的文章內容進行分類總結。
每個主題下列出關鍵要點，且每個重點最後必須附上對應的原文連結。
輸出為適合電子紙閱讀的 Markdown 格式。"

# 呼叫 Gemini CLI
echo "正在使用 Gemini CLI 進行新聞總結..."
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" > summary_raw.md

# 清理輸出
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "成功生成總結報告: summary.md"
else
    echo "錯誤: 生成的總結報告內容為空。"
    exit 1
fi
