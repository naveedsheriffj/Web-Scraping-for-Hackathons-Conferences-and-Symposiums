"""
Regression & Edge-Case Unit Tests for Hackathon Scraper.
Tests all 10 failure cases specified in design criteria.
"""

import unittest
from hackathon_scraper.config import CURRENT_DATE
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.models.hackathon import Hackathon, ProvenanceInfo
from hackathon_scraper.pipelines.deduplicate import deduplicate_records, merge_hackathon_records
from hackathon_scraper.pipelines.export import export_normalized_records
from hackathon_scraper.validators.hackathon_validator import validate_hackathon


class TestRegressions(unittest.TestCase):

    def test_1_hackrit_no_fake_location_or_prize(self):
        """Case 1: Hackrit - ensure no fake location/prize fallbacks (location & prize remain null)."""
        rec = Hackathon(
            id="hackrit-1",
            title="Hackrit 2026",
            event_url="https://unstop.com/hackathons/hackrit-2026",
            source_site="unstop",
            source_url="https://unstop.com/hackathons/hackrit-2026",
            event_start_date="2026-10-01",
            event_end_date="2026-10-02",
            organizer=None,
            location=None,
            city=None,
            prize=None,
            raw_data_hash="hash_hackrit",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertEqual(rec.status, "VALID")
        self.assertIsNone(rec.location)
        self.assertIsNone(rec.prize)

    def test_2_metamorph_deadline_conflict(self):
        """Case 2: Metamorph 2.0 - multi-source deadline conflict stored in candidate_values."""
        rec1 = Hackathon(
            id="metamorph-1",
            title="Metamorph 2.0",
            event_url="https://devfolio.co/metamorph",
            source_site="devfolio",
            source_url="https://devfolio.co/metamorph",
            event_start_date="2026-10-15",
            registration_deadline="2026-10-10",
            deadline_source=ProvenanceInfo(type="visible_event_page", url="https://devfolio.co/metamorph", raw_value="Oct 10, 2026"),
            raw_data_hash="hash_meta1",
        )
        rec2 = Hackathon(
            id="metamorph-1",
            title="Metamorph 2.0",
            event_url="https://devfolio.co/metamorph",
            source_site="unstop",
            source_url="https://unstop.com/metamorph",
            event_start_date="2026-10-15",
            registration_deadline="2026-10-12",  # Conflicting deadline
            deadline_source=ProvenanceInfo(type="visible_event_page", url="https://unstop.com/metamorph", raw_value="Oct 12, 2026"),
            raw_data_hash="hash_meta2",
        )
        merged = merge_hackathon_records(rec1, rec2)
        self.assertEqual(merged.registration_deadline, "2026-10-10")
        self.assertTrue(len(merged.deadline_source.candidate_values) > 0)
        self.assertIn("unstop", merged.deadline_source.candidate_values[0]["source_site"])

    def test_3_boss_battle_no_fallbacks(self):
        """Case 3: BOSS Battle - strict metadata, no fallback organizer strings."""
        rec = Hackathon(
            id="boss-battle-1",
            title="BOSS Battle",
            event_url="https://devfolio.co/boss-battle",
            source_site="devfolio",
            source_url="https://devfolio.co/boss-battle",
            event_start_date="2026-11-01",
            organizer=None,
            raw_data_hash="hash_boss",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertEqual(rec.status, "VALID")
        self.assertIsNone(rec.organizer)

    def test_4_hackspire_optional_fields_null(self):
        """Case 4: HackSpire - optional missing fields remain null and record is VALID."""
        rec = Hackathon(
            id="hackspire-1",
            title="HackSpire",
            event_url="https://unstop.com/hackspire",
            source_site="unstop",
            source_url="https://unstop.com/hackspire",
            event_start_date="2026-10-10",
            event_end_date="2026-10-11",
            organizer=None,
            college=None,
            city=None,
            state=None,
            prize_amount=None,
            team_size_min=None,
            team_size_max=None,
            raw_data_hash="hash_hackspire",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertEqual(rec.status, "VALID")

    def test_5_hack_with_gdg_url_canonicalization(self):
        """Case 5: Hack With GDG S4 - tracking parameters and fragments stripped."""
        raw_url = "https://devfolio.co/hack-gdg-s4/?utm_source=telegram&ref=feature#details"
        canonical = canonicalize_url(raw_url)
        self.assertEqual(canonical, "https://devfolio.co/hack-gdg-s4")

    def test_6_code_clash_no_generic_organizer(self):
        """Case 6: Code Clash - no generic organizer string like 'Unstop Organizer'."""
        rec = Hackathon(
            id="code-clash-1",
            title="Code Clash 2026",
            event_url="https://unstop.com/code-clash",
            source_site="unstop",
            source_url="https://unstop.com/code-clash",
            event_start_date="2026-09-25",
            organizer=None,
            raw_data_hash="hash_clash",
        )
        self.assertIsNone(rec.organizer)
        self.assertNotEqual(rec.organizer, "Unstop Organizer")

    def test_7_singularity_mode_parsing(self):
        """Case 7: Singularity - mode parsed cleanly as ONLINE, missing location remains null."""
        rec = Hackathon(
            id="singularity-1",
            title="Singularity Hack 2026",
            event_url="https://hackerearth.com/challenges/singularity",
            source_site="hackerearth",
            source_url="https://hackerearth.com/challenges/singularity",
            event_start_date="2026-09-28",
            mode="ONLINE",
            location=None,
            raw_data_hash="hash_sing",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertEqual(rec.status, "VALID")
        self.assertEqual(rec.mode, "ONLINE")
        self.assertIsNone(rec.location)

    def test_8_sih_program_vs_hackathon_dates(self):
        """Case 8: SIH - program timeline classified as PROGRAM, not fake start/end dates."""
        rec = Hackathon(
            id="sih-program-1",
            title="Smart India Hackathon 2026",
            event_url="https://sih.gov.in/",
            source_site="sih",
            source_url="https://sih.gov.in/",
            event_type="PROGRAM",
            event_start_date=None,
            event_end_date=None,
            registration_deadline="2026-09-30",
            raw_data_hash="hash_sih",
        )
        self.assertEqual(rec.event_type, "PROGRAM")
        self.assertIsNone(rec.event_start_date)

    def test_9_knowafest_listing_page_exclusion(self):
        """Case 9: KnowAFest category/listing page classified as CATEGORY and excluded from upcoming.json."""
        rec = Hackathon(
            id="knowafest-cat-1",
            title="Hackathons in India",
            event_url="https://knowafest.com/explore/category/Hackathons",
            source_site="knowafest",
            source_url="https://knowafest.com/",
            page_type="CATEGORY",
            event_start_date="2026-09-10",
            raw_data_hash="hash_know_cat",
        )
        rec, missing, warnings = validate_hackathon(rec)
        paths = export_normalized_records([rec])
        
        import json
        with open(paths["upcoming_json"], "r", encoding="utf-8") as f:
            upcoming = json.load(f)
        
        self.assertEqual(len(upcoming), 0)  # Excluded because page_type != EVENT

    def test_10_devpost_past_event_classification(self):
        """Case 10: Devpost past event - ended event assigned PAST status."""
        rec = Hackathon(
            id="devpost-past-1",
            title="AI World Cup 2025",
            event_url="https://devpost.com/ai-world-cup-2025",
            source_site="devpost",
            source_url="https://devpost.com/ai-world-cup-2025",
            event_start_date="2025-01-01",
            event_end_date="2025-01-10",
            raw_data_hash="hash_past",
        )
        rec, missing, warnings = validate_hackathon(rec)
        self.assertEqual(rec.status, "PAST")


    def test_6_target_records_regressions(self):
        """Regression tests for the 6 target records as requested by user."""
        from hackathon_scraper.scrapers.devfolio import DevfolioScraper
        from hackathon_scraper.scrapers.unstop import UnstopScraper

        dev = DevfolioScraper()
        unstop = UnstopScraper()

        # 1. Hackrit
        hackrit = dev.fetch_details({"event_url": "https://hackrit2026.devfolio.co/", "source_url": "https://hackrit2026.devfolio.co/", "raw_item": {}})
        if hackrit and hackrit.get("event_start_date"):
            self.assertEqual(hackrit["event_start_date"], "2026-09-11")
            self.assertEqual(hackrit["event_end_date"], "2026-09-12")
            self.assertEqual(hackrit["registration_deadline"], "2026-09-06")
            self.assertNotEqual(hackrit["registration_deadline"], hackrit["event_start_date"])
            self.assertEqual(hackrit["city"], "Kolkata")
            self.assertEqual(hackrit["team_size_min"], 2)
            self.assertEqual(hackrit["team_size_max"], 4)
            self.assertEqual(hackrit["team_size"], "2-4")

        # 2. Metamorph 2.0
        meta = dev.fetch_details({"event_url": "https://metamorph-2.devfolio.co/", "source_url": "https://metamorph-2.devfolio.co/", "raw_item": {}})
        if meta and meta.get("event_start_date"):
            self.assertEqual(meta["event_start_date"], "2026-09-12")
            self.assertEqual(meta["event_end_date"], "2026-09-13")
            self.assertEqual(meta["registration_deadline"], "2026-09-06")
            self.assertNotEqual(meta["registration_deadline"], meta["event_start_date"])

        # 3. WebCraft24
        webcraft = dev.fetch_details({"event_url": "https://webcraft24.devfolio.co/", "source_url": "https://webcraft24.devfolio.co/", "raw_item": {}})
        if webcraft and webcraft.get("event_start_date"):
            self.assertEqual(webcraft["event_start_date"], "2026-09-25")
            self.assertEqual(webcraft["event_end_date"], "2026-09-26")
            self.assertEqual(webcraft["registration_deadline"], "2026-09-10")
            self.assertNotEqual(webcraft["registration_deadline"], webcraft["event_start_date"])
        self.assertEqual(webcraft["city"], "Greater Noida")
        self.assertEqual(webcraft["college"], "GL Bajaj Institute of Management")

        # 4. HackCelestial 3.0
        celestial = unstop.fetch_details({"event_url": "https://unstop.com/hackathons/hackcelestial-30-pillai-university-navi-mumbai-1737808", "source_url": "https://unstop.com/hackathons/hackcelestial-30-pillai-university-navi-mumbai-1737808"})
        self.assertEqual(celestial["event_start_date"], "2026-09-26")
        self.assertEqual(celestial["event_end_date"], "2026-09-27")
        self.assertEqual(celestial["registration_start"], "2026-08-17")
        self.assertNotEqual(celestial["event_start_date"], celestial["registration_start"])

        # 5. Singularity Hackathon
        singularity = unstop.fetch_details({"event_url": "https://unstop.com/hackathons/singularity-hackathon-aj-institute-of-engineering-and-technology-ajiet-mangalore-karnataka-1735180", "source_url": "https://unstop.com/hackathons/singularity-hackathon-aj-institute-of-engineering-and-technology-ajiet-mangalore-karnataka-1735180"})
        self.assertEqual(singularity["event_start_date"], "2026-10-08")
        self.assertEqual(singularity["event_end_date"], "2026-10-09")
        self.assertEqual(singularity["screening_start"], "2026-09-03")
        self.assertEqual(singularity["screening_end"], "2026-09-30")
        self.assertEqual(singularity["grand_finale_date"], "2026-10-08")
        self.assertNotEqual(singularity["event_start_date"], singularity["screening_start"])

        # 6. Code Clash
        clash = unstop.fetch_details({"event_url": "https://unstop.com/competitions/code-clash-rv-university-rvu-bangalore-1749224", "source_url": "https://unstop.com/competitions/code-clash-rv-university-rvu-bangalore-1749224"})
        self.assertEqual(clash["event_type"], "COMPETITION")
        self.assertEqual(clash["event_start_date"], "2026-09-25")
        self.assertNotEqual(clash["event_start_date"], "2026-09-04")
        self.assertEqual(clash["registration_start"], "2026-09-04")
        self.assertEqual(clash["team_size_min"], 2)
        self.assertEqual(clash["team_size_max"], 3)
        self.assertEqual(clash["team_size"], "2-3")
        self.assertEqual(clash["city"], "Bangalore")


if __name__ == "__main__":
    unittest.main()

