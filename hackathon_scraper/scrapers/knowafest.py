"""
KnowAFest Scraper with strict page classification and detail page fetching.
"""

from typing import Any, Dict, List, Optional
from scrapling import Fetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import extract_event_dates
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import normalize_mode, parse_location
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.utils.text import clean_text


class KnowAFestScraper(BaseHackathonScraper):
    source_name = "knowafest"
    base_url = TARGET_URLS["knowafest"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = Fetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover individual hackathon event links from categories and listings."""
        discovered: List[Dict[str, Any]] = []
        visited_urls = set()

        urls_to_crawl = [
            "https://www.knowafest.com/explore/fest-type/Hackathon",
            "https://www.knowafest.com/explore/category/Hackathons",
            "https://www.knowafest.com/explore/events",
            "https://www.knowafest.com/explore/upcomingfests",
        ]

        for url in urls_to_crawl:
            if len(discovered) >= limit:
                break
            try:
                response = self.fetcher.get(url)
                if response.status != 200:
                    continue

                links = response.xpath("//a/@href").getall()
                for link in links:
                    if len(discovered) >= limit:
                        break
                    full_url = canonicalize_url(link, base_url="https://www.knowafest.com/")
                    if not full_url or full_url in visited_urls:
                        continue

                    # Filter EXCLUSIVELY for individual event detail URLs
                    if "/events/20" in full_url or ("/explore/events/" in full_url and len(full_url.split("/")) > 6):
                        visited_urls.add(full_url)
                        discovered.append({
                            "title": None,
                            "event_url": full_url,
                            "page_type": "EVENT",
                            "source_site": self.source_name,
                            "source_url": url,
                        })
            except Exception:
                continue

        return discovered

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Fetch and parse detailed event page on KnowAFest."""
        event_url = event_summary["event_url"]
        response = self.fetcher.get(event_url)

        if response.status != 200:
            return event_summary

        # Title
        raw_title = clean_text(
            response.css("h1::text").get()
            or response.xpath("//h2[contains(@class, 'title') or contains(@class, 'fest')]/text()").get()
            or response.xpath("//title/text()").get()
        )
        title = raw_title.split("|")[0].strip() if raw_title and "|" in raw_title else raw_title

        # Page classification check: if title represents a category page, flag as CATEGORY
        if title and ("Competitions, Events Contests" in title or "College Fests in India" in title):
            return {
                "title": title,
                "event_url": event_url,
                "page_type": "CATEGORY",
                "source_site": self.source_name,
                "source_url": event_summary["source_url"],
            }

        page_texts = [clean_text(t) for t in response.xpath("//tr//text() | //p//text() | //h2//text() | //h3//text() | //li//text()").getall()]
        page_texts = [t for t in page_texts if t]
        full_page_str = "\n".join(page_texts)

        dates_raw = None
        college = None
        organizer = None
        location_raw = None
        mode_raw = None
        deadline_raw = None
        registration_url = None
        description = None

        # Registration URL
        reg_link = response.xpath("//a[contains(translate(@href, 'APPLY', 'apply'), 'apply') or contains(translate(@href, 'REGISTER', 'register'), 'register') or contains(@href, 'forms.gle')]/@href").get()
        if reg_link:
            registration_url = canonicalize_url(reg_link, base_url=event_url)

        for idx, text in enumerate(page_texts):
            lower = text.lower()
            if "college" in lower and not college and idx + 1 < len(page_texts):
                college = page_texts[idx + 1]
            if ("organized by" in lower or "organizer" in lower) and not organizer and idx + 1 < len(page_texts):
                organizer = page_texts[idx + 1]
            if ("mode" in lower or "online" in lower or "offline" in lower or "hybrid" in lower) and not mode_raw:
                mode_raw = text
            if any(m in lower for m in ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]) and not dates_raw:
                if any(char.isdigit() for char in text):
                    dates_raw = text
            if "last date" in lower or "deadline" in lower:
                deadline_raw = text
            if "about" in lower and not description and idx + 1 < len(page_texts):
                description = page_texts[idx + 1]

        start_date, end_date, date_raw, _ = extract_event_dates(dates_raw)
        reg_deadline, dead_raw, _ = extract_registration_deadline(deadline_raw or full_page_str)
        mode = normalize_mode(mode_raw, location_text=location_raw)
        loc, city, state, country = parse_location(location_raw)

        return {
            "title": title or event_url.split("/")[-1].replace("-", " ").title(),
            "organizer": organizer,
            "college": college,
            "description": description,
            "page_type": "EVENT",
            "event_type": "HACKATHON",
            "event_date": date_raw or dates_raw,
            "event_start_date": start_date,
            "event_end_date": end_date,
            "registration_deadline": reg_deadline,
            "event_date_raw": date_raw or dates_raw,
            "deadline_raw": dead_raw or deadline_raw,
            "registration_url": registration_url or event_url,
            "event_url": event_url,
            "location": loc,
            "city": city,
            "state": state,
            "country": country,
            "mode": mode,
            "eligibility": None,
            "team_size": None,
            "prize": None,
            "prize_currency": "INR",
            "skills": ["Hackathon"],
            "technologies": [],
            "tags": ["KnowAFest", "College Fest"],
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {"type": "visible_event_page", "url": event_url, "raw_value": dates_raw, "evidence_text": dates_raw, "selection_reason": "Visible page date text"},
            "deadline_source": {"type": "visible_event_page", "url": event_url, "raw_value": deadline_raw, "evidence_text": deadline_raw, "selection_reason": "Visible page deadline text"},
            "organizer_source": {"type": "visible_event_page", "url": event_url, "raw_value": organizer, "evidence_text": organizer, "selection_reason": "Visible organizer label"},
            "college_source": {"type": "visible_event_page", "url": event_url, "raw_value": college, "evidence_text": college, "selection_reason": "Visible college label"},
            "location_source": {"type": "visible_event_page", "url": event_url, "raw_value": location_raw, "evidence_text": location_raw, "selection_reason": "Visible location section"},
            "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": registration_url, "evidence_text": registration_url, "selection_reason": "Registration action link"},
        }
