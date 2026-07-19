import json
import re
import html
import datetime
import os
import glob

import markdown


MIN_CATEGORIES_PER_RUN = 5


def md_to_html(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'sane_lists'])


def render_fact_html(fact_summary: str) -> str:
    return f'<div class="fact-block"><strong>事實</strong>：{html.escape(fact_summary)}</div>'


def render_judgment_html(judgment: str, used_source_urls: list[str]) -> str:
    links = "".join(f' <a href="{html.escape(u)}">[來源]</a>' for u in used_source_urls)
    return f'<div class="judgment-block"><strong>判斷</strong>：{html.escape(judgment)}{links}</div>'


def load_category_archive(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def archive_to_category_data(archive: dict, run_dirname: str) -> dict:
    cat_name = archive["category"]
    anchor = cat_name.replace(" ", "-").replace("/", "-")
    stories = []
    for s in archive.get("stories", []):
        body_md = s.get("body_md", "")
        if body_md:
            fact_html = ""
            judgment_html = md_to_html(body_md)
        else:
            fact_html = render_fact_html(s.get("fact_summary", ""))
            judgment_html = render_judgment_html(s.get("judgment", ""), s.get("used_source_urls", []))
        stories.append({
            "title": s["title"],
            "confidence": s.get("confidence"),
            "heat": s.get("heat"),
            "fact_html": fact_html,
            "judgment_html": judgment_html,
        })
    watchlist = [
        {
            "title": w["title"],
            "url": w["url"],
            "tier": w["tier"],
            "seen_count": w["seen_count"],
        }
        for w in archive.get("watchlist", [])
    ]
    return {
        "name": cat_name,
        "anchor": anchor,
        "archive_url": f"./history/{run_dirname}/index.html#{anchor}",
        "stories": stories,
        "watchlist": watchlist,
        "no_signal": archive.get("no_signal", False),
        "deep_count": len(stories),
        "watch_count": len(watchlist),
    }


def build_day_json(date_str):
    year, month, day = date_str.split("-")
    day_data = {"date": date_str, "runs": []}

    for run_dir in sorted(glob.glob(f"history/{date_str}_*/")):
        dirname = os.path.basename(run_dir.rstrip("/"))
        m = re.match(r'^\d{4}-\d{2}-\d{2}_(\d{2}-\d{2})$', dirname)
        if not m:
            continue

        json_files = sorted(glob.glob(f"{run_dir}/*.json"))
        if len(json_files) < MIN_CATEGORIES_PER_RUN:
            print(f"跳過殘缺 run {dirname}（僅 {len(json_files)} 個 category，門檻 {MIN_CATEGORIES_PER_RUN}）")
            continue

        time_str = m.group(1).replace("-", ":")
        categories = []
        for json_file in json_files:
            archive = load_category_archive(json_file)
            categories.append(archive_to_category_data(archive, dirname))

        day_data["runs"].append({"time": time_str, "categories": categories})

    out_dir = os.path.join("data", year, month)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{date_str}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(day_data, f, ensure_ascii=False, indent=2)

    return day_data


def build_history_index():
    index = []
    for year_dir in sorted(glob.glob("data/????/"), reverse=True):
        for month_dir in sorted(glob.glob(f"{year_dir}??/"), reverse=True):
            for day_file in sorted(glob.glob(f"{month_dir}????-??-??.json"), reverse=True):
                with open(day_file, "r", encoding="utf-8") as f:
                    day_data = json.load(f)
                runs_summary = []
                for run in day_data.get("runs", []):
                    runs_summary.append({
                        "time": run["time"],
                        "categories": [c["name"] for c in run.get("categories", [])]
                    })
                index.append({
                    "date": day_data["date"],
                    "runs": runs_summary
                })

    os.makedirs("data", exist_ok=True)
    with open("data/history_index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    return index


def build_site():
    now = datetime.datetime.now()

    if not os.path.exists("summary.md"):
        print("summary.md not found, skipping site build")
        return

    with open("summary.md", "r", encoding="utf-8") as f:
        summary_text = f.read()

    ts_match = re.search(r'\((\d{4}-\d{2}-\d{2})[_ ](\d{2}[-:]\d{2})\)', summary_text)
    ts_display = ts_match.group(0).strip("()") if ts_match else now.strftime("%Y-%m-%d %H:%M")

    categories = []
    total_deep = 0
    total_watch = 0

    if ts_match:
        run_dirname = f"{ts_match.group(1)}_{ts_match.group(2).replace(':', '-')}"
        run_dir = f"history/{run_dirname}"
        for json_file in sorted(glob.glob(f"{run_dir}/*.json")):
            archive = load_category_archive(json_file)
            cat_data = archive_to_category_data(archive, run_dirname)
            categories.append(cat_data)
            total_deep += cat_data["deep_count"]
            total_watch += cat_data["watch_count"]

    site_data = {
        "meta": {
            "timestamp": ts_display,
            "generated": now.strftime("%Y-%m-%d %H:%M UTC"),
            "deep_count": total_deep,
            "watch_count": total_watch,
            "cat_count": len(categories)
        },
        "categories": categories
    }

    os.makedirs("data", exist_ok=True)
    with open("data/site_data.json", "w", encoding="utf-8") as f:
        json.dump(site_data, f, ensure_ascii=False, indent=2)

    print(f"site_data.json: {total_deep} deep, {total_watch} watch, {len(categories)} categories")


if __name__ == "__main__":
    for run_dir in sorted(glob.glob("history/????-??-??_*/")):
        dirname = os.path.basename(run_dir.rstrip("/"))
        date_str = dirname[:10]
        build_day_json(date_str)

    build_history_index()
    build_site()
    print("Site built successfully.")
