"""
Unit tests for Normalization Pipeline.
"""

import unittest
from hackathon_scraper.pipelines.normalize import normalize_record


class TestNormalization(unittest.TestCase):

    def test_normalize_raw_dict(self):
        raw = {
            "title": "Smart India Hackathon 2026",
            "organizer": "AICTE",
            "event_start_date": "2026-09-01",
            "event_end_date": "2026-12-31",
            "registration_deadline": "2026-09-30",
            "event_url": "https://sih.gov.in/",
            "source_site": "sih",
            "source_url": "https://sih.gov.in/",
        }

        rec = normalize_record(raw, is_structured=True)
        self.assertEqual(rec.title, "Smart India Hackathon 2026")
        self.assertEqual(rec.organizer, "AICTE")
        self.assertEqual(rec.source_site, "sih")
        self.assertIsNotNone(rec.id)
        self.assertGreaterEqual(rec.confidence, 0.7)


if __name__ == "__main__":
    unittest.main()
