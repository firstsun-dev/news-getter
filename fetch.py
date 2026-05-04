import feedparser
import yaml
import datetime
from bs4 import BeautifulSoup
import os

def clean_html(html):
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def fetch_feeds():
    with open("feeds.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    feeds = config.get("feeds", [])
    all_articles = []
    
    now = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = now - datetime.timedelta(days=1)
    
    for feed_info in feeds:
        print(f"Fetching: {feed_info['name']}...")
        parsed = feedparser.parse(feed_info["url"])
        
        for entry in parsed.entries:
            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            # Filter by date (last 24 hours)
            if published and published < one_day_ago:
                continue
                
            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].value
            elif hasattr(entry, "summary"):
                content = entry.summary
                
            all_articles.append({
                "source": feed_info["name"],
                "category": feed_info["category"],
                "title": entry.title,
                "link": entry.link,
                "content": clean_html(content)[:1000] # Limit content for summarization
            })
            
    return all_articles

def save_for_summarization(articles):
    with open("raw_content.txt", "w") as f:
        for art in articles:
            f.write(f"Source: {art['source']} ({art['category']})\n")
            f.write(f"Title: {art['title']}\n")
            f.write(f"Link: {art['link']}\n")
            f.write(f"Content: {art['content']}\n")
            f.write("-" * 40 + "\n\n")

import sys

# ... (keep existing imports and functions)

if __name__ == "__main__":
    try:
        articles = fetch_feeds()
        if articles:
            save_for_summarization(articles)
            print(f"Successfully fetched {len(articles)} articles and saved to raw_content.txt")
        else:
            print("No new articles found in the last 24 hours.")
            if os.path.exists("raw_content.txt"):
                os.remove("raw_content.txt")
            # 這裡我們選擇退出 code 0 因為「沒新聞」通常不視為系統錯誤
            # 但如果您希望沒新聞也算失敗，可以改為 sys.exit(1)
            sys.exit(0)
    except Exception as e:
        print(f"Error during fetching: {e}")
        sys.exit(1)
