import datetime
import unittest
from unittest import mock

from src import fetch


class FakeEntry:
    def __init__(self, title, link, summary, published):
        self.title = title
        self.link = link
        self.summary = summary
        self.published_parsed = published.timetuple()


class TestFetch(unittest.TestCase):
    def test_articles_carry_tier_and_role_from_feeds_yaml(self):
        fake_config = {
            "feeds": [
                {"name": "Test Feed", "url": "http://example.com/rss", "category": "AI", "tier": 1, "role": "primary"},
                {"name": "Test Feed 2", "url": "http://example.com/rss2", "category": "Technology", "tier": 4, "role": "aggregator"},
            ]
        }
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = FakeEntry("Title A", "http://example.com/a", "Summary A", now)

        fake_parsed = mock.Mock()
        fake_parsed.entries = [entry]

        with mock.patch("src.fetch.yaml.safe_load", return_value=fake_config), \
             mock.patch("src.fetch.requests.get", return_value=mock.Mock(content=b"<xml/>")), \
             mock.patch("src.fetch.feedparser.parse", return_value=fake_parsed):
            articles = fetch.fetch_feeds()

        # one entry per feed since feedparser.parse is mocked identically for both
        self.assertEqual(len(articles), 2)

        by_source = {a["source"]: a for a in articles}
        self.assertEqual(by_source["Test Feed"]["tier"], 1)
        self.assertEqual(by_source["Test Feed"]["role"], "primary")
        self.assertEqual(by_source["Test Feed"]["category"], "AI")
        self.assertEqual(by_source["Test Feed 2"]["tier"], 4)
        self.assertEqual(by_source["Test Feed 2"]["role"], "aggregator")

    def test_relative_link_resolved_against_feed_url(self):
        fake_config = {
            "feeds": [
                {"name": "Test Feed", "url": "https://example.com/rss", "category": "AI", "tier": 1, "role": "primary"},
            ]
        }
        now = datetime.datetime.now(datetime.timezone.utc)
        entry = FakeEntry("Relative Link Title", "/2026/07/some-article", "Summary", now)

        fake_parsed = mock.Mock()
        fake_parsed.entries = [entry]

        with mock.patch("src.fetch.yaml.safe_load", return_value=fake_config), \
             mock.patch("src.fetch.requests.get", return_value=mock.Mock(content=b"<xml/>")), \
             mock.patch("src.fetch.feedparser.parse", return_value=fake_parsed):
            articles = fetch.fetch_feeds()

        self.assertEqual(articles[0]["link"], "https://example.com/2026/07/some-article")


if __name__ == "__main__":
    unittest.main()
