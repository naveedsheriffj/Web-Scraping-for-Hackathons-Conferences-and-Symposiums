"""
Unit tests for Registration Deadline Extraction.
"""

import unittest
from hackathon_scraper.extractors.deadlines import extract_registration_deadline


class TestDeadlinesExtractor(unittest.TestCase):

    def test_explicit_registration_deadline(self):
        text = "Event Date: September 20. Registration Deadline: September 15, 2026."
        deadline_iso, raw, warn = extract_registration_deadline(text)
        self.assertEqual(deadline_iso, "2026-09-15")
        self.assertIsNone(warn)

    def test_apply_by_pattern(self):
        text = "Apply by 10 Oct 2026 to participate."
        deadline_iso, raw, warn = extract_registration_deadline(text)
        self.assertEqual(deadline_iso, "2026-10-10")
        self.assertIsNone(warn)


if __name__ == "__main__":
    unittest.main()
