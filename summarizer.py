import html
import json
import logging
import os
import re
import subprocess
import datetime

from pydantic import BaseModel, Field, HttpUrl, ValidationError

from scoring import score_story, qualifies_for_deep_analysis

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

PLACEHOLDER_PATTERN = re.compile(r"待補充|TBD|TODO|placeholder", re.IGNORECASE)


class StoryDigest(BaseModel):
    fact_summary: str = Field(min_length=20, max_length=400)
    judgment: str = Field(min_length=20, max_length=600)
    used_source_urls: list[HttpUrl] = Field(min_length=1, max_length=3)


def parse_digest(raw_text: str, allowed_urls: set[str]):
    """Parse and validate a Gemini JSON response into a StoryDigest.

    Returns (StoryDigest, None) on success, or (None, reason) on failure.
    """
    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"invalid JSON: {e}"

    try:
        digest = StoryDigest(**data)
    except ValidationError as e:
        return None, f"schema validation failed: {e}"

    if PLACEHOLDER_PATTERN.search(digest.fact_summary) or PLACEHOLDER_PATTERN.search(digest.judgment):
        return None, "placeholder text detected"

    used = {str(u) for u in digest.used_source_urls}
    if not used.issubset(allowed_urls):
        return None, f"used_source_urls not subset of input URLs: {used - allowed_urls}"

    return digest, None


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


def group_stories(articles):
    """Group a category's articles (already carrying tier/role/sources from fetch.py)
    by fingerprint, so a story hit by multiple feeds in the same run is scored once."""
    grouped = {}
    for art in articles:
        fp = art.get("fingerprint") or art["link"]
        if fp not in grouped:
            grouped[fp] = {
                "title": art["title"],
                "articles": [],
                "sources": art.get("sources") or [{"name": art["source"], "tier": art["tier"], "role": art["role"]}],
                "seen_count": art.get("seen_count", 1),
            }
        grouped[fp]["articles"].append(art)
        # sources/seen_count reflect the latest state seen for this fingerprint in this run
        grouped[fp]["sources"] = art.get("sources") or grouped[fp]["sources"]
        grouped[fp]["seen_count"] = max(grouped[fp]["seen_count"], art.get("seen_count", 1))
    return grouped


def build_prompt_deep(story, allowed_urls):
    content_text = ""
    for art in story["articles"]:
        content_text += f"Source: {art['source']}\nTitle: {art['title']}\nLink: {art['link']}\nContent: {art['content']}\n{'-'*20}\n"

    source_names = ", ".join(sorted({s["name"] for s in story["sources"]}))
    urls_list = "\n".join(f"- {u}" for u in sorted(allowed_urls))

    return f"""你是一位資深的產業分析師。請針對以下同一則新聞的輸入內容，輸出【純 JSON】（不要任何 Markdown 或說明文字），格式如下：

{{"fact_summary": "20-400字的事實摘要，只能陳述輸入內容裡出現的事實", "judgment": "20-600字的產業判斷或影響分析", "used_source_urls": ["至少 1 個、最多 3 個你在 judgment 中引用依據的連結，必須完全取自下方允許的連結清單"]}}

規則：
1. `used_source_urls` 裡的每個網址都必須逐字取自「允許的連結清單」，不可自行編造或修改。
2. `fact_summary`/`judgment` 不可包含「待補充」「TBD」「TODO」「placeholder」等佔位詞。
3. 不要輸出 JSON 以外的任何文字。

累積證據：seen_count={story['seen_count']}，獨立來源={source_names}

允許的連結清單：
{urls_list}

輸入內容：
{content_text}
"""


def render_story_block(title, digest: StoryDigest, scores: dict):
    fact = html.escape(digest.fact_summary)
    judgment = html.escape(digest.judgment)
    links = "".join(
        f' <a href="{html.escape(str(u))}">[來源]</a>' for u in digest.used_source_urls
    )
    return f"""#### {html.escape(title)}

<span class="score-badge confidence">confidence: {scores['confidence']}</span> <span class="score-badge heat">heat: {scores['heat']}</span>

<div class="fact-block"><strong>事實</strong>：{fact}</div>
<div class="judgment-block"><strong>判斷</strong>：{judgment}{links}</div>
"""


def render_headline_list(stories):
    lines = []
    for s in stories:
        min_tier = min(src["tier"] for src in s["sources"])
        link = s["articles"][0]["link"]
        lines.append(f"- [{html.escape(s['title'])}]({link}) (tier {min_tier}, seen_count={s['seen_count']}) — 觀察中")
    return "\n".join(lines)


def process_category(category, articles, base_dir, timestamp):
    stories = group_stories(articles)

    deep_blocks = []
    headline_stories = []

    for fp, story in stories.items():
        tiers = [s["tier"] for s in story["sources"]]
        distinct_sources = len({s["name"] for s in story["sources"]})
        scores = score_story(tiers=tiers, seen_count=story["seen_count"], distinct_sources=distinct_sources)

        if not qualifies_for_deep_analysis(scores):
            headline_stories.append(story)
            continue

        allowed_urls = {art["link"] for art in story["articles"]}
        prompt = build_prompt_deep(story, allowed_urls)
        raw_response = run_gemini(prompt)

        if not raw_response:
            logging.warning("Gemini 無回應，story 降級為速報: %s", story["title"])
            headline_stories.append(story)
            continue

        digest, reason = parse_digest(raw_response, allowed_urls)
        if digest is None:
            logging.warning("Story 被丟棄（%s）: %s", reason, story["title"])
            headline_stories.append(story)
            continue

        deep_blocks.append(render_story_block(story["title"], digest, scores))

    body_parts = []
    if deep_blocks:
        body_parts.extend(deep_blocks)
    else:
        body_parts.append("> 本次無達標深度分析\n")

    if headline_stories:
        body_parts.append("#### 觀察中（未達深度分析門檻）\n\n" + render_headline_list(headline_stories))

    body = "\n\n".join(body_parts)

    file_cat = category.replace("/", "_").replace(" ", "_")
    with open(f"{base_dir}/{file_cat}.md", "w", encoding="utf-8") as f:
        f.write(f"# {category} 深度專報 ({timestamp.replace('_', ' ')})\n\n{body}")

    return body


def summarize_all():
    if not os.path.exists("raw_data.json"):
        print("找不到 raw_data.json")
        return

    with open("raw_data.json", "r", encoding="utf-8") as f:
        categorized_data = json.load(f)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    base_dir = f"history/{timestamp}"
    os.makedirs(base_dir, exist_ok=True)

    cat_order = ["Strategy", "Global", "Finance", "Investments", "AI", "Energy", "Technology", "TW Social", "TW News"]
    sorted_categories = sorted(categorized_data.keys(), key=lambda x: cat_order.index(x) if x in cat_order else 999)

    category_bodies = {}
    for category in sorted_categories:
        articles = categorized_data[category]
        print(f"正在處理分類: {category} ({len(articles)} 篇文章)...")
        body = process_category(category, articles, base_dir, timestamp)
        category_bodies[category] = body

    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"# 📅 每日情報精選 ({timestamp.replace('_', ' ')})\n\n")
        f.write("> 💡 首頁顯示通過收斂門禁的深度分析（事實/判斷雙區塊 + confidence/heat）。如需完整清單，請點擊各分類下方的『完整深度報告』連結。\n\n")

        for category in sorted_categories:
            f.write(f"## 🔍 {category}\n")
            f.write(category_bodies[category] + "\n")
            file_cat = category.replace("/", "_").replace(" ", "_")
            f.write(f"[查看此分類的獨立存檔頁面](./history/{timestamp}/{file_cat}.md)\n\n")


if __name__ == "__main__":
    summarize_all()
