import markdown
from feedgen.feed import FeedGenerator
import datetime
import os

def build_html(summary_md):
    # Convert markdown to HTML
    html_content = markdown.markdown(summary_md)
    
    # Simple e-ink friendly template
    template = f"""
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
            @media (prefers-color-scheme: dark) {{
                body {{ background: white; color: black; }} /* Force light for e-ink */
            }}
        </style>
    </head>
    <body>
        <h1>今日 AI 新聞總結</h1>
        <p>更新時間: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        {html_content}
    </body>
    </html>
    """
    with open("index.html", "w") as f:
        f.write(template)

def build_rss(summary_md):
    fg = FeedGenerator()
    fg.id("https://claudiafang.github.io/news-getter/") # Replace with actual URL if known
    fg.title("AI News Aggregator Digest")
    fg.author({'name': 'Gemini CLI', 'email': 'gemini@example.com'})
    fg.link(href="https://claudiafang.github.io/news-getter/", rel="alternate")
    fg.description("Daily AI-summarized news digest from selected RSS feeds.")
    fg.language("zh-TW")

    # Add the latest summary as an item
    fe = fg.add_entry()
    fe.id(datetime.datetime.now().strftime('%Y-%m-%d'))
    fe.title(f"AI 新聞摘要 - {datetime.datetime.now().strftime('%Y-%m-%d')}")
    fe.link(href="https://claudiafang.github.io/news-getter/index.html")
    
    html_content = markdown.markdown(summary_md)
    fe.content(html_content, type="html")
    fe.published(datetime.datetime.now(datetime.timezone.utc))

    fg.rss_file("rss.xml")

if __name__ == "__main__":
    if os.path.exists("summary.md"):
        with open("summary.md", "r") as f:
            summary_md = f.read()
        
        build_html(summary_md)
        build_rss(summary_md)
        print("Successfully generated index.html and rss.xml")
    else:
        print("Error: summary.md not found.")
