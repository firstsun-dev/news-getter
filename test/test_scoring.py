import unittest

from src.scoring import score_story


class TestScoring(unittest.TestCase):
    def test_tier1_multi_source_beats_tier4_single_source(self):
        tier1_multi = score_story(tiers=[1], seen_count=1, distinct_sources=2)
        tier4_single = score_story(tiers=[4], seen_count=1, distinct_sources=1)
        self.assertGreater(tier1_multi["confidence"], tier4_single["confidence"])

    def test_heat_increases_with_seen_count_until_cap(self):
        heat_1 = score_story(tiers=[2], seen_count=1, distinct_sources=1)["heat"]
        heat_3 = score_story(tiers=[2], seen_count=3, distinct_sources=1)["heat"]
        heat_6 = score_story(tiers=[2], seen_count=6, distinct_sources=1)["heat"]
        heat_10 = score_story(tiers=[2], seen_count=10, distinct_sources=1)["heat"]

        self.assertLess(heat_1, heat_3)
        self.assertLess(heat_3, heat_6)
        self.assertEqual(heat_6, heat_10)  # capped at seen_count=6


if __name__ == "__main__":
    unittest.main()
