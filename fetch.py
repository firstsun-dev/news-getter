import feedparser
import yaml
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import json
import requests

import store

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
    fetch_window = now - datetime.timedelta(hours=15)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 news-getter/1.0'
    }
    
    for feed_info in feeds:
        print(f"Fetching: {feed_info['name']}...")
        try:
            response = requests.get(feed_info["url"], headers=headers, timeout=15)
            parsed = feedparser.parse(response.content)
            if not parsed.entries:
                parsed = feedparser.parse(feed_info["url"])
        except Exception as e:
            print(f"Error fetching {feed_info['name']}: {e}")
            continue
        
        for entry in parsed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime.datetime(*entry.updated_parsed[:6], tzinfo=datetime.timezone.utc)
            
            if published and published < fetch_window:
                continue
                
            content = ""
            if hasattr(entry, "content"):
                content = entry.content[0].value
            elif hasattr(entry, "summary"):
                content = entry.summary
                
            all_articles.append({
                "source": feed_info["name"],
                "category": feed_info["category"],
                "tier": feed_info["tier"],
                "role": feed_info["role"],
                "title": entry.title,
                "link": urljoin(feed_info["url"], entry.link),
                "content": clean_html(content)[:1200]
            })
            
    return all_articles

def persist_and_enrich(articles):
    enriched = []
    for art in articles:
        story = store.upsert_story(art)
        enriched.append({
            **art,
            "fingerprint": story["fingerprint"],
            "seen_count": story["seen_count"],
            "sources": story["sources"],
        })
    return enriched

def save_structured_data(articles):
    categorized = {}
    for art in articles:
        cat = art["category"]
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(art)

    with open("raw_data.json", "w", encoding="utf-8") as f:
        json.dump(categorized, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    try:
        articles = fetch_feeds()
        if articles:
            enriched = persist_and_enrich(articles)
            save_structured_data(enriched)
            print(f"Successfully fetched {len(enriched)} articles and saved to raw_data.json")
        else:
            print("No new articles found.")
            sys.exit(0)
    except Exception as e:
        print(f"Error during fetching: {e}")
        sys.exit(1)
