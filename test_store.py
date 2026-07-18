import json
import os
import tempfile
import unittest

import store


class TestStore(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.remove(self.db_path)  # let store create it fresh

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_same_url_upserted_twice_increments_seen_count_without_duplicating_source(self):
        article = {
            "source": "Feed A",
            "category": "AI",
            "tier": 1,
            "role": "primary",
            "title": "Same Story",
            "link": "https://example.com/story",
            "content": "content",
        }
        first = store.upsert_story(article, db_path=self.db_path)
        second = store.upsert_story(article, db_path=self.db_path)

        self.assertEqual(first["seen_count"], 1)
        self.assertEqual(second["seen_count"], 2)
        self.assertEqual(len(second["sources"]), 1)

    def test_same_title_different_feed_accumulates_distinct_sources(self):
        article_a = {
            "source": "Feed A",
            "category": "AI",
            "tier": 1,
            "role": "primary",
            "title": "Breaking News Story",
            "link": "https://example.com/a",
            "content": "content a",
        }
        article_b = {
            "source": "Feed B",
            "category": "AI",
            "tier": 2,
            "role": "professional",
            "title": "Breaking News Story",
            "link": "https://example.org/b",
            "content": "content b",
        }
        store.upsert_story(article_a, db_path=self.db_path)
        result = store.upsert_story(article_b, db_path=self.db_path)

        self.assertEqual(result["seen_count"], 2)
        source_names = {s["name"] for s in result["sources"]}
        self.assertEqual(source_names, {"Feed A", "Feed B"})


if __name__ == "__main__":
    unittest.main()
