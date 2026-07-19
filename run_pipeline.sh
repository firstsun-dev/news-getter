#!/bin/bash
# 新聞深度總結 Pipeline
#
# 用法：
#   ./run_pipeline.sh            # 完整流程：fetch → summarize → build_site.py → Astro build
#   ./run_pipeline.sh data-only  # 只跑 Python 階段，產出 data/ JSON，不蓋 Astro（CI 的 data-fetch 用）

set -euo pipefail

cd "$(dirname "$0")"

MODE="${1:-full}"

echo "=== [$(date)] 啟動新聞深度總結 Pipeline (mode: $MODE) ==="

if [ ! -d ".venv" ]; then
    echo "正在建立隔離的 Python 虛擬環境 (.venv)..."
    python3 -m venv .venv
fi

echo "Step 1: 啟動環境並抓取 RSS..."
source .venv/bin/activate
./.venv/bin/pip install --upgrade pip --quiet
./.venv/bin/pip install -r requirements.txt --quiet
PYTHONPATH=. ./.venv/bin/python3 src/fetch.py

if [ ! -f "data/raw_data.json" ]; then
    echo "沒有新文章，Pipeline 正常結束。"
    exit 0
fi

echo "Step 2: 執行各領域深度總結 (AI 分析中)..."
PYTHONPATH=. ./.venv/bin/python3 src/summarizer.py

echo "Step 3: 生成 data/ JSON..."
PYTHONPATH=. ./.venv/bin/python3 src/build_site.py

if [ "$MODE" = "data-only" ]; then
    echo "=== Pipeline (data-only) 執行完成 ==="
    exit 0
fi

echo "Step 4: Astro build → dist/..."
if ! command -v npm >/dev/null 2>&1; then
    echo "npm 未安裝，跳過 Astro build。"
    exit 0
fi
cd astro-src
if [ ! -d node_modules ]; then
    npm ci
fi
npm run build

echo "=== Pipeline 執行完成 ==="