import markdown
from feedgen.feed import FeedGenerator
import datetime
import os
import glob

def build_site(summary_md):
    now = datetime.datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    timestamp_str = now.strftime('%Y-%m-%d_%H-%M')
    html_content = markdown.markdown(summary_md)
    
    # 1. Save this report to history with timestamp to support multiple updates per day
    os.makedirs("history", exist_ok=True)
    history_filename = f"history/{timestamp_str}.html"
    
    # Create the standalone daily page
    daily_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>AI 新聞總結 - {timestamp_str}</title>
        <style>
            body {{ font-family: serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background: white; color: black; }}
            h1, h2 {{ border-bottom: 1px solid black; }}
            a {{ color: black; text-decoration: underline; }}
            .nav {{ margin-bottom: 20px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="nav"><a href="../index.html">← 回首頁</a></div>
        <h1>AI 新聞總結 - {timestamp_str}</h1>
        {html_content}
    </body>
    </html>
    """
    with open(history_filename, "w") as f:
        f.write(daily_template)

    # 2. Build index.html with the latest summary AND links to history
    history_files = sorted(glob.glob("history/*.html"), reverse=True)
    # Display formatted date-time in the link list
    history_links = "".join([f'<li><a href="{f}">{os.path.basename(f).replace(".html", "").replace("_", " ")}</a></li>' for f in history_files])

    index_template = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>每日 AI 新聞總結</title>
        <style>
            body {{ font-family: serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; background: white; color: black; }}
            h1, h2 {{ border-bottom: 1px solid black; }}
            a {{ color: black; text-decoration: underline; }}
            .history {{ margin-top: 50px; border-top: 2px solid black; padding-top: 20px; }}
            .meta {{ font-style: italic; color: #555; }}
            @media (prefers-color-scheme: dark) {{
                body {{ background: white; color: black; }}
            }}
        </style>
    </head>
    <body>
        <h1>最新 AI 新聞總結</h1>
        <p class="meta">最後更新時間: {now.strftime('%Y-%m-%d %H:%M')}</p>
        {html_content}
        
        <div class="history">
            <h2>歷史回顧 (Archive)</h2>
            <ul>
                {history_links}
            </ul>
        </div>
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(index_template)

def build_rss(summary_md):
    now = datetime.datetime.now()
    timestamp_str = now.strftime('%Y-%m-%d_%H-%M')
    fg = FeedGenerator()
    base_url = "https://firstsun-dev.github.io/news-getter/"
    fg.id(base_url)
    fg.title("AI News Aggregator Digest")
    fg.author({'name': 'Gemini CLI', 'email': 'gemini@example.com'})
    fg.link(href=base_url, rel="alternate")
    fg.description("Daily AI-summarized news digest from selected RSS feeds.")
    fg.language("zh-TW")

    # Add current item
    fe = fg.add_entry()
    fe.id(timestamp_str)
    fe.title(f"AI 新聞摘要 - {now.strftime('%Y-%m-%d %H:%M')}")
    fe.link(href=f"{base_url}history/{timestamp_str}.html")
    
    html_content = markdown.markdown(summary_md)
    fe.content(html_content, type="html")
    fe.published(datetime.datetime.now(datetime.timezone.utc))

    fg.rss_file("rss.xml")

if __name__ == "__main__":
    if os.path.exists("summary.md"):
        with open("summary.md", "r") as f:
            summary_md = f.read()
        
        build_site(summary_md)
        build_rss(summary_md)
        print("Successfully updated index.html, rss.xml and history archive.")
    else:
        print("Error: summary.md not found.")
