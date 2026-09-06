"""
Unit tests for Date Extraction and ISO Normalization.
"""

import unittest
from hackathon_scraper.extractors.dates import extract_event_dates, parse_single_date


class TestDatesExtractor(unittest.TestCase):

    def test_parse_single_date_iso(self):
        self.assertEqual(parse_single_date("2026-09-20"), "2026-09-20")

    def test_parse_single_date_formatted(self):
        self.assertEqual(parse_single_date("20 Sep 2026"), "2026-09-20")
        self.assertEqual(parse_single_date("September 20, 2026"), "2026-09-20")
        self.assertEqual(parse_single_date("20/09/2026"), "2026-09-20")

    def test_extract_event_dates_range(self):
        start, end, raw, warn = extract_event_dates("Sep 20 - Sep 21, 2026")
        self.assertEqual(start, "2026-09-20")
        self.assertEqual(end, "2026-09-21")
        self.assertIsNone(warn)


if __name__ == "__main__":
    unittest.main()
