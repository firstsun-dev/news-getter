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
        try:
            result = subprocess.run(["find", "/Users", "/opt", "-name", "gemini", "-type", "f", "-perm", "+111"], capture_output=True, text=True)
            if result.stdout:
                gemini_bin = result.stdout.splitlines()[0]
        except:
            pass

    if not gemini_bin:
        print("❌ 錯誤: 找不到 gemini 指令")
        return ""

    process = subprocess.Popen(
        [gemini_bin, "-p", "", "--skip-trust"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate(input=prompt)
    
    if process.returncode != 0:
        print(f"Gemini 執行出錯: {stderr}")
        return ""
    
    lines = stdout.splitlines()
    cleaned = [l for l in lines if not any(noise_term in l for noise_term in ["MCP issues", "Ripgrep is not available", "Tool with name", "overriding"])]
    content = "\n".join(cleaned).strip()
    
    # 清理 AI 加上去的 code block
    if content.startswith("```"):
        content = "\n".join(content.splitlines()[1:-1]) if content.endswith("```") else "\n".join(content.splitlines()[1:])
    return content

def summarize_all():
    if not os.path.exists("raw_data.json"):
        print("找不到 raw_data.json")
        return

    with open("raw_data.json", "r", encoding="utf-8") as f:
        categorized_data = json.load(f)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    base_dir = f"history/{timestamp}"
    os.makedirs(base_dir, exist_ok=True)
    
    deep_summaries = {}
    
    cat_order = ["Strategy", "Global", "Finance", "Investments", "AI", "Energy", "Technology", "TW Social", "TW News"]
    sorted_categories = sorted(categorized_data.keys(), key=lambda x: cat_order.index(x) if x in cat_order else 999)

    # 第一階段：針對每個分類產出極其詳盡的內容
    for category in sorted_categories:
        articles = categorized_data[category]
        print(f"正在產出詳細專報: {category} ({len(articles)} 篇文章)...")
        
        content_text = ""
        for art in articles:
            content_text += f"Source: {art['source']}\nTitle: {art['title']}\nLink: {art['link']}\nContent: {art['content']}\n{'-'*20}\n"
            
        prompt_deep = f"""你是一位資深的產業分析師。請針對以下『{category}』分類的新聞內容進行【極其詳盡】的深度總結。
要求：
1. **不限篇幅**：挖掘大量細節，針對每個重要事件產出 3-5 句的深度摘要。
2. **多維度分析**：解釋事件背景、對產業的衝擊、以及未來的觀察重點。
3. **強制來源連結**：在每個要點末尾，必須精確附上對應的 [原文連結](網址)。
4. 輸出必須是純 Markdown 格式。

待處理內容：
{content_text}
"""
        summary = run_gemini(prompt_deep)
        if summary:
            deep_summaries[category] = summary
            file_cat = category.replace("/", "_").replace(" ", "_")
            with open(f"{base_dir}/{file_cat}.md", "w", encoding="utf-8") as f:
                f.write(f"# {category} 深度專報 ({timestamp.replace('_', ' ')})\n\n{summary}")

    # 第二階段：針對每個分類個別產出精簡版，確保所有分類都出現在首頁
    print("正在產出首頁精簡版摘要...")
    executive_parts = []
    for cat, summ in deep_summaries.items():
        prompt_concise = f"""你是一位高級主編。以下是『{cat}』分類的深度報告。
請從中挑出 2-3 個「最高信號」的重點，寫成首頁精華摘要。

要求：
1. **格式要求**：輸出必須以 `## 🔍 {cat}` 作為第一行標題。
2. **極度精簡**：每個重點濃縮成 1-2 句話。
3. **保留來源**：每個重點末尾附上 [原文連結](網址)。
4. 語氣：乾脆、果斷、專業。
5. 輸出為純 Markdown 格式，不要加任何額外說明。

深度報告內容如下：
{summ[:8000]}
"""
        part = run_gemini(prompt_concise)
        if part:
            executive_parts.append(part)
    executive_overview = "\n\n".join(executive_parts)

    # 產生主頁 summary.md
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"# 📅 每日情報精選 ({timestamp.replace('_', ' ')})\n\n")
        f.write("> 💡 首頁僅顯示最核心重點。如需深入分析，請點擊各分類下方的『完整深度報告』連結。\n\n")
        
        # 我們解析 AI 產出的內容，並確保格式正確
        # 注意：我們在每個分類標題下補上連結
        lines = executive_overview.splitlines()
        for line in lines:
            f.write(line + "\n")
            if line.startswith("## 🔍 "):
                cat_name = line.replace("## 🔍 ", "").strip()
                # 尋找對應的 md 檔案路徑
                matched_cat = next((c for c in deep_summaries.keys() if c in cat_name), None)
                if matched_cat:
                    file_cat = matched_cat.replace("/", "_").replace(" ", "_")
                    f.write(f"[查看此分類的獨立存檔頁面](./history/{timestamp}/{file_cat}.md)\n")

if __name__ == "__main__":
    summarize_all()
