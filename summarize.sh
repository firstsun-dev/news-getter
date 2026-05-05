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

# 1. 優先嘗試從目前的 PATH 中尋找
GEMINI_BIN=$(command -v gemini || true)

# 2. 如果找不到，嘗試多個已知可能的安裝路徑
if [ -z "$GEMINI_BIN" ]; then
    SEARCH_LOCATIONS=(
        "/Users/tianyao/.nvm/versions/node/v22.21.1/bin/gemini"
        "/Users/claudia.fang/.nvm/versions/node/v22.21.1/bin/gemini"
        "/opt/homebrew/bin/gemini"
        "/usr/local/bin/gemini"
        "$HOME/.nvm/versions/node/*/bin/gemini"
    )
    
    for loc in "${SEARCH_LOCATIONS[@]}"; do
        # 處理路徑中的通配符
        for found in $loc; do
            if [ -x "$found" ]; then
                GEMINI_BIN="$found"
                break 2
            fi
        done
    done
fi

# 3. 如果還是找不到，進行全域搜尋 (最後手段)
if [ -z "$GEMINI_BIN" ]; then
    echo "警告: 在常見路徑中找不到 gemini，嘗試全域搜尋..."
    # 限制搜尋範圍以加速
    GEMINI_BIN=$(find /Users /opt -name "gemini" -type f -perm +111 2>/dev/null | head -n 1 || true)
fi

if [ -z "$GEMINI_BIN" ]; then
    echo "❌ 錯誤: 找不到 gemini 指令。"
    echo "目前的 User 為: $(whoami)"
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
# 加入 --skip-trust 避免在自動化環境中卡住
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" --skip-trust > summary_raw.md

# 清理輸出 (移除系統警告雜訊)
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "✅ 成功生成總結報告: summary.md"
else
    echo "❌ 錯誤: 生成的總結內容為空。"
    exit 1
fi
