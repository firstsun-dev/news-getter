import sqlite3
import json
import hashlib
import datetime
import re

DB_PATH = "data/news.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
  fingerprint    TEXT PRIMARY KEY,
  title          TEXT NOT NULL,
  canonical_url  TEXT NOT NULL,
  category       TEXT NOT NULL,
  first_seen_at  TEXT NOT NULL,
  last_seen_at   TEXT NOT NULL,
  seen_count     INTEGER NOT NULL DEFAULT 1,
  sources_json   TEXT NOT NULL
)
"""


def _normalize_title(title):
    return re.sub(r"\s+", " ", title.strip().lower())


def _fingerprint(article):
    """sha256(canonical_url 或 normalize(title)) — prefer canonical_url first."""
    canonical_url = article.get("link") or ""
    if canonical_url:
        basis = canonical_url
    else:
        title = article.get("title") or ""
        basis = _normalize_title(title) if title else ""
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def _connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def upsert_story(article, db_path=DB_PATH):
    conn = _connect(db_path)
    try:
        fingerprint = _fingerprint(article)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        source_entry = {
            "name": article["source"],
            "tier": article["tier"],
            "role": article["role"],
        }

        row = conn.execute(
            "SELECT sources_json, seen_count FROM stories WHERE fingerprint = ?",
            (fingerprint,),
        ).fetchone()

        if row is None:
            sources = [source_entry]
            conn.execute(
                """INSERT INTO stories
                   (fingerprint, title, canonical_url, category,
                    first_seen_at, last_seen_at, seen_count, sources_json)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    fingerprint,
                    article["title"],
                    article.get("link", ""),
                    article["category"],
                    now,
                    now,
                    json.dumps(sources, ensure_ascii=False),
                ),
            )
            seen_count = 1
        else:
            sources_json, seen_count = row
            sources = json.loads(sources_json)
            if not any(s["name"] == source_entry["name"] for s in sources):
                sources.append(source_entry)
            seen_count += 1
            conn.execute(
                """UPDATE stories
                   SET last_seen_at = ?, seen_count = ?, sources_json = ?
                   WHERE fingerprint = ?""",
                (now, seen_count, json.dumps(sources, ensure_ascii=False), fingerprint),
            )

        conn.commit()
        return {
            "fingerprint": fingerprint,
            "title": article["title"],
            "canonical_url": article.get("link", ""),
            "category": article["category"],
            "seen_count": seen_count,
            "sources": sources,
        }
    finally:
        conn.close()


def stories_since(since_iso, db_path=DB_PATH):
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            """SELECT fingerprint, title, canonical_url, category,
                      first_seen_at, last_seen_at, seen_count, sources_json
               FROM stories WHERE last_seen_at >= ?
               ORDER BY last_seen_at DESC""",
            (since_iso,),
        ).fetchall()
        return [
            {
                "fingerprint": r[0],
                "title": r[1],
                "canonical_url": r[2],
                "category": r[3],
                "first_seen_at": r[4],
                "last_seen_at": r[5],
                "seen_count": r[6],
                "sources": json.loads(r[7]),
            }
            for r in rows
        ]
    finally:
        conn.close()
