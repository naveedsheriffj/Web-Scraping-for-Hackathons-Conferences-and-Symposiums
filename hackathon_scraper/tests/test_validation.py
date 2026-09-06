"""
Unit tests for Hackathon Validation & Confidence Scoring.
"""

import unittest
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.validators.hackathon_validator import calculate_confidence, validate_hackathon


class TestValidation(unittest.TestCase):

    def test_valid_hackathon(self):
        rec = Hackathon(
            id="test-id-123",
            title="AI Hackathon 2026",
            organizer="Test Tech Org",
            event_start_date="2026-09-20",
            registration_deadline="2026-09-15",
            event_url="https://example.com/hackathon",
            source_site="devfolio",
            source_url="https://example.com/hackathon",
            raw_data_hash="abc123hash",
        )
        rec, missing, warnings = validate_hackathon(rec)
        score = calculate_confidence(rec)

        self.assertEqual(rec.status, "VALID")
        self.assertGreaterEqual(score, 0.6)

    def test_invalid_date_order(self):
        rec = Hackathon(
            id="test-id-456",
            title="Suspicious Hackathon",
            event_start_date="2026-09-20",
            registration_deadline="2026-09-25",  # Deadline after start date
            event_url="https://example.com/hackathon2",
            source_site="unstop",
            source_url="https://example.com/hackathon2",
            raw_data_hash="xyz456hash",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertTrue(any("Registration deadline" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
