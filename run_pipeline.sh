#!/bin/bash

# 切換到專案目錄
cd "$(dirname "$0")"

echo "=== [$(date)] 啟動新聞總結 Pipeline ==="

# 1. 啟動虛擬環境並抓取新聞
echo "Step 1: 抓取 RSS..."
source venv/bin/activate
python3 fetch.py

if [ ! -f "raw_content.txt" ]; then
    echo "沒有新文章，Pipeline 提早結束。"
    exit 0
fi

# 2. 呼叫 Gemini CLI 進行總結
echo "Step 2: AI 總結中..."
bash summarize.sh

# 3. 建立網頁與 RSS
echo "Step 3: 生成 HTML 與 RSS..."
python3 build_site.py

# 4. (選用) 自動部署到 GitHub Pages
# 註：這部分假設您已設定好 Git remote 並有權限 push
# echo "Step 4: 部署至 GitHub Pages..."
# git add index.html rss.xml summary.md feeds.yaml
# git commit -m "Auto-update news: $(date +'%Y-%m-%d')"
# git push origin gh-pages

echo "=== Pipeline 執行完成 ==="
