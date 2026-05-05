#!/bin/bash

# 啟用嚴格模式
set -euo pipefail

# 切換到腳本所在的絕對路徑
cd "$(dirname "$0")"

echo "=== [$(date)] 啟動新聞總結 Pipeline ==="
echo "Debug: Current User = $(whoami)"
echo "Debug: Current PATH = $PATH"

# 1. 檢查並建立隔離的虛擬環境 (.venv)
if [ ! -d ".venv" ]; then
    echo "正在建立隔離的 Python 虛擬環境 (.venv)..."
    python3 -m venv .venv
fi

echo "Step 1: 啟動環境並抓取 RSS..."
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
python3 fetch.py

if [ ! -f "raw_content.txt" ]; then
    echo "沒有新文章，Pipeline 正常結束。"
    exit 0
fi

# 2. 呼叫 Gemini CLI 進行總結
echo "Step 2: AI 總結中..."
bash summarize.sh

# 3. 建立網頁與 RSS
echo "Step 3: 生成 HTML 與 RSS..."
python3 build_site.py

echo "=== Pipeline 執行完成 ==="
