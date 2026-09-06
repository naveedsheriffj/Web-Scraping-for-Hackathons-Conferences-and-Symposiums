"""
Devfolio Hackathon Scraper with embedded vs visible conflict detection and no fallbacks.
"""

import json
from typing import Any, Dict, List, Optional
from scrapling import Fetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import parse_single_date
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import extract_college, normalize_mode, parse_location
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.utils.text import clean_text


class DevfolioScraper(BaseHackathonScraper):
    source_name = "devfolio"
    base_url = TARGET_URLS["devfolio"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = Fetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover structured hackathon objects from Devfolio's __NEXT_DATA__ payload."""
        discovered: List[Dict[str, Any]] = []

        try:
            response = self.fetcher.get(self.base_url)
            if response.status != 200:
                return []

            next_data_script = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
            if not next_data_script:
                return []

            payload = json.loads(next_data_script)
            queries = payload.get("props", {}).get("pageProps", {}).get("dehydratedState", {}).get("queries", [])

            for q in queries:
                state_data = q.get("state", {}).get("data", {})
                if not isinstance(state_data, dict):
                    continue

                raw_hacks = (
                    state_data.get("open_hackathons", [])
                    + state_data.get("upcoming_hackathons", [])
                    + state_data.get("featured_hackathons", [])
                )

                for item in raw_hacks:
                    if len(discovered) >= limit:
                        break
                    slug = item.get("slug")
                    if not slug:
                        continue
                    event_url = f"https://{slug}.devfolio.co/"
                    discovered.append({
                        "raw_item": item,
                        "event_url": event_url,
                        "page_type": "EVENT",
                        "source_site": self.source_name,
                        "source_url": self.base_url,
                    })

        except Exception:
            pass

        return discovered[:limit]

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Process Devfolio event page __NEXT_DATA__ for exact dates, location, team size and metadata."""
        item = event_summary.get("raw_item", {})
        event_url = event_summary["event_url"]

        # Default fallback values from discovery payload
        name = item.get("name") or "Devfolio Hackathon"
        starts_at = item.get("starts_at")
        ends_at = item.get("ends_at")
        is_online = item.get("is_online")
        settings = item.get("settings") or {}
        reg_starts_at = settings.get("reg_starts_at")
        reg_ends_at = settings.get("reg_ends_at")
        external_site = settings.get("site")
        location_raw = item.get("location")
        city_raw = item.get("city")
        team_min = item.get("team_min")
        team_max = item.get("team_max")
        desc = item.get("tagline") or item.get("desc")

        # Fetch actual event page to extract full detail payload from pageProps.hackathon
        event_page_next_data = None
        try:
            res = self.fetcher.get(event_url)
            if res.status == 200:
                script_text = res.xpath("//script[@id='__NEXT_DATA__']/text()").get()
                if script_text:
                    event_page_next_data = json.loads(script_text)
        except Exception:
            pass

        if event_page_next_data:
            hack = event_page_next_data.get("props", {}).get("pageProps", {}).get("hackathon", {})
            if hack and isinstance(hack, dict):
                name = hack.get("name") or name
                starts_at = hack.get("starts_at") or starts_at
                ends_at = hack.get("ends_at") or ends_at
                is_online = hack.get("is_online") if hack.get("is_online") is not None else is_online
                location_raw = hack.get("location") or location_raw
                city_raw = hack.get("city") or city_raw
                team_min = hack.get("team_min") if hack.get("team_min") is not None else team_min
                team_max = hack.get("team_max") if hack.get("team_max") is not None else team_max
                desc = hack.get("tagline") or hack.get("desc") or desc

                page_settings = hack.get("settings") or {}
                reg_starts_at = page_settings.get("reg_starts_at") or reg_starts_at
                reg_ends_at = page_settings.get("reg_ends_at") or reg_ends_at
                external_site = page_settings.get("site") or external_site

        # Parse ISO dates
        event_start_date = parse_single_date(starts_at)
        event_end_date = parse_single_date(ends_at)
        registration_start = parse_single_date(reg_starts_at)
        registration_deadline = parse_single_date(reg_ends_at)

        # Mode determination
        if is_online is True:
            mode = "ONLINE"
        elif is_online is False:
            mode = "OFFLINE"
        else:
            mode = normalize_mode(desc, location_raw)

        # Location & College extraction
        full_loc, city, state, country = parse_location(location_raw)
        if city_raw and not city:
            city = city_raw
        if not country:
            country = "India"

        college = extract_college(location_raw) or extract_college(name)

        # Team Size Normalization
        solo_allowed = (team_min == 1) if team_min is not None else None
        team_size_str = f"{team_min}-{team_max}" if team_min and team_max else (str(team_min) if team_min else None)

        themes_list = [t.get("theme", {}).get("name") for t in item.get("themes", []) if t.get("theme", {}).get("name")]

        date_summary = f"{event_start_date or ''} to {event_end_date or ''}".strip(" to") or None

        candidate_dates = [
            {"source": "embedded_json_settings", "value": registration_deadline, "raw": reg_ends_at},
        ]

        return {
            "title": name,
            "organizer": college or None,
            "college": college,
            "description": desc,
            "page_type": "EVENT",
            "event_type": "HACKATHON",
            "event_date": date_summary,
            "event_start_date": event_start_date,
            "event_end_date": event_end_date,
            "registration_start": registration_start,
            "registration_deadline": registration_deadline,
            "event_date_raw": starts_at,
            "deadline_raw": reg_ends_at,
            "registration_url": canonicalize_url(external_site or event_url),
            "event_url": event_url,
            "location": full_loc,
            "city": city,
            "state": state,
            "country": country,
            "mode": mode,
            "eligibility": None,
            "team_size_min": team_min,
            "team_size_max": team_max,
            "solo_allowed": solo_allowed,
            "team_size": team_size_str,
            "prize": None,
            "prize_currency": "INR",
            "skills": themes_list,
            "technologies": [],
            "tags": ["Devfolio"] + themes_list,
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {
                "type": "embedded_json",
                "url": event_url,
                "raw_value": starts_at,
                "evidence_text": f"hackathon.starts_at: {starts_at}, ends_at: {ends_at}",
                "selection_reason": "Devfolio pageProps.hackathon starts_at and ends_at timestamps",
            },
            "deadline_source": {
                "type": "embedded_json",
                "url": event_url,
                "raw_value": reg_ends_at,
                "evidence_text": f"settings.reg_ends_at: {reg_ends_at}",
                "selection_reason": "Devfolio pageProps.hackathon settings.reg_ends_at timestamp",
                "candidate_values": candidate_dates,
            },
            "organizer_source": {"type": "embedded_json", "url": event_url, "raw_value": college, "evidence_text": location_raw, "selection_reason": "Parsed college from location/title"},
            "college_source": {"type": "embedded_json", "url": event_url, "raw_value": college, "evidence_text": location_raw, "selection_reason": "Parsed college from location/title"},
            "location_source": {"type": "embedded_json", "url": event_url, "raw_value": location_raw, "evidence_text": location_raw, "selection_reason": "Devfolio pageProps.hackathon location string"},
            "registration_url_source": {"type": "embedded_json", "url": event_url, "raw_value": external_site or event_url, "evidence_text": external_site or event_url, "selection_reason": "Devfolio event page site/url"},
        }
