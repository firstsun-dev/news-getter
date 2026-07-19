#!/usr/bin/env python3
"""Validate all history/*/*.json against CategoryArchive schema and report issues."""
import glob
import json
import sys
from collections import Counter

errors = []
warnings = []
stats = Counter()

for path in sorted(glob.glob('history/*/*.json')):
    try:
        d = json.load(open(path, encoding='utf-8'))
    except Exception as e:
        errors.append(f'{path}: JSON parse error: {e}')
        continue

    if 'category' not in d:
        errors.append(f'{path}: missing "category"')
        continue
    if 'timestamp' not in d:
        errors.append(f'{path}: missing "timestamp"')
        continue
    if 'stories' not in d:
        errors.append(f'{path}: missing "stories"')
        continue
    if 'watchlist' not in d:
        errors.append(f'{path}: missing "watchlist"')
        continue
    if 'no_signal' not in d:
        errors.append(f'{path}: missing "no_signal"')
        continue

    stats['files'] += 1
    stats['total_stories'] += len(d['stories'])
    stats['total_watch'] += len(d['watchlist'])
    if d['no_signal']:
        stats['no_signal'] += 1

    for i, s in enumerate(d['stories']):
        if 'title' not in s or not s['title']:
            errors.append(f'{path}: story[{i}] missing/empty title')
            continue
        has_structured = bool(s.get('fact_summary') or s.get('judgment'))
        has_body = bool(s.get('body_md'))
        if not has_structured and not has_body:
            errors.append(f'{path}: story[{i}] "{s["title"][:30]}" has neither structured fields nor body_md')
        elif has_structured and not has_body:
            stats['structured_stories'] += 1
        elif has_body and not has_structured:
            stats['migrated_stories'] += 1
        elif has_body and has_structured:
            warnings.append(f'{path}: story[{i}] has both structured and body_md (unexpected)')

        urls = s.get('used_source_urls', [])
        if not isinstance(urls, list):
            errors.append(f'{path}: story[{i}] used_source_urls not a list')

    for i, w in enumerate(d['watchlist']):
        for fld in ('title', 'url', 'tier', 'seen_count'):
            if fld not in w:
                errors.append(f'{path}: watchlist[{i}] missing "{fld}"')

print('=== 統計 ===')
for k, v in sorted(stats.items()):
    print(f'  {k}: {v}')
print()
if warnings:
    print(f'=== 警告 ({len(warnings)}) ===')
    for w in warnings[:10]:
        print(f'  {w}')
    if len(warnings) > 10:
        print(f'  ... 還有 {len(warnings)-10} 條')
print()
if errors:
    print(f'=== 錯誤 ({len(errors)}) ===')
    for e in errors[:20]:
        print(f'  {e}')
    if len(errors) > 20:
        print(f'  ... 還有 {len(errors)-20} 條')
    sys.exit(1)
else:
    print('=== 全部通過，0 錯誤 ===')