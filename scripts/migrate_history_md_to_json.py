#!/usr/bin/env python3
"""One-shot migration: history/<ts>/<Cat>.md → history/<ts>/<Cat>.json

Historical md files contain free-form Gemini prose (NOT the render_story_block
template format). This script heuristically splits each md into structured
stories and writes a CategoryArchive JSON alongside the md.

Usage:
    python3 scripts/migrate_history_md_to_json.py          # write json only
    python3 scripts/migrate_history_md_to_json.py --delete  # write json, then delete md
"""
import argparse
import glob
import json
import os
import re
import sys

HEADING_RE = re.compile(r'^(#{2,4})\s+(.+)$')
BOLD_NUM_TITLE_RE = re.compile(r'^\*\*(\d+[.、]\s*.+)\*\*$')
WATCHLIST_ITEM_RE = re.compile(
    r'^[-*]\s+\[(.*?)\]\((https?://[^)]+)\)\s*\(tier\s+(\d+),\s*seen_count=(\d+)\)'
)
LINK_RE = re.compile(r'\[([^\]]*)\]\((https?://[^)]+)\)')
NUM_PREFIX_RE = re.compile(
    r'^(\d+[.、]\s*|[一二三四五六七八九十百]+[、.：:]\s*|專題[一二三四五六七八九十百]+[：:]\s*)'
)

FILE_HEADER_RE = re.compile(r'^#\s+.+深度專報.*$')


def clean_title(raw: str) -> str:
    t = raw.strip()
    t = t.strip('*').strip()
    t = NUM_PREFIX_RE.sub('', t).strip()
    t = t.strip('*').strip()
    return t


def extract_urls(body: str, limit: int = 3) -> list[str]:
    seen = []
    for _label, url in LINK_RE.findall(body):
        if url not in seen:
            seen.append(url)
        if len(seen) >= limit:
            break
    return seen


def strip_file_header(text: str) -> tuple[str, str]:
    """Remove the first '# Cat 深度專報 (ts)' line. Returns (body, timestamp)."""
    lines = text.split('\n')
    ts = ''
    if lines and FILE_HEADER_RE.match(lines[0].strip()):
        m = re.search(r'\((\d{4}-\d{2}-\d{2})[_ ](\d{2}[-:]\d{2})\)', lines[0])
        if m:
            ts = f"{m.group(1)}_{m.group(2).replace(':', '-')}"
        lines = lines[1:]
    while lines and lines[0].strip() == '':
        lines = lines[1:]
    return '\n'.join(lines), ts


def extract_watchlist(lines: list[str]) -> tuple[list, list[str]]:
    """Pull out the '#### 觀察中' block. Returns (watchlist_items, remaining_lines)."""
    watchlist = []
    out = []
    i = 0
    in_wl = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith('#### ') and '觀察中' in stripped:
            in_wl = True
            i += 1
            continue
        if in_wl:
            m = WATCHLIST_ITEM_RE.match(stripped)
            if m:
                watchlist.append({
                    'title': m.group(1),
                    'url': m.group(2),
                    'tier': int(m.group(3)),
                    'seen_count': int(m.group(4)),
                })
                i += 1
                continue
            if stripped == '' or stripped.startswith('-') or stripped.startswith('*'):
                i += 1
                continue
            if stripped.startswith('##') or stripped.startswith('###') or stripped.startswith('####'):
                in_wl = False
                out.append(line)
                i += 1
                continue
            i += 1
            continue
        out.append(line)
        i += 1
    return watchlist, out


def split_into_stories(body: str) -> list[dict]:
    """Heuristically split free-form markdown into story records."""
    lines = body.split('\n')

    no_signal = any('本次無達標深度分析' in l for l in lines if l.strip().startswith('>'))
    if no_signal:
        return [], True

    chunks = []
    current_title = None
    current_body = []

    def flush():
        nonlocal current_title, current_body
        body_text = '\n'.join(current_body).strip()
        if current_title and body_text and len(body_text) >= 20:
            chunks.append({
                'title': current_title,
                'body_md': body_text,
                'used_source_urls': extract_urls(body_text),
            })
        current_title = None
        current_body = []

    for line in lines:
        stripped = line.strip()

        m = HEADING_RE.match(stripped)
        if m:
            flush()
            current_title = clean_title(m.group(2))
            continue

        m2 = BOLD_NUM_TITLE_RE.match(stripped)
        if m2:
            flush()
            current_title = clean_title(m2.group(1))
            continue

        if current_title is not None:
            current_body.append(line)
        else:
            current_body.append(line)

    flush()

    if not chunks:
        whole = body.strip()
        if whole and len(whole) >= 20:
            chunks.append({
                'title': '(綜述)',
                'body_md': whole,
                'used_source_urls': extract_urls(whole),
            })

    return chunks, False


def migrate_file(md_path: str) -> dict | None:
    with open(md_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    body, ts_from_header = strip_file_header(raw)
    body_lines = body.split('\n')

    watchlist, body_lines = extract_watchlist(body_lines)
    body_clean = '\n'.join(body_lines)

    stories, no_signal = split_into_stories(body_clean)

    dirname = os.path.basename(os.path.dirname(md_path))
    cat_name = os.path.basename(md_path).replace('.md', '').replace('_', ' ')

    if ts_from_header:
        timestamp = ts_from_header
    else:
        timestamp = dirname

    archive = {
        'category': cat_name,
        'timestamp': timestamp,
        'stories': stories,
        'watchlist': watchlist,
        'no_signal': no_signal,
    }
    return archive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--delete', action='store_true', help='delete md files after writing json')
    args = ap.parse_args()

    md_files = sorted(glob.glob('history/*/*.md'))
    if not md_files:
        print('No md files found under history/')
        return

    total = len(md_files)
    written = 0
    errors = 0
    total_stories = 0
    total_watch = 0
    no_signal_count = 0

    for md_path in md_files:
        try:
            archive = migrate_file(md_path)
            if archive is None:
                errors += 1
                continue
            json_path = md_path.replace('.md', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(archive, f, ensure_ascii=False, indent=2)
            written += 1
            total_stories += len(archive['stories'])
            total_watch += len(archive['watchlist'])
            if archive['no_signal']:
                no_signal_count += 1
            if args.delete:
                os.remove(md_path)
        except Exception as e:
            print(f'ERROR {md_path}: {e}', file=sys.stderr)
            errors += 1

    print(f'Migrated {written}/{total} files ({errors} errors)')
    print(f'Total stories: {total_stories}, watchlist items: {total_watch}, no_signal: {no_signal_count}')
    if args.delete:
        print('md files deleted')


if __name__ == '__main__':
    main()