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
            elif line.startswith("## 🔍 "):
                current_cat = line.strip("# 🔍 \n")
                categories[current_cat] = {"content": "", "md_path": ""}
            elif current_cat and "[查看" in line and "獨立存檔頁面]" in line:
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

        # 4. 獲取歷史列表連結 (修正連結失效問題)
        history_dirs = sorted(glob.glob("history/*/"), reverse=True)
        history_links = ""
        for hdir in history_dirs:
            # 嘗試找該目錄下的 Finance.html 作為代表，或只連結到目錄(如果 Server 支援 index)
            dname = os.path.basename(hdir.rstrip("/")).replace("_", " ").replace("-", "/")
            # 建立一個指向該次更新 index 的路徑 (雖然目前沒做子目錄 index，我們先連到 Finance 或第一個檔)
            first_file = glob.glob(f"{hdir}/*.html")
            target = first_file[0] if first_file else "#"
            history_links += f'<li><a href="{target}">{dname}</a></li>'

        index_template = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI 新聞深度情報中心</title>
            <style>
                body {{ font-family: -apple-system, "Noto Sans TC", "Microsoft JhengHei", serif; line-height: 1.8; max-width: 1000px; margin: 0 auto; padding: 40px 20px; background: #f8f9fa; color: #1a1a1a; }}
                .container {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
                h1 {{ font-size: 2.2em; border-bottom: 3px solid #333; padding-bottom: 10px; }}
                h2 {{ font-size: 1.5em; margin-top: 2em; color: #2c3e50; }}
                a {{ color: #0366d6; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                .toc {{ background: #f1f3f5; padding: 20px; border-radius: 5px; margin: 30px 0; }}
                .toc ul {{ margin: 0; }}
                .history {{ margin-top: 60px; padding-top: 30px; border-top: 2px solid #eee; font-size: 0.9em; }}
                @media (prefers-color-scheme: dark) {{ body {{ background: #f8f9fa; color: #1a1a1a; }} }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title_line}</h1>
                <p class="meta">最後更新時間: {now.strftime('%Y-%m-%d %H:%M')}</p>
                
                <div class="toc">{toc_html}</div>
                
                <div class="main-content">
                    {content_html}
                </div>
                
                <div class="history">
                    <h3>📚 歷史情報存檔 (Archive)</h3>
                    <ul>{history_links}</ul>
                </div>
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
