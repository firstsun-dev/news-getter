#!/bin/bash

# 啟用嚴格模式
set -euo pipefail

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# --- 智慧路徑搜尋 (考慮 root 使用者與 tianyao 的路徑) ---
echo "正在搜尋 gemini 指令..."

# 1. 嘗試直接從目前的 PATH 中尋找
GEMINI_BIN=$(command -v gemini || true)

# 2. 如果是 root，嘗試強制指向 tianyao 使用者的安裝路徑
if [ -z "$GEMINI_BIN" ]; then
    SEARCH_LOCATIONS=(
        "/Users/tianyao/.nvm/versions/node/v22.21.1/bin/gemini"
        "/Users/claudia.fang/.nvm/versions/node/v22.21.1/bin/gemini"
        "/opt/homebrew/bin/gemini"
        "/usr/local/bin/gemini"
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

# 3. 終極手段：使用 find 搜尋
if [ -z "$GEMINI_BIN" ]; then
    echo "警告: 在預設路徑找不到 gemini，嘗試在 /Users 目錄下搜尋..."
    GEMINI_BIN=$(find /Users -name "gemini" -type f -perm +111 2>/dev/null | grep ".nvm" | head -n 1 || true)
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
# 對於 root 使用者執行，可能需要確保能讀取到 tianyao 的設定，或是直接跑
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" --skip-trust > summary_raw.md

# 清理輸出
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "✅ 成功生成總結報告: summary.md"
else
    echo "❌ 錯誤: 生成的總結內容為空。"
    exit 1
fi
