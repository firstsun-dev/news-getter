import unittest
import json
import os
import glob
import shutil
import tempfile

from src import build_site


class TestParseCategoryContent(unittest.TestCase):
    def test_no_signal_marker_is_detected(self):
        raw = "> 本次無達標深度分析\n"
        out = build_site.parse_category_content(raw)
        self.assertTrue(out["no_signal"])
        self.assertEqual(out["stories"], [])
        self.assertEqual(out["watchlist"], [])

    def test_watchlist_items_are_parsed(self):
        raw = (
            "#### 觀察中\n"
            "- [Title A](https://a.example/x) (tier 2, seen_count=3)\n"
            "- [Title B](https://b.example/y) (tier 1, seen_count=5)\n"
        )
        out = build_site.parse_category_content(raw)
        self.assertEqual(len(out["watchlist"]), 2)
        self.assertEqual(out["watchlist"][0]["title"], "Title A")
        self.assertEqual(out["watchlist"][0]["tier"], 2)
        self.assertEqual(out["watchlist"][1]["seen_count"], 5)

    def test_story_with_fact_and_judgment_blocks(self):
        raw = (
            "#### Story One\n"
            'confidence: 72 <span class="score-badge heat" data-h="65">65</span>\n'
            '<div class="fact-block">\nfact line\n</div>\n'
            '<div class="judgment-block">\njudgment line\n</div>\n'
        )
        out = build_site.parse_category_content(raw)
        self.assertEqual(len(out["stories"]), 1)
        s = out["stories"][0]
        self.assertEqual(s["title"], "Story One")
        self.assertEqual(s["confidence"], 72)
        self.assertEqual(s["heat"], 65)
        self.assertIn("fact-block", s["fact_html"])
        self.assertIn("judgment-block", s["judgment_html"])


class TestBuildDayJsonNoHtml(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ng-test-")
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        os.makedirs("history/2026-07-18_10-53", exist_ok=True)
        with open("history/2026-07-18_10-53/AI.md", "w", encoding="utf-8") as f:
            f.write("# AI\n\n#### Story\nconfidence: 70\n")

    def tearDown(self):
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_build_day_json_emits_json_only_no_index_html(self):
        build_site.build_day_json("2026-07-18")
        self.assertTrue(os.path.exists("data/2026/07/2026-07-18.json"))
        with open("data/2026/07/2026-07-18.json", encoding="utf-8") as f:
            day = json.load(f)
        self.assertEqual(day["date"], "2026-07-18")
        self.assertEqual(len(day["runs"]), 1)
        self.assertEqual(day["runs"][0]["categories"][0]["name"], "AI")
        # No HTML template copied into the run dir
        self.assertFalse(os.path.exists("history/2026-07-18_10-53/index.html"))


class TestBuildSiteEmitsNoHtml(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ng-test-")
        self.cwd = os.getcwd()
        os.chdir(self.tmp)
        os.makedirs("data", exist_ok=True)
        with open("summary.md", "w", encoding="utf-8") as f:
            f.write("# Brief (2026-07-18 10-53)\n\n## AI\n\n#### S\nconfidence: 70\n")

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
        # No HTML/RSS artifacts at repo root
        self.assertFalse(os.path.exists("index.html"))
        self.assertFalse(os.path.exists("rss.xml"))


class TestBuildRssRemoved(unittest.TestCase):
    def test_build_rss_is_not_exported(self):
        self.assertFalse(hasattr(build_site, "build_rss"))


if __name__ == "__main__":
    unittest.main()