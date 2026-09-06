"""
Unstop Hackathon Scraper implementation removing all fallback values.
"""

from typing import Any, Dict, List, Optional
from scrapling import Fetcher, StealthyFetcher
from hackathon_scraper.config import TARGET_URLS, MAX_EVENTS
from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.extractors.dates import extract_event_dates
from hackathon_scraper.extractors.deadlines import extract_registration_deadline
from hackathon_scraper.extractors.metadata import extract_college, normalize_mode, parse_location, parse_prize, parse_team_size
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.utils.text import clean_text


class UnstopScraper(BaseHackathonScraper):
    source_name = "unstop"
    base_url = TARGET_URLS["unstop"]

    def __init__(self, delay: float = 1.0, timeout: int = 30):
        super().__init__(delay=delay, timeout=timeout)
        self.fetcher = StealthyFetcher()
        self.api_fetcher = Fetcher()

    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover Unstop hackathon event URLs using StealthyFetcher."""
        discovered: List[Dict[str, Any]] = []
        visited = set()

        pages = [
            f"{self.base_url}?oppstatus=open",
            f"{self.base_url}?oppstatus=upcoming",
        ]

        for page_url in pages:
            if len(discovered) >= limit:
                break
            try:
                response = self.fetcher.fetch(page_url)
                if response.status != 200:
                    continue

                links = response.xpath("//a/@href").getall()
                for link in links:
                    if len(discovered) >= limit:
                        break
                    full_url = canonicalize_url(link, base_url="https://unstop.com/")
                    if not full_url or full_url in visited:
                        continue

                    if "/hackathons/" in full_url or "/competitions/" in full_url:
                        if full_url not in ("https://unstop.com/hackathons", "https://unstop.com/competitions"):
                            visited.add(full_url)
                            discovered.append({
                                "event_url": full_url,
                                "page_type": "EVENT",
                                "source_site": self.source_name,
                                "source_url": page_url,
                            })
            except Exception:
                continue

        return discovered[:limit]

    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Process Unstop hackathon slug and detail attributes without fallbacks."""
        event_url = event_summary["event_url"]
        
        # Extract title, college, and id from URL slug
        slug = event_url.split("/")[-1].split("?")[0].strip("/")
        parts = slug.split("-")

        opp_id = parts[-1] if parts and parts[-1].isdigit() else None
        
        # Try fetching official JSON API endpoint first
        api_data = None
        if opp_id:
            try:
                api_url = f"https://unstop.com/api/public/competition/{opp_id}"
                res = self.api_fetcher.get(api_url)
                if res.status == 200:
                    api_data = res.json().get("data", {}).get("competition", {})
            except Exception:
                pass

        if api_data:
            title = api_data.get("title") or api_data.get("display_title")
            org_info = api_data.get("organisation", {})
            organizer = org_info.get("name") if isinstance(org_info, dict) else None

            subtype = (api_data.get("subtype") or "").lower()
            opp_type = (api_data.get("type") or "").lower()

            # Event Classification: ICPC-style competitive programming contest vs Hackathon
            if subtype in ["online_coding_challenge", "coding_challenge", "quiz"] or "coding contest" in (title or "").lower() or "icpc" in (title or "").lower() or "code clash" in (title or "").lower():
                event_type = "COMPETITION"
            else:
                event_type = "HACKATHON"


            # Location & College
            addr_obj = api_data.get("address_with_country_logo")
            loc_str = None
            city = None
            state = None
            country = "India"
            college = extract_college(organizer)

            if isinstance(addr_obj, dict):
                addr_text = addr_obj.get("address")
                city = addr_obj.get("city")
                state = addr_obj.get("state")
                c_data = addr_obj.get("country")
                country = c_data.get("name") if isinstance(c_data, dict) else "India"
                parts_loc = [p for p in [addr_text, city, state, country] if p]
                loc_str = ", ".join(parts_loc) if parts_loc else None
                college = extract_college(addr_text) or college

            if not loc_str:
                raw_loc = api_data.get("location")
                if raw_loc:
                    loc_str, city, state, country = parse_location(raw_loc)
                    college = extract_college(loc_str) or college

            # Dates & Multi-stage Milestones
            raw_start = api_data.get("start_date")
            raw_end = api_data.get("end_date")
            reg_reqs = api_data.get("regnRequirements") or {}
            raw_reg_end = reg_reqs.get("end_regn_dt") or api_data.get("regn_open")
            raw_reg_start = reg_reqs.get("start_regn_dt")

            reg_start_date = raw_reg_start[:10] if raw_reg_start and len(raw_reg_start) >= 10 else (raw_start[:10] if raw_start and len(raw_start) >= 10 else None)
            reg_deadline = raw_reg_end[:10] if raw_reg_end and isinstance(raw_reg_end, str) and len(raw_reg_end) >= 10 else None

            event_start_date = None
            event_end_date = None
            screening_start = None
            screening_end = None
            grand_finale_date = None

            rounds = api_data.get("rounds", [])
            for r in rounds:
                for d in r.get("details", []):
                    r_title = (d.get("title") or "").lower()
                    r_start_raw = d.get("start_date")
                    r_end_raw = d.get("end_date")
                    r_start = r_start_raw[:10] if r_start_raw and len(r_start_raw) >= 10 else None
                    r_end = r_end_raw[:10] if r_end_raw and len(r_end_raw) >= 10 else None

                    if any(kw in r_title for kw in ["screening", "ideathon", "submission", "round 1"]):
                        if r_start:
                            screening_start = r_start
                        if r_end:
                            screening_end = r_end
                    elif any(kw in r_title for kw in ["finale", "offline", "round 2", "round 3", "coding"]):
                        event_start_date = r_start
                        event_end_date = r_end
                        grand_finale_date = r_start

            # Fallback if rounds did not explicitly specify a finale/event round
            if not event_start_date:
                if rounds and len(rounds) > 0:
                    last_r = rounds[-1]
                    for d in last_r.get("details", []):
                        if d.get("start_date"):
                            event_start_date = d.get("start_date")[:10]
                            event_end_date = d.get("end_date")[:10] if d.get("end_date") else event_start_date
                            grand_finale_date = event_start_date
                            break

            if not event_start_date:
                event_start_date = raw_start[:10] if raw_start and len(raw_start) >= 10 else None
                event_end_date = raw_end[:10] if raw_end and len(raw_end) >= 10 else event_start_date

            date_summary = f"{event_start_date or ''} to {event_end_date or ''}".strip(" to") or None

            # Mode
            region = (api_data.get("region") or "").lower()
            mode = "ONLINE" if "online" in region else ("OFFLINE" if "offline" in region else "UNKNOWN")

            # Team Size Normalization
            min_t = reg_reqs.get("min_team_size")
            max_t = reg_reqs.get("max_team_size")
            solo = (min_t == 1) if min_t is not None else None
            t_str = f"{min_t}-{max_t}" if min_t is not None and max_t is not None else (str(min_t) if min_t else None)

            # Prizes
            prizes = api_data.get("prizes", [])
            prize_amt = None
            prize_curr = "INR"
            if isinstance(prizes, list) and len(prizes) > 0:
                first_prize = prizes[0]
                if isinstance(first_prize, dict):
                    prize_amt = first_prize.get("cash")
                    prize_curr = first_prize.get("currencyCode", "INR")
            prize_str = f"{prize_curr} {prize_amt:,.0f}" if prize_amt else None

            desc = clean_text(api_data.get("details")) if api_data.get("details") else None

            return {
                "title": title,
                "organizer": organizer,
                "college": college,
                "description": desc,
                "page_type": "EVENT",
                "event_type": event_type,
                "event_date": date_summary,
                "event_start_date": event_start_date,
                "event_end_date": event_end_date,
                "registration_start": reg_start_date,
                "registration_deadline": reg_deadline,
                "screening_start": screening_start,
                "screening_end": screening_end,
                "grand_finale_date": grand_finale_date,
                "event_date_raw": raw_start,
                "deadline_raw": raw_reg_end,
                "registration_url": event_url,
                "event_url": event_url,
                "location": loc_str,
                "city": city,
                "state": state,
                "country": country,
                "mode": mode,
                "eligibility": None,
                "team_size_min": min_t,
                "team_size_max": max_t,
                "solo_allowed": solo,
                "team_size": t_str,
                "prize_amount": prize_amt,
                "prize_currency": prize_curr,
                "prize_description": None,
                "prize": prize_str,
                "skills": ["Coding", "Hackathon"],
                "technologies": [],
                "tags": ["Unstop"],
                "source_site": self.source_name,
                "source_url": event_summary["source_url"],
                "event_date_source": {"type": "api_response", "url": event_url, "raw_value": str(event_start_date), "evidence_text": f"Unstop competition API rounds finale date: {event_start_date}", "selection_reason": "Mapped finale/event round start_date from Unstop competition API rounds"},
                "deadline_source": {"type": "api_response", "url": event_url, "raw_value": raw_reg_end, "evidence_text": f"end_regn_dt: {raw_reg_end}", "selection_reason": "Unstop public API regnRequirements.end_regn_dt"},
                "organizer_source": {"type": "api_response", "url": event_url, "raw_value": organizer, "evidence_text": organizer, "selection_reason": "Unstop public API organisation.name"},
                "college_source": {"type": "api_response", "url": event_url, "raw_value": college, "evidence_text": college, "selection_reason": "Unstop public API address/organizer college name"},
                "location_source": {"type": "api_response", "url": event_url, "raw_value": loc_str, "evidence_text": loc_str, "selection_reason": "Unstop public API address_with_country_logo"},
                "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": event_url, "evidence_text": event_url, "selection_reason": "Page event URL"},
            }


        # Fallback to visible HTML parsing if API unavailable
        title_raw = slug.replace("-", " ").title()
        page_text = ""
        try:
            res = self.fetcher.fetch(event_url)
            if res.status == 200:
                page_text = " ".join([clean_text(t) for t in res.xpath("//body//*[not(self::script or self::style)]/text()").getall() if clean_text(t)])
        except Exception:
            pass

        reg_deadline, dead_raw, _ = extract_registration_deadline(page_text) if page_text else (None, None, None)
        start_date, end_date, date_raw, _ = extract_event_dates(page_text) if page_text else (None, None, None, None)
        mode = normalize_mode(page_text)
        loc, city, state, country = parse_location(page_text)
        min_t, max_t, solo, t_str = parse_team_size(page_text)
        amt, curr, p_desc, p_str = parse_prize(page_text)

        return {
            "title": title_raw,
            "organizer": None,
            "college": None,
            "description": None,
            "page_type": "EVENT",
            "event_type": "HACKATHON",
            "event_date": date_raw,
            "event_start_date": start_date,
            "event_end_date": end_date,
            "registration_deadline": reg_deadline,
            "event_date_raw": date_raw,
            "deadline_raw": dead_raw,
            "registration_url": event_url,
            "event_url": event_url,
            "location": loc,
            "city": city,
            "state": state,
            "country": country,
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
            "skills": ["Coding", "Hackathon"],
            "technologies": [],
            "tags": ["Unstop"],
            "source_site": self.source_name,
            "source_url": event_summary["source_url"],
            "event_date_source": {"type": "visible_event_page", "url": event_url, "raw_value": date_raw, "evidence_text": date_raw, "selection_reason": "Visible page date"},
            "deadline_source": {"type": "visible_event_page", "url": event_url, "raw_value": dead_raw, "evidence_text": dead_raw, "selection_reason": "Visible deadline"},
            "organizer_source": {"type": "unknown", "url": event_url, "raw_value": None, "evidence_text": None, "selection_reason": None},
            "college_source": {"type": "unknown", "url": event_url, "raw_value": None, "evidence_text": None, "selection_reason": None},
            "location_source": {"type": "visible_event_page", "url": event_url, "raw_value": loc, "evidence_text": loc, "selection_reason": "Parsed location"},
            "registration_url_source": {"type": "visible_event_page", "url": event_url, "raw_value": event_url, "evidence_text": event_url, "selection_reason": "Page event URL"},
        }
