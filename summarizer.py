import json
import os
import subprocess
import datetime

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
            # 測試路徑是否有效
            cmd = ["which", path] if not path.startswith("/") else ["ls", path]
            if subprocess.run(cmd, capture_output=True).returncode == 0:
                gemini_bin = path
                break
        except:
            continue
            
    if not gemini_bin:
        raise Exception("找不到 gemini 指令")

    # 執行總結
    process = subprocess.Popen(
        [gemini_bin, "-p", "", "--skip-trust"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
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
    
    for category, articles in categorized_data.items():
        print(f"正在深度總結分類: {category} ({len(articles)} 篇文章)...")
        
        # 組裝文章內容
        content_text = ""
        for art in articles:
            content_text += f"Source: {art['source']}\nTitle: {art['title']}\nLink: {art['link']}\nContent: {art['content']}\n{'-'*20}\n"
            
        prompt = f"""你是一位資深的產業分析師。請針對以下『{category}』分類的新聞內容進行深度總結。
要求：
1. **挖掘細節**：針對每個主要新聞，產出 3-5 句的深度摘要，包含事件經過與潛在影響。
2. **多維度分析**：解釋這些新聞背後的背景。
3. **強制附上來源**：在每個要點末尾，必須附上對應的 [原文連結](網址)。
4. 輸出必須是高品質的 Markdown 格式。

待處理內容：
{content_text}
"""
        summary = run_gemini(prompt)
        if summary:
            summaries[category] = summary
            # 存入個別分類檔案
            file_cat = category.replace("/", "_").replace(" ", "_")
            with open(f"{base_dir}/{file_cat}.md", "w", encoding="utf-8") as f:
                f.write(f"# {category} 深度專報\n\n{summary}")

    # 最後產生一個總體精選摘要 (Chief Editor View)
    print("正在產生總體精選摘要...")
    all_summary_text = "\n\n".join([f"## {cat}\n{summ}" for cat, summ in summaries.items()])
    
    prompt_chief = f"""你是一位新聞主編。以下是今日各個領域的深度摘要。
請幫我撰寫一份『今日情報精選』，字數約 500-800 字。
要求：
1. 挑選出今日最值得關注的 3-5 個跨領域核心大事件。
2. 以專業且具備洞察力的語氣撰寫。
3. **不要**列出所有細節，而是給予整體的宏觀評論。
4. 結尾請鼓勵讀者點擊各分類查看詳情。

各領域摘要如下：
{all_summary_text[:12000]} 
"""
    chief_summary = run_gemini(prompt_chief)
    
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"# 📅 每日新聞深度總結 ({timestamp.replace('_', ' ')})\n\n")
        f.write(f"## 🎙️ 主編精選導讀\n\n{chief_summary}\n\n---\n\n")
        f.write("## 🔍 分類深度報告 (點擊查看詳情)\n\n")
        for cat in summaries.keys():
            file_cat = cat.replace("/", "_").replace(" ", "_")
            f.write(f"*   [{cat} 深度專報](./history/{timestamp}/{file_cat}.md)\n")

if __name__ == "__main__":
    summarize_all()
