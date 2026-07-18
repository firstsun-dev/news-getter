#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== 1. 刪除根目錄舊檔 ==="
git rm -f fetch.py store.py scoring.py summarizer.py build_site.py 2>/dev/null || true
git rm -f test_fetch.py test_store.py test_scoring.py test_summarizer_schema.py 2>/dev/null || true
git rm -f feeds.yaml 2>/dev/null || true

echo "=== 2. 搬移 raw_data.json ==="
if [ -f raw_data.json ]; then
    git mv raw_data.json data/raw_data.json 2>/dev/null || mv raw_data.json data/raw_data.json
fi

echo "=== 3. 暫存新檔案 ==="
git add src/ test/ config/ data/ 2>/dev/null || true
git add .gitignore run_pipeline.sh AGENTS.md 2>/dev/null || true

echo "=== 4. 跑測試 ==="
source .venv/bin/activate
PYTHONPATH=. python3 -m unittest discover -s test -v

echo "=== 完成 ==="
