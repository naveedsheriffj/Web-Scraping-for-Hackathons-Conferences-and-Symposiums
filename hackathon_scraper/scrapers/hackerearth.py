"""
HackerEarth Hackathon Scraper inspecting actual event pages for classification.
"""

from typing import Any, Dict, List, Optional
from scrapling import Fetcher, DynamicFetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import extract_event_dates
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import normalize_mode, parse_location, parse_prize, parse_team_size
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.utils.text import clean_text


EXCLUDE_KEYWORDS = ["hiring", "coding test", "assessment", "quiz", "practice challenge", "job challenge"]
INCLUDE_KEYWORDS = ["hackathon", "buildathon", "innovation challenge", "developer competition", "build challenge", "hackathon/"]


class HackerEarthScraper(BaseHackathonScraper):
    source_name = "hackerearth"
    base_url = TARGET_URLS["hackerearth"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = Fetcher()
        self.dynamic_fetcher = DynamicFetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover challenge links from HackerEarth listings."""
        discovered: List[Dict[str, Any]] = []
        visited = set()

        try:
            response = self.dynamic_fetcher.fetch(self.base_url)
            if response.status == 200:
                links = response.xpath("//a[contains(@href, '/challenges/')] /@href").getall()
                for link in links:
                    if len(discovered) >= limit:
                        break
                    full_url = canonicalize_url(link, base_url="https://www.hackerearth.com/")
                    if not full_url or full_url in visited or full_url.endswith("/challenges/"):
                        continue

                    visited.add(full_url)
                    discovered.append({
                        "event_url": full_url,
                        "source_site": self.source_name,
                        "source_url": self.base_url,
                    })
        except Exception:
            pass

        return discovered

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Inspect actual event page before classification and field extraction."""
        event_url = event_summary["event_url"]
        response = self.fetcher.get(event_url)

        if response.status != 200:
            return event_summary

        title = clean_text(
            response.css("h1::text").get()
            or response.css("title::text").get()
        )
        if title and "|" in title:
            title = title.split("|")[0].strip()

        page_text = " ".join([clean_text(t) for t in response.xpath("//body//text()").getall() if clean_text(t)])
        lower_text = f"{title or ''} {page_text}".lower()

        # Classification check: Exclude hiring tests, coding assessments, quizzes
        if any(k in lower_text for k in EXCLUDE_KEYWORDS) and not any(k in lower_text for k in INCLUDE_KEYWORDS):
            return {
                "title": title,
                "event_url": event_url,
                "page_type": "EVENT",
                "event_type": "COMPETITION",
                "source_site": self.source_name,
                "source_url": event_summary["source_url"],
                "status": "INVALID",
            }

        # Classify as HACKATHON or BUILDATHON
        event_type = "BUILDATHON" if "buildathon" in lower_text or "build challenge" in lower_text else "HACKATHON"

        organizer = None
        if title and " by " in title:
            organizer = title.split(" by ")[-1].strip()

        reg_deadline, dead_raw, _ = extract_registration_deadline(page_text)
        start_date, end_date, date_raw, _ = extract_event_dates(page_text)
        mode = normalize_mode(page_text)
        min_t, max_t, solo, t_str = parse_team_size(page_text)
        amt, curr, p_desc, p_str = parse_prize(page_text)

        reg_link = response.xpath("//a[contains(translate(@href, 'REGISTER', 'register'), 'register') or contains(translate(@href, 'SUBMIT', 'submit'), 'submit')]/@href").get()
        registration_url = canonicalize_url(reg_link, base_url=event_url) if reg_link else event_url

        return {
            "title": title or "HackerEarth Event",
            "organizer": organizer,  # NO generic fallback!
            "college": None,
            "description": None,     # NO generic fallback!
            "page_type": "EVENT",
            "event_type": event_type,
            "event_date": date_raw,
            "event_start_date": start_date,
            "event_end_date": end_date,
            "registration_deadline": reg_deadline,
            "event_date_raw": date_raw,
            "deadline_raw": dead_raw,
            "registration_url": registration_url,
            "event_url": event_url,
            "location": None,
            "city": None,
            "state": None,
            "country": None,
            "mode": mode,
            "eligibility": None,
            "team_size_min": min_t,
            "team_size_max": max_t,
            "solo_allowed": solo,
            "team_size": t_str,
            "prize_amount": amt,
            "prize_currency": curr,
            "prize_description": p_desc,
            "prize": p_str,
            "skills": ["Software Engineering", "Hackathon"],
            "technologies": [],
            "tags": ["HackerEarth", event_type],
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {"type": "visible_event_page", "url": event_url, "raw_value": date_raw, "evidence_text": date_raw, "selection_reason": "Visible page text"},
            "deadline_source": {"type": "visible_event_page", "url": event_url, "raw_value": dead_raw, "evidence_text": dead_raw, "selection_reason": "Visible deadline text"},
            "organizer_source": {"type": "visible_event_page", "url": event_url, "raw_value": organizer, "evidence_text": organizer, "selection_reason": "Extracted from title/page"},
            "college_source": {"type": "unknown", "url": event_url, "raw_value": None},
            "location_source": {"type": "unknown", "url": event_url, "raw_value": None},
            "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": registration_url, "evidence_text": registration_url, "selection_reason": "Registration action link"},
        }
