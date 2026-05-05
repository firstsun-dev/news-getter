#!/bin/bash

# 啟用嚴格模式
set -euo pipefail

# 切換到腳本所在的絕對路徑
cd "$(dirname "$0")"

echo "=== [$(date)] 啟動新聞深度總結 Pipeline ==="

# 1. 檢查並建立隔離的虛擬環境 (.venv)
if [ ! -d ".venv" ]; then
    echo "正在建立隔離的 Python 虛擬環境 (.venv)..."
    python3 -m venv .venv
fi

echo "Step 1: 啟動環境並抓取 RSS..."
source .venv/bin/activate
./.venv/bin/pip install --upgrade pip --quiet
./.venv/bin/pip install -r requirements.txt --quiet
./.venv/bin/python3 fetch.py

if [ ! -f "raw_data.json" ]; then
    echo "沒有新文章，Pipeline 正常結束。"
    exit 0
fi

# 2. 執行深度總結
echo "Step 2: 執行各領域深度總結 (AI 分析中)..."
./.venv/bin/python3 summarizer.py

# 3. 建立多頁面網頁與 RSS
echo "Step 3: 生成 HTML 結構與 RSS..."
./.venv/bin/python3 build_site.py

echo "=== Pipeline 執行完成 ==="
