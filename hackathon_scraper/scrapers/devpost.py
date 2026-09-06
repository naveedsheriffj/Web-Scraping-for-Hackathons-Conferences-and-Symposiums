"""
Devpost Hackathon Scraper implementation using DynamicFetcher and Fetcher.
"""

from typing import Any, Dict, List, Optional
from scrapling import Fetcher, DynamicFetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import extract_event_dates
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import normalize_mode, parse_location
from hackathon_scraper.extractors.urls import normalize_url
from hackathon_scraper.utils.text import clean_text


class DevpostScraper(BaseHackathonScraper):
    source_name = "devpost"
    base_url = TARGET_URLS["devpost"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = Fetcher()
        self.dynamic_fetcher = DynamicFetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover Devpost hackathon event links."""
        discovered: List[Dict[str, Any]] = []
        visited = set()

        pages = [f"{self.base_url}?page={p}" for p in range(1, 4)]
        for page_url in pages:
            if len(discovered) >= limit:
                break
            try:
                response = self.dynamic_fetcher.fetch(page_url)
                if response.status != 200:
                    continue

                links = response.xpath("//a[contains(@href, 'devpost.com')]/@href").getall()
                for link in links:
                    if len(discovered) >= limit:
                        break
                    full_url = normalize_url(link, base_url=self.base_url)
                    if not full_url or full_url in visited:
                        continue

                    # Filter for actual hackathon subdomains/paths
                    if ".devpost.com" in full_url and not any(x in full_url for x in ["info.devpost.com", "secure.devpost.com", "help.devpost.com", "blog.devpost.com"]):
                        visited.add(full_url)
                        discovered.append({
                            "title": None,
                            "event_url": full_url,
                            "source_site": self.source_name,
                            "source_url": page_url,
                        })
            except Exception:
                continue

        return discovered

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Process Devpost hackathon detail page."""
        event_url = event_summary["event_url"]
        response = self.fetcher.get(event_url)

        if response.status != 200:
            return event_summary

        title_raw = response.xpath("//title/text()").get() or ""
        title = title_raw.split("- Devpost")[0].strip() if "- Devpost" in title_raw else title_raw.strip()
        if title.endswith("| Devpost"):
            title = title[:-9].strip()

        page_text = " ".join([clean_text(t) for t in response.xpath("//body//text()").getall() if clean_text(t)])

        organizer = None
        # Devpost mentions host/sponsor name in stats or headings
        org_node = response.xpath("//div[contains(@class, 'host')]//text() | //span[contains(@class, 'organizer')]//text() | //div[contains(@id, 'hackathon-organizer')]//text()").get()
        if org_node and clean_text(org_node):
            organizer = clean_text(org_node)

        # Mode & Location parsing
        mode = normalize_mode(page_text)
        loc_node = response.xpath("//span[contains(@class, 'location')]//text() | //div[contains(@class, 'location')]//text()").get()
        loc_str = clean_text(loc_node) if loc_node else None
        city, state, country = parse_location(loc_str) if loc_str else (None, None, None)

        # Dates & deadlines
        reg_deadline, dead_raw, dead_label = extract_registration_deadline(page_text)
        start_date, end_date, date_raw, date_label = extract_event_dates(page_text)

        # Prize pool
        prize_node = response.xpath("//span[contains(@class, 'prize')]//text() | //div[contains(@class, 'prize-pool')]//text()").get()
        prize = clean_text(prize_node) if prize_node else None

        # Description
        desc_node = response.xpath("//meta[@name='description']/@content | //div[contains(@id, 'app-details')]//text()").get()
        desc = clean_text(desc_node) if desc_node else None

        # Page Type
        page_type = "EVENT" if ".devpost.com" in event_url else "UNKNOWN"

        return {
            "title": title or None,
            "organizer": organizer,
            "college": None,
            "description": desc,
            "page_type": page_type,
            "event_type": "HACKATHON",
            "event_date": date_raw,
            "event_start_date": start_date,
            "event_end_date": end_date,
            "registration_deadline": reg_deadline,
            "event_date_raw": date_raw,
            "deadline_raw": dead_raw,
            "registration_url": event_url,
            "event_url": event_url,
            "location": loc_str,
            "city": city,
            "state": state,
            "country": country,
            "mode": mode,
            "eligibility": None,
            "team_size": None,
            "team_size_min": None,
            "team_size_max": None,
            "prize": prize,
            "prize_amount": None,
            "prize_currency": None,
            "skills": [],
            "technologies": [],
            "tags": [],
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {"type": "visible_event_page", "url": event_url, "label": date_label, "raw_value": date_raw},
            "deadline_source": {"type": "visible_event_page", "url": event_url, "label": dead_label, "raw_value": dead_raw},
            "organizer_source": {"type": "visible_event_page" if organizer else "unknown", "url": event_url, "raw_value": organizer},
            "college_source": {"type": "unknown", "url": event_url, "raw_value": None},
            "location_source": {"type": "visible_event_page" if loc_str else "unknown", "url": event_url, "raw_value": loc_str},
            "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": event_url},
        }
