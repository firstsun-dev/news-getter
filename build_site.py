import markdown
from feedgen.feed import FeedGenerator
import datetime
import os
import glob

def convert_md_to_html(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    
    # 修正 MD 中的內部連結，從 .md 改為 .html
    md_content = md_content.replace(".md)", ".html)")
    
    html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    title = os.path.basename(md_path).replace(".md", "").replace("_", " ")
    
    template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ font-family: serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; background: white; color: black; }}
            h1, h2 {{ border-bottom: 2px solid black; padding-bottom: 10px; }}
            h3 {{ margin-top: 30px; border-left: 5px solid black; padding-left: 15px; border-bottom: 1px solid #eee; }}
            a {{ color: #0066cc; text-decoration: none; border-bottom: 1px solid #ccc; }}
            a:hover {{ border-bottom: 1px solid #0066cc; }}
            li {{ margin-bottom: 10px; }}
            .nav {{ margin-bottom: 30px; font-size: 0.9em; color: #666; }}
            @media (prefers-color-scheme: dark) {{
                body {{ background: white; color: black; }}
            }}
        </style>
    </head>
    <body>
        <div class="nav"><a href="../../index.html">← 回首頁</a></div>
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
    
    # 1. 轉換當前所有 history 子目錄下的 .md 為 .html
    md_files = glob.glob("history/*/*.md")
    for md in md_files:
        convert_md_to_html(md)

    # 2. 讀取主 summary.md 並產生 index.html
    if os.path.exists("summary.md"):
        with open("summary.md", "r", encoding="utf-8") as f:
            summary_md = f.read()
        
        # 修正 summary.md 中的連結，從 .md 改為 .html
        summary_md_fixed = summary_md.replace(".md)", ".html)")
        html_content = markdown.markdown(summary_md_fixed, extensions=['tables', 'fenced_code'])
        
        # 獲取歷史列表 (以目錄為單位)
        history_dirs = sorted(glob.glob("history/*/"), reverse=True)
        history_links = ""
        for hdir in history_dirs:
            dname = os.path.basename(hdir.rstrip("/")).replace("_", " ").replace("-", "/")
            # 找到該次更新的主入口（如果有）
            history_links += f'<li>{dname}</li>'

        index_template = f"""
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>每日 AI 新聞情報</title>
            <style>
                body {{ font-family: serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; background: white; color: black; }}
                h1, h2 {{ border-bottom: 2px solid black; padding-bottom: 10px; }}
                h3 {{ margin-top: 30px; border-left: 5px solid black; padding-left: 15px; border-bottom: 1px solid #eee; }}
                a {{ color: black; text-decoration: underline; }}
                .history {{ margin-top: 50px; border-top: 1px dashed #ccc; padding-top: 20px; color: #666; font-size: 0.8em; }}
                @media (prefers-color-scheme: dark) {{
                    body {{ background: white; color: black; }}
                }}
            </style>
        </head>
        <body>
            <h1>最新 AI 新聞情報深度總結</h1>
            <p>最後更新時間: {now.strftime('%Y-%m-%d %H:%M')}</p>
            {html_content}
            
            <div class="history">
                <h2>存檔目錄 (Archive)</h2>
                <ul>
                    {history_links}
                </ul>
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
    fg.description("Deep AI-summarized intelligence from selected global sources.")
    fg.language("zh-TW")

    if os.path.exists("summary.md"):
        with open("summary.md", "r", encoding="utf-8") as f:
            summary_md = f.read()
        
        # 在 RSS 中使用絕對路徑
        summary_rss = summary_md.replace("./history/", f"{base_url}history/")
        summary_rss = summary_rss.replace(".md)", ".html)")
        
        fe = fg.add_entry()
        fe.id(timestamp_str)
        fe.title(f"AI 新聞深度摘要 - {now.strftime('%Y-%m-%d %H:%M')}")
        fe.link(href=base_url)
        
        html_content = markdown.markdown(summary_rss, extensions=['tables', 'fenced_code'])
        fe.content(html_content, type="html")
        fe.published(datetime.datetime.now(datetime.timezone.utc))

    fg.rss_file("rss.xml")

if __name__ == "__main__":
    build_site()
    build_rss()
    print("Successfully built multi-page site and RSS feed.")
