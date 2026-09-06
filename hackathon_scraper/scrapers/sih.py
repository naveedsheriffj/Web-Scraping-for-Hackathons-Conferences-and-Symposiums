"""
Smart India Hackathon (SIH) Scraper implementation using static Fetcher.
"""

from typing import Any, Dict, List, Optional
from scrapling import Fetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import extract_event_dates
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import normalize_mode, parse_location
from hackathon_scraper.utils.text import clean_text


class SIHScraper(BaseHackathonScraper):
    source_name = "sih"
    base_url = TARGET_URLS["sih"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = Fetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover SIH problem statements & edition announcements."""
        discovered: List[Dict[str, Any]] = []

        # Target latest PS page and home page
        urls = [
            "https://sih.gov.in/sih2026PS",
            "https://sih.gov.in/",
        ]

        for url in urls:
            if len(discovered) >= limit:
                break
            try:
                response = self.fetcher.get(url)
                if response.status != 200:
                    continue

                # Parse problem statement tables if available
                rows = response.xpath("//table//tr")
                current_ps: Dict[str, Any] = {}

                for r in rows:
                    if len(discovered) >= limit:
                        break
                    cells = [clean_text(c) for c in r.xpath(".//td//text() | .//th//text()").getall() if clean_text(c)]
                    if not cells:
                        continue

                    if len(cells) >= 3 and cells[0].isdigit():
                        if current_ps.get("title"):
                            discovered.append(current_ps)
                        current_ps = {
                            "ps_id": cells[-1] if len(cells) > 3 else cells[0],
                            "organization": cells[1] if len(cells) > 1 else "Government of India",
                            "title": f"SIH 2026: {cells[2]}",
                            "category": cells[3] if len(cells) > 3 else "Software/Hardware",
                            "event_url": url,
                            "source_site": self.source_name,
                            "source_url": url,
                        }
                    elif "Description" in cells[0] and current_ps:
                        current_ps["description"] = " ".join(cells[1:])

                if current_ps and current_ps.get("title") and len(discovered) < limit:
                    discovered.append(current_ps)

                # Fallback: if no tables found, add main SIH event card
                if not discovered:
                    discovered.append({
                        "title": "Smart India Hackathon 2026",
                        "organization": "MoE Innovation Cell & AICTE",
                        "description": "World's biggest open innovation model for college students.",
                        "event_url": "https://sih.gov.in/",
                        "source_site": self.source_name,
                        "source_url": "https://sih.gov.in/",
                    })

            except Exception:
                continue

        return discovered[:limit]

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Process detail attributes for SIH problem statement/edition."""
        title = event_summary.get("title") or "Smart India Hackathon"
        org = event_summary.get("organization")
        desc = event_summary.get("description")
        event_url = event_summary.get("event_url", "https://sih.gov.in/")

        # Determine event_type and page_type
        if event_summary.get("ps_id"):
            event_type = "PROBLEM_STATEMENT"
            page_type = "EVENT"
        else:
            event_type = "PROGRAM"
            page_type = "EVENT"

        # Attempt to parse live text from response if available
        page_text = ""
        try:
            res = self.fetcher.get(event_url)
            if res.status == 200:
                page_text = " ".join([clean_text(t) for t in res.xpath("//body//text()").getall() if clean_text(t)])
        except Exception:
            pass

        # Extract real dates if present, else keep null
        reg_deadline, dead_raw, dead_label = extract_registration_deadline(page_text) if page_text else (None, None, None)
        start_date, end_date, date_raw, date_label = extract_event_dates(page_text) if page_text else (None, None, None)

        mode = normalize_mode(page_text) if page_text else "UNKNOWN"

        return {
            "title": title,
            "organizer": org,
            "college": None,
            "description": desc,
            "page_type": page_type,
            "event_type": event_type,
            "event_date": date_raw,
            "event_start_date": start_date,
            "event_end_date": end_date,
            "registration_deadline": reg_deadline,
            "event_date_raw": date_raw,
            "deadline_raw": dead_raw,
            "registration_url": event_url,
            "event_url": event_url,
            "location": None,
            "city": None,
            "state": None,
            "country": "India",
            "mode": mode,
            "eligibility": "HEI Students in India" if "HEI" in page_text else None,
            "team_size": None,
            "team_size_min": None,
            "team_size_max": None,
            "prize": None,
            "prize_amount": None,
            "prize_currency": "INR",
            "skills": [],
            "technologies": [],
            "tags": ["Smart India Hackathon"],
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {"type": "visible_event_page" if date_raw else "unknown", "url": event_url, "label": date_label, "raw_value": date_raw},
            "deadline_source": {"type": "visible_event_page" if dead_raw else "unknown", "url": event_url, "label": dead_label, "raw_value": dead_raw},
            "organizer_source": {"type": "visible_event_page" if org else "unknown", "url": event_url, "raw_value": org},
            "college_source": {"type": "unknown", "url": event_url, "raw_value": None},
            "location_source": {"type": "unknown", "url": event_url, "raw_value": None},
            "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": event_url},
        }
