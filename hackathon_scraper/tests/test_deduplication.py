"""
Unit tests for Deduplication & Record Merging.
"""

import unittest
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.pipelines.deduplicate import deduplicate_records


class TestDeduplication(unittest.TestCase):

    def test_deduplicate_identical_records(self):
        rec1 = Hackathon(
            id="same-fingerprint-id",
            title="National AI Challenge 2026",
            event_url="https://devfolio.co/ai-challenge",
            source_site="devfolio",
            source_url="https://devfolio.co/ai-challenge",
            raw_data_hash="hash1",
        )
        rec2 = Hackathon(
            id="same-fingerprint-id",
            title="National AI Challenge 2026",
            event_url="https://unstop.com/ai-challenge",
            source_site="unstop",
            source_url="https://unstop.com/ai-challenge",
            raw_data_hash="hash2",
        )

        dedup, count = deduplicate_records([rec1, rec2])
        self.assertEqual(len(dedup), 1)
        self.assertEqual(count, 1)
        self.assertIn("devfolio", dedup[0].source_sites)
        self.assertIn("unstop", dedup[0].source_sites)


if __name__ == "__main__":
    unittest.main()
