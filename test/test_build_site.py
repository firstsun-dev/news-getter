import unittest
import json
import os
import glob
import shutil
import tempfile

from src import build_site


class TestArchiveToCategoryData(unittest.TestCase):
    def test_structured_story_renders_fact_and_judgment(self):
        archive = {
            "category": "AI",
            "timestamp": "2026-07-18_20-59",
            "stories": [
                {
                    "title": "Story One",
                    "confidence": 72,
                    "heat": 65,
                    "fact_summary": "這是事實摘要內容。",
                    "judgment": "這是判斷內容。",
                    "used_source_urls": ["https://example.com/a"],
                }
            ],
            "watchlist": [],
            "no_signal": False,
        }
        out = build_site.archive_to_category_data(archive, "2026-07-18_20-59")
        self.assertEqual(out["name"], "AI")
        self.assertEqual(out["anchor"], "AI")
        self.assertEqual(out["archive_url"], "./history/2026-07-18_20-59/index.html#AI")
        self.assertEqual(len(out["stories"]), 1)
        s = out["stories"][0]
        self.assertEqual(s["title"], "Story One")
        self.assertEqual(s["confidence"], 72)
        self.assertEqual(s["heat"], 65)
        self.assertIn("fact-block", s["fact_html"])
        self.assertIn("judgment-block", s["judgment_html"])

    def test_body_md_story_renders_as_judgment_html(self):
        archive = {
            "category": "Tech",
            "timestamp": "2026-05-05_13-47",
            "stories": [
                {
                    "title": "Historical Story",
                    "body_md": "### Title\n\nSome prose paragraph.\n\n[link](https://x.com)",
                }
            ],
            "watchlist": [],
            "no_signal": False,
        }
        out = build_site.archive_to_category_data(archive, "2026-05-05_13-47")
        s = out["stories"][0]
        self.assertEqual(s["fact_html"], "")
        self.assertIn("Some prose paragraph", s["judgment_html"])

    def test_watchlist_items_pass_through(self):
        archive = {
            "category": "Finance",
            "timestamp": "2026-07-18_20-59",
            "stories": [],
            "watchlist": [
                {"title": "WL A", "url": "https://a.example/x", "tier": 2, "seen_count": 3},
                {"title": "WL B", "url": "https://b.example/y", "tier": 1, "seen_count": 5},
            ],
            "no_signal": True,
        }
        out = build_site.archive_to_category_data(archive, "2026-07-18_20-59")
        self.assertTrue(out["no_signal"])
        self.assertEqual(len(out["watchlist"]), 2)
        self.assertEqual(out["watchlist"][0]["tier"], 2)
        self.assertEqual(out["watchlist"][1]["seen_count"], 5)
        self.assertEqual(out["deep_count"], 0)
        self.assertEqual(out["watch_count"], 2)


class TestBuildDayJsonFromArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ng-test-")
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        run_dir = "history/2026-07-18_10-53"
        os.makedirs(run_dir, exist_ok=True)
        for cat in ["AI", "Finance", "Global", "Strategy", "Tech"]:
            archive = {
                "category": cat,
                "timestamp": "2026-07-18_10-53",
                "stories": [
                    {
                        "title": f"S-{cat}",
                        "confidence": 70,
                        "heat": 60,
                        "fact_summary": "fact text here long enough.",
                        "judgment": "judgment text here long enough.",
                        "used_source_urls": [],
                    }
                ],
                "watchlist": [],
                "no_signal": False,
            }
            with open(f"{run_dir}/{cat}.json", "w", encoding="utf-8") as f:
                json.dump(archive, f)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_day_json_reads_archive_json(self):
        build_site.build_day_json("2026-07-18")
        self.assertTrue(os.path.exists("data/2026/07/2026-07-18.json"))
        with open("data/2026/07/2026-07-18.json", encoding="utf-8") as f:
            day = json.load(f)
        self.assertEqual(day["date"], "2026-07-18")
        self.assertEqual(len(day["runs"]), 1)
        cat_names = [c["name"] for c in day["runs"][0]["categories"]]
        self.assertIn("AI", cat_names)
        ai_cat = day["runs"][0]["categories"][0]
        self.assertEqual(ai_cat["stories"][0]["title"], "S-AI")

    def test_build_day_json_skips_partial_run(self):
        partial = "history/2026-07-18_22-00"
        os.makedirs(partial, exist_ok=True)
        with open(f"{partial}/OnlyOne.json", "w", encoding="utf-8") as f:
            json.dump({"category": "OnlyOne", "timestamp": "2026-07-18_22-00",
                        "stories": [], "watchlist": [], "no_signal": True}, f)
        build_site.build_day_json("2026-07-18")
        with open("data/2026/07/2026-07-18.json", encoding="utf-8") as f:
            day = json.load(f)
        times = [r["time"] for r in day["runs"]]
        self.assertIn("10:53", times)
        self.assertNotIn("22:00", times)


class TestBuildSiteFromArchive(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ng-test-")
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        os.makedirs("data", exist_ok=True)
        os.makedirs("history/2026-07-18_10-53", exist_ok=True)
        with open("summary.md", "w", encoding="utf-8") as f:
            f.write("# Brief (2026-07-18 10-53)\n\n## AI\n\n#### S\nconfidence: 70\n")
        archive = {
            "category": "AI",
            "timestamp": "2026-07-18_10-53",
            "stories": [
                {
                    "title": "S",
                    "confidence": 70,
                    "heat": 60,
                    "fact_summary": "fact text here long enough.",
                    "judgment": "judgment text here long enough.",
                    "used_source_urls": [],
                }
            ],
            "watchlist": [],
            "no_signal": False,
        }
        with open("history/2026-07-18_10-53/AI.json", "w", encoding="utf-8") as f:
            json.dump(archive, f)

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_site_writes_only_json(self):
        build_site.build_site()
        self.assertTrue(os.path.exists("data/site_data.json"))
        with open("data/site_data.json", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("meta", data)
        self.assertIn("categories", data)
        self.assertEqual(data["categories"][0]["name"], "AI")
        self.assertEqual(data["categories"][0]["stories"][0]["title"], "S")
        self.assertFalse(os.path.exists("index.html"))
        self.assertFalse(os.path.exists("rss.xml"))


class TestBuildRssRemoved(unittest.TestCase):
    def test_build_rss_is_not_exported(self):
        self.assertFalse(hasattr(build_site, "build_rss"))


class TestParseCategoryContentRemoved(unittest.TestCase):
    def test_parse_category_content_is_not_exported(self):
        self.assertFalse(hasattr(build_site, "parse_category_content"))


if __name__ == "__main__":
    unittest.main()