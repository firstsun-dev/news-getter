#!/bin/bash

# 啟用嚴格模式
set -euo pipefail

# 檢查檔案是否存在
if [ ! -f "raw_content.txt" ]; then
    echo "錯誤: 找不到 raw_content.txt，請先執行 fetch.py"
    exit 1
fi

# --- 智慧路徑搜尋 ---
# 優先順序：目前的 PATH > 使用者家目錄下的常見位置 > Homebrew 位置
echo "正在搜尋 gemini 指令..."
GEMINI_BIN=$(which gemini 2>/dev/null || true)

if [ -z "$GEMINI_BIN" ]; then
    # 搜尋可能包含 gemini 的路徑，排除虛擬環境
    # 增加更多常見的 nvm/npm 路徑
    SEARCH_LOCATIONS=(
        "$HOME/.nvm/versions/node/*/bin/gemini"
        "$HOME/.npm-global/bin/gemini"
        "$HOME/bin/gemini"
        "/opt/homebrew/bin/gemini"
        "/usr/local/bin/gemini"
        "/Users/tianyao/.nvm/versions/node/*/bin/gemini"
    )
    
    for loc in "${SEARCH_LOCATIONS[@]}"; do
        # 使用 ls 展開通配符並過濾掉錯誤訊息
        found=$(ls $loc 2>/dev/null | head -n 1)
        if [ -n "$found" ] && [ -x "$found" ]; then
            GEMINI_BIN="$found"
            break
        fi
    done
fi

if [ -z "$GEMINI_BIN" ]; then
    echo "錯誤: 在常見路徑中找不到 gemini 指令。"
    echo "請確認 gemini 是否已正確安裝，或手動在腳本中指定正確的路徑。"
    exit 1
fi

echo "確認使用 gemini 路徑: $GEMINI_BIN"

# 定義 Prompt
PROMPT="你是一位專業且嚴謹的新聞編輯。請將以下從 RSS 抓取的文章內容進行分類總結。
每個主題下列出關鍵要點，且每個重點最後必須附上對應的原文連結。
輸出為適合電子紙閱讀的 Markdown 格式。"

# 呼叫 Gemini CLI
echo "正在呼叫 AI 進行總結..."
# 使用 -p "" 確保以非互動模式執行
(echo "$PROMPT"; echo "內容如下："; cat raw_content.txt) | "$GEMINI_BIN" -p "" > summary_raw.md

# 清理輸出 (移除可能的系統警告雜訊)
grep -v "MCP issues detected\|Ripgrep is not available\|Tool with name\|Skill .* is overriding" summary_raw.md > summary.md
rm summary_raw.md

if [ -s "summary.md" ]; then
    echo "✅ 成功生成總結報告: summary.md"
else
    echo "❌ 錯誤: 生成的總結內容為空。"
    exit 1
fi
