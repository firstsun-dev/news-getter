import markdown
from feedgen.feed import FeedGenerator
import datetime
import os
import glob

# 擴充 Markdown 轉換功能，確保支援標題、列表、表格等
def md_to_html_util(md_text):
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc', 'sane_lists'])

def convert_md_to_html(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # 修正 MD 中的內部連結
    md_content = md_content.replace(".md)", ".html)")
    html_body = md_to_html_util(md_content)
    title = os.path.basename(md_path).replace(".md", "").replace("_", " ")
    
    template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, "Noto Sans TC", "Microsoft JhengHei", serif; line-height: 1.8; max-width: 900px; margin: 0 auto; padding: 40px 20px; background: #fff; color: #1a1a1a; }}
            h1, h2, h3 {{ color: #000; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; margin-top: 1.5em; }}
            h3 {{ border-left: 5px solid #333; padding-left: 15px; border-bottom: none; }}
            a {{ color: #0366d6; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
            li {{ margin-bottom: 8px; }}
            .nav {{ margin-bottom: 30px; font-size: 0.9em; }}
            hr {{ height: 0.25em; padding: 0; margin: 24px 0; background-color: #e1e4e8; border: 0; }}
            @media (prefers-color-scheme: dark) {{ body {{ background: white; color: black; }} }}
        </style>
    </head>
    <body>
        <div class="nav"><a href="../../index.html">← 返回主編精選</a></div>
        {html_body}
    </body>
    </html>
    """
    html_path = md_path.replace(".md", ".html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(template)
    return html_path

def build_site():
    now = datetime.datetime.now()
    
    # 1. 先處理所有子分類的轉換
    md_files = glob.glob("history/*/*.md")
    for md in md_files:
        convert_md_to_html(md)

    # 2. 讀取主 summary.md 並解析
    if os.path.exists("summary.md"):
        with open("summary.md", "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 提取標題、簡介與各分類內容
        title_line = ""
        intro = ""
        categories = {} # {cat_name: {"content": str, "md_path": str}}
        current_cat = None
        
        for line in lines:
            if line.startswith("# "):
                title_line = line.strip("# \n")
            elif line.startswith("## ") or line.startswith("### "):
                header_text = line.lstrip("# ").strip()
                # 排除一些非分類的標題
                if "完整情報存檔" in header_text or "Deep Analysis" in header_text or "快速索引" in header_text:
                    current_cat = None
                    continue

                current_cat = header_text.replace("🔍", "").strip()
                categories[current_cat] = {"content": "", "md_path": ""}
            elif current_cat and ("獨立深度存檔頁面" in line or "獨立存檔頁面" in line) and "(" in line and ")" in line:
                # 提取 md 路徑
                path_part = line.split("(")[-1].split(")")[0]
                categories[current_cat]["md_path"] = path_part.replace(".md", ".html")
            elif current_cat:
                categories[current_cat]["content"] += line
            elif not current_cat and line.strip() and not line.startswith(">"):
                intro += line


        # 3. 建立 Table of Contents (ToC) 與 內容 HTML
        toc_html = "<h2>📌 快速索引 (ToC)</h2><ul>"
        content_html = ""
        
        for cat, data in categories.items():
            anchor = cat.replace(" ", "-").replace("/", "-")
            toc_html += f'<li><a href="#{anchor}">{cat}</a></li>'
            
            # 分類連結改放在標題下方
            archive_link = f'<p style="font-size:0.85em;"><a href="{data["md_path"]}">📂 查看此分類的獨立深度存檔頁面</a></p>' if data["md_path"] else ""
            cat_body = md_to_html_util(data["content"])
            
            content_html += f'<div id="{anchor}"><h2>🔍 {cat}</h2>{archive_link}{cat_body}</div><hr>'
        
        toc_html += "</ul>"

        # 4. 獲取歷史列表連結，依日期群組顯示所有分類深度頁面
        from collections import defaultdict
        history_dirs = sorted(glob.glob("history/*/"), reverse=True)
        daily_groups = defaultdict(list)
        for hdir in history_dirs:
            dirname = os.path.basename(hdir.rstrip("/"))
            date_part = dirname[:10]
            daily_groups[date_part].append(dirname)

        history_links = ""
        for date in sorted(daily_groups.keys(), reverse=True):
            history_links += f'<li class="history-day"><span class="history-date">{date}</span><ul class="history-runs">'
            for dirname in sorted(daily_groups[date], reverse=True):
                time_part = dirname[11:].replace("-", ":")
                html_files = sorted(glob.glob(f"history/{dirname}/*.html"))
                cat_links = " &nbsp;·&nbsp; ".join(
                    f'<a href="history/{dirname}/{os.path.basename(f)}">{os.path.basename(f).replace(".html","").replace("_"," ")}</a>'
                    for f in html_files
                )
                history_links += f'<li><span class="run-time">{time_part}</span> {cat_links}</li>'
            history_links += '</ul></li>'

        index_template = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI 新聞深度情報中心</title>
            <style>
                :root {{ --primary-blue: #0366d6; --bg-gray: #f8f9fa; --text-main: #1a1a1a; }}
                body {{ font-family: -apple-system, "Noto Sans TC", "Microsoft JhengHei", serif; line-height: 1.8; margin: 0; padding: 0; background: var(--bg-gray); color: var(--text-main); }}
                
                .header-banner {{ background: #333; color: white; padding: 40px 20px; text-align: center; }}
                .header-banner h1 {{ margin: 0; font-size: 2em; }}
                
                .main-wrapper {{ display: flex; max-width: 1200px; margin: 40px auto; gap: 40px; padding: 0 20px; }}
                
                .sidebar {{ width: 280px; position: sticky; top: 20px; height: fit-content; max-height: 90vh; overflow-y: auto; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
                .sidebar h2 {{ font-size: 1.2em; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
                .sidebar ul {{ list-style: none; padding: 0; margin: 0; }}
                .sidebar li {{ margin-bottom: 12px; }}
                .sidebar a {{ color: #555; text-decoration: none; font-size: 0.95em; transition: color 0.2s; }}
                .sidebar a:hover {{ color: var(--primary-blue); }}
                
                .content-area {{ flex: 1; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); min-width: 0; }}
                h2 {{ font-size: 1.8em; margin-top: 0; color: #2c3e50; border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; }}
                h3 {{ margin-top: 35px; border-left: 5px solid #333; padding-left: 15px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                a {{ color: var(--primary-blue); text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                
                .history {{ margin-top: 60px; padding-top: 30px; border-top: 2px solid #eee; font-size: 0.9em; color: #666; }}
                .history-day {{ list-style: none; margin-bottom: 14px; }}
                .history-date {{ font-weight: bold; color: #333; display: block; margin-bottom: 4px; }}
                .history-runs {{ list-style: none; padding-left: 12px; margin: 4px 0 0 0; }}
                .history-runs li {{ margin-bottom: 4px; line-height: 1.6; }}
                .run-time {{ color: #999; font-size: 0.88em; margin-right: 6px; }}
                .history ul {{ padding-left: 0; }}
                
                @media (max-width: 900px) {{
                    .main-wrapper {{ flex-direction: column; }}
                    .sidebar {{ width: auto; position: static; max-height: none; }}
                    .content-area {{ padding: 25px; }}
                }}
                
                @media (prefers-color-scheme: dark) {{
                    /* For e-ink compatibility, we keep light mode mostly, but can adjust here */
                }}
            </style>
        </head>
        <body>
            <div class="header-banner">
                <h1>{title_line}</h1>
                <p>最後更新時間: {now.strftime('%Y-%m-%d %H:%M')}</p>
            </div>
            
            <div class="main-wrapper">
                <nav class="sidebar">
                    {toc_html.replace("📌 快速索引 (ToC)", "📂 內容導覽")}
                </nav>
                
                <main class="content-area">
                    {content_html}
                    
                    <div class="history">
                        <h3>📚 歷史情報存檔 (Archive)</h3>
                        <ul>{history_links}</ul>
                    </div>
                </main>
            </div>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(index_template)

def build_rss():
    now = datetime.datetime.now()
    timestamp_str = now.strftime('%Y-%m-%d_%H-%M')
    fg = FeedGenerator()
    base_url = "https://firstsun-dev.github.io/news-getter/"
    fg.id(base_url)
    fg.title("AI News Intelligence Digest")
    fg.link(href=base_url, rel="alternate")
    fg.description("Deep AI-summarized intelligence from global sources.")
    fg.language("zh-TW")

    if os.path.exists("summary.md"):
        with open("summary.md", "r", encoding="utf-8") as f:
            summary_md = f.read()
        
        summary_rss = summary_md.replace("./history/", f"{base_url}history/")
        summary_rss = summary_rss.replace(".md)", ".html)")
        html_content = md_to_html_util(summary_rss)
        
        fe = fg.add_entry()
        fe.id(timestamp_str)
        fe.title(f"AI 新聞深度摘要 - {now.strftime('%Y-%m-%d %H:%M')}")
        fe.link(href=base_url)
        fe.content(html_content, type="html")
        fe.published(datetime.datetime.now(datetime.timezone.utc))

    fg.rss_file("rss.xml")

if __name__ == "__main__":
    build_site()
    build_rss()
    print("Successfully optimized UI and fixed navigation.")
