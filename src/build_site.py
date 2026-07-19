import json
import re
import datetime
import os
import glob


def md_to_html_util(md_text):
    import markdown
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code', 'toc', 'sane_lists'])


def parse_category_content(raw_content):
    stories = []
    watchlist = []
    no_signal = False

    lines = raw_content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if line.startswith(">") and "本次無達標深度分析" in line:
            no_signal = True
            i += 1
            continue

        if line.startswith("#### ") and "觀察中" in line:
            i += 1
            while i < len(lines):
                wl_line = lines[i].strip()
                if wl_line.startswith("- [") or wl_line.startswith("* ["):
                    m = re.match(r'[-*]\s+\[(.*?)\]\((.*?)\)\s*\(tier\s+(\d+),\s*seen_count=(\d+)\)', wl_line)
                    if m:
                        watchlist.append({
                            "title": m.group(1),
                            "url": m.group(2),
                            "tier": int(m.group(3)),
                            "seen_count": int(m.group(4))
                        })
                    i += 1
                elif wl_line == "":
                    i += 1
                    continue
                elif wl_line.startswith("[查看") or wl_line.startswith("##") or wl_line.startswith("###"):
                    break
                else:
                    i += 1
            continue

        if line.startswith("#### ") or line.startswith("### ### "):
            if line.startswith("### ### "):
                title = line[8:].strip()
            else:
                title = line[5:].strip()
            confidence = None
            heat = None
            fact_html = ""
            judgment_html = ""

            i += 1
            while i < len(lines):
                inner = lines[i].strip()
                if inner.startswith("#### ") or inner.startswith("## ") or inner.startswith("### ") or inner.startswith("[查看"):
                    break

                conf_match = re.search(r'confidence:\s*(\d+)', inner)
                if conf_match:
                    confidence = int(conf_match.group(1))

                heat_match = re.search(r'<span[^>]*class="score-badge heat"[^>]*>(\d+)</span>', inner)
                if heat_match:
                    heat = int(heat_match.group(1))

                if '<div class="fact-block">' in inner:
                    fact_parts = [inner]
                    while i + 1 < len(lines):
                        i += 1
                        fact_parts.append(lines[i])
                        if '</div>' in lines[i]:
                            break
                    fact_html = md_to_html_util("".join(fact_parts))

                elif '<div class="judgment-block">' in inner:
                    judgment_parts = [inner]
                    while i + 1 < len(lines):
                        i += 1
                        judgment_parts.append(lines[i])
                        if '</div>' in lines[i]:
                            break
                    judgment_html = md_to_html_util("".join(judgment_parts))

                i += 1

            stories.append({
                "title": title,
                "confidence": confidence,
                "heat": heat,
                "fact_html": fact_html,
                "judgment_html": judgment_html
            })
            continue

        i += 1

    return {"stories": stories, "watchlist": watchlist, "no_signal": no_signal}


def build_day_json(date_str):
    year, month, day = date_str.split("-")
    day_data = {"date": date_str, "runs": []}

    for run_dir in sorted(glob.glob(f"history/{date_str}_*/")):
        dirname = os.path.basename(run_dir.rstrip("/"))
        m = re.match(r'^\d{4}-\d{2}-\d{2}_(\d{2}-\d{2})$', dirname)
        if not m:
            continue

        time_str = m.group(1).replace("-", ":")
        md_files = sorted(glob.glob(f"{run_dir}/*.md"))

        categories = []
        for md_file in md_files:
            cat_name = os.path.basename(md_file).replace(".md", "").replace("_", " ")
            with open(md_file, "r", encoding="utf-8") as f:
                raw = f.read()
            body = "\n".join(raw.split("\n")[2:])
            parsed = parse_category_content(body)
            anchor = cat_name.replace(" ", "-").replace("/", "-")
            categories.append({
                "name": cat_name,
                "anchor": anchor,
                "stories": parsed["stories"],
                "watchlist": parsed["watchlist"],
                "no_signal": parsed["no_signal"],
                "deep_count": len(parsed["stories"]),
                "watch_count": len(parsed["watchlist"])
            })

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
        lines = f.readlines()

    title_line = ""
    categories_raw = {}
    current_cat = None

    for line in lines:
        if line.startswith("# "):
            title_line = line.strip("# \n")
        elif line.startswith("## ") or line.startswith("### "):
            header_text = line.lstrip("# ").strip()
            if "完整情報存檔" in header_text or "Deep Analysis" in header_text or "快速索引" in header_text:
                current_cat = None
                continue
            current_cat = header_text.replace("\U0001f50d", "").strip()
            categories_raw[current_cat] = {"content": "", "md_path": ""}
        elif current_cat and ("獨立深度存檔頁面" in line or "獨立存檔頁面" in line) and "(" in line and ")" in line:
            path_part = line.split("(")[-1].split(")")[0]
            dirname = os.path.dirname(path_part)
            cat_file = os.path.basename(path_part).replace(".md", "")
            cat_name = cat_file.replace("_", " ")
            categories_raw[current_cat]["md_path"] = f"./{dirname}/index.html#{cat_name.replace(' ', '-')}"
        elif current_cat:
            categories_raw[current_cat]["content"] += line

    ts_match = re.search(r'\((\d{4}-\d{2}-\d{2})[_ ](\d{2}[-:]\d{2})\)', title_line)
    ts_display = ts_match.group(0).strip("()") if ts_match else now.strftime("%Y-%m-%d %H:%M")

    if ts_match:
        run_dirname = f"{ts_match.group(1)}_{ts_match.group(2).replace(':', '-')}"
        run_dir = f"history/{run_dirname}"
        if os.path.exists(run_dir):
            for md_file in sorted(glob.glob(f"{run_dir}/*.md")):
                cat_name = os.path.basename(md_file).replace(".md", "").replace("_", " ")
                if cat_name not in categories_raw:
                    with open(md_file, "r", encoding="utf-8") as f:
                        raw = f.read()
                    body = "\n".join(raw.split("\n")[2:])
                    anchor = cat_name.replace(" ", "-").replace("/", "-")
                    categories_raw[cat_name] = {
                        "content": body,
                        "md_path": f"./{run_dir}/index.html#{anchor}"
                    }

    categories = []
    total_deep = 0
    total_watch = 0

    for cat_name, data in categories_raw.items():
        parsed = parse_category_content(data["content"])
        anchor = cat_name.replace(" ", "-").replace("/", "-")
        categories.append({
            "name": cat_name,
            "anchor": anchor,
            "archive_url": data["md_path"] if data["md_path"] else None,
            "stories": parsed["stories"],
            "watchlist": parsed["watchlist"],
            "no_signal": parsed["no_signal"],
            "deep_count": len(parsed["stories"]),
            "watch_count": len(parsed["watchlist"])
        })
        total_deep += len(parsed["stories"])
        total_watch += len(parsed["watchlist"])

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
