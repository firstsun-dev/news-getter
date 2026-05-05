import json
import os
import subprocess
import datetime
import sys

def run_gemini(prompt):
    # 定義可能的 gemini 路徑
    search_paths = [
        "gemini",
        "/Users/tianyao/.nvm/versions/node/v22.21.1/bin/gemini",
        "/Users/claudia.fang/.nvm/versions/node/v22.21.1/bin/gemini",
        "/opt/homebrew/bin/gemini",
        "/usr/local/bin/gemini"
    ]
    
    gemini_bin = None
    for path in search_paths:
        try:
            cmd = ["which", path] if not path.startswith("/") else ["ls", path]
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                gemini_bin = path
                break
        except:
            continue
            
    if not gemini_bin:
        # 嘗試全域搜尋作為最後手段
        try:
            result = subprocess.run(["find", "/Users", "/opt", "-name", "gemini", "-type", "f", "-perm", "+111"], capture_output=True, text=True)
            if result.stdout:
                gemini_bin = result.stdout.splitlines()[0]
        except:
            pass

    if not gemini_bin:
        print("❌ 錯誤: 找不到 gemini 指令")
        return ""

    # 執行總結
    process = subprocess.Popen(
        [gemini_bin, "-p", "", "--skip-trust"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate(input=prompt)
    
    if process.returncode != 0:
        print(f"Gemini 執行出錯: {stderr}")
        return ""
    
    # 清理輸出雜訊
    lines = stdout.splitlines()
    cleaned = [l for l in lines if not any(noise_term in l for noise_term in ["MCP issues", "Ripgrep is not available", "Tool with name", "overriding"])]
    return "\n".join(cleaned).strip()

def summarize_all():
    if not os.path.exists("raw_data.json"):
        print("找不到 raw_data.json")
        return

    with open("raw_data.json", "r", encoding="utf-8") as f:
        categorized_data = json.load(f)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    base_dir = f"history/{timestamp}"
    os.makedirs(base_dir, exist_ok=True)
    
    summaries = {}
    
    # 按照特定順序排序分類
    cat_order = ["Strategy", "Global", "Finance", "Investments", "AI", "Energy", "Technology", "TW Social", "TW News"]
    sorted_categories = sorted(categorized_data.keys(), key=lambda x: cat_order.index(x) if x in cat_order else 999)

    for category in sorted_categories:
        articles = categorized_data[category]
        print(f"正在深度總結分類: {category} ({len(articles)} 篇文章)...")
        
        content_text = ""
        for art in articles:
            content_text += f"Source: {art['source']}\nTitle: {art['title']}\nLink: {art['link']}\nContent: {art['content']}\n{'-'*20}\n"
            
        prompt = f"""你是一位資深的產業分析師。請針對以下『{category}』分類的新聞內容進行【極其詳盡】的深度總結。

【輸出規範】：
1. **純 Markdown 格式**：僅輸出內容，不要包含任何開場白、結尾語、或 ```markdown 程式碼塊包裝。
2. **不限篇幅**：挖掘大量細節，針對每個重要事件產出 3-5 句的深度摘要。
3. **多維度分析**：解釋事件背景、對產業的衝擊、以及未來的觀察重點。
4. **強制來源連結**：在每個要點末尾，必須精確附上對應的 [原文連結](網址)。
5. **使用 H3 標題**：區分不同的新聞事件或主題。

待處理內容：
{content_text}
"""
        summary = run_gemini(prompt)
        
        # 強制清理可能存在的 code block 標籤 (AI 有時會手癢加上去)
        if summary.startswith("```"):
            summary = "\n".join(summary.splitlines()[1:-1]) if summary.endswith("```") else "\n".join(summary.splitlines()[1:])

        if summary:
            summaries[category] = summary
            # 存入個別分類檔案
            file_cat = category.replace("/", "_").replace(" ", "_")
            with open(f"{base_dir}/{file_cat}.md", "w", encoding="utf-8") as f:
                f.write(f"# {category} 深度專報 ({timestamp.replace('_', ' ')})\n\n{summary}")
    print("正在產生主頁摘要...")
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"# 📅 每日新聞深度總結 ({timestamp.replace('_', ' ')})\n\n")
        f.write("> 這是一份由 AI 彙整全球 300+ 權威來源產出的深度情報。\n\n")
        
        for cat, summ in summaries.items():
            file_cat = cat.replace("/", "_").replace(" ", "_")
            f.write(f"## 🔍 {cat}\n")
            f.write(f"{summ}\n\n")
            f.write(f"[查看 {cat} 獨立存檔頁面](./history/{timestamp}/{file_cat}.md)\n\n---\n\n")

if __name__ == "__main__":
    summarize_all()
