#!/bin/bash

# 啟用嚴格模式：任一指令失敗、變數未定義、或管線中途失敗，即刻停止執行
set -euo pipefail

# 切換到腳本所在的絕對路徑
cd "$(dirname "$0")"

echo "=== [$(date)] 啟動新聞總結 Pipeline ==="

# 1. 檢查並啟動虛擬環境
if [ ! -d "venv" ]; then
    echo "正在建立 Python 虛擬環境..."
    python3 -m venv venv
fi

echo "Step 1: 啟動環境並抓取 RSS..."
source venv/bin/activate
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
