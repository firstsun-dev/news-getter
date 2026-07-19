import json
import unittest

from src.summarizer import parse_digest, StoryRecord, CategoryArchive

ALLOWED = {"https://example.com/a", "https://example.com/b"}

VALID = {
    "fact_summary": "這是一段長度足夠的事實摘要內容，描述輸入文章裡出現的具體事件細節。",
    "judgment": "這是一段長度足夠的產業判斷內容，說明此事件對產業可能造成的影響與後續觀察重點。",
    "used_source_urls": ["https://example.com/a"],
}


class TestSummarizerSchema(unittest.TestCase):
    def test_valid_digest_passes(self):
        digest, reason = parse_digest(json.dumps(VALID), ALLOWED)
        self.assertIsNone(reason)
        self.assertIsNotNone(digest)
        self.assertEqual(str(digest.used_source_urls[0]), "https://example.com/a")

    def test_url_outside_input_set_rejected(self):
        bad = dict(VALID, used_source_urls=["https://evil.example.com/fake"])
        digest, reason = parse_digest(json.dumps(bad), ALLOWED)
        self.assertIsNone(digest)
        self.assertIn("not subset", reason)

    def test_placeholder_text_rejected(self):
        bad = dict(VALID, fact_summary=VALID["fact_summary"] + " 待補充")
        digest, reason = parse_digest(json.dumps(bad), ALLOWED)
        self.assertIsNone(digest)
        self.assertEqual(reason, "placeholder text detected")

    def test_fact_summary_too_short_rejected(self):
        bad = dict(VALID, fact_summary="太短")
        digest, reason = parse_digest(json.dumps(bad), ALLOWED)
        self.assertIsNone(digest)
        self.assertIn("schema validation failed", reason)

    def test_judgment_too_long_rejected(self):
        bad = dict(VALID, judgment="長" * 601)
        digest, reason = parse_digest(json.dumps(bad), ALLOWED)
        self.assertIsNone(digest)
        self.assertIn("schema validation failed", reason)

    def test_invalid_json_rejected(self):
        digest, reason = parse_digest("not json", ALLOWED)
        self.assertIsNone(digest)
        self.assertIn("invalid JSON", reason)


class TestStoryRecordAndArchive(unittest.TestCase):
    def test_story_record_body_md_optional(self):
        r = StoryRecord(title="T", body_md="some markdown prose")
        self.assertEqual(r.title, "T")
        self.assertEqual(r.body_md, "some markdown prose")
        self.assertEqual(r.fact_summary, "")
        self.assertEqual(r.judgment, "")

    def test_story_record_structured_fields(self):
        r = StoryRecord(
            title="T", confidence=80, heat=70,
            fact_summary="x" * 25, judgment="y" * 25,
            used_source_urls=["https://e.com/a"],
        )
        self.assertEqual(r.confidence, 80)
        self.assertEqual(r.used_source_urls, ["https://e.com/a"])

    def test_category_archive_minimal(self):
        a = CategoryArchive(category="AI", timestamp="2026-07-18_20-59")
        self.assertEqual(a.category, "AI")
        self.assertEqual(a.stories, [])
        self.assertEqual(a.watchlist, [])
        self.assertFalse(a.no_signal)

    def test_category_archive_with_stories(self):
        a = CategoryArchive(
            category="AI", timestamp="2026-07-18_20-59",
            stories=[StoryRecord(title="S", fact_summary="f", judgment="j")],
            watchlist=[],
            no_signal=False,
        )
        self.assertEqual(len(a.stories), 1)
        self.assertEqual(a.stories[0].title, "S")


if __name__ == "__main__":
    unittest.main()
