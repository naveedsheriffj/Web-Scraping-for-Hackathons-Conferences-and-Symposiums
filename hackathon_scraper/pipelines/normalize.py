"""
Normalization pipeline converting raw extracted dictionaries into normalized Hackathon Pydantic models.
"""

from typing import Any, Dict, List, Tuple
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.models.hackathon import Hackathon, ProvenanceInfo
from hackathon_scraper.utils.hashing import compute_fingerprint, compute_raw_hash
from hackathon_scraper.validators.hackathon_validator import calculate_confidence, validate_hackathon


def normalize_record(raw_dict: Dict[str, Any], is_structured: bool = False) -> Hackathon:
    """
    Transforms a raw dict into a normalized Hackathon model with full provenance and confidence scoring.
    """
    title = (raw_dict.get("title") or "Untitled Hackathon").strip()
    organizer = raw_dict.get("organizer")
    college = raw_dict.get("college")
    event_start_date = raw_dict.get("event_start_date")
    city = raw_dict.get("city")
    event_url = raw_dict.get("event_url") or "https://unknown-event.org"
    source_site = raw_dict.get("source_site", "unknown").strip().lower()

    # Canonicalize URL and generate dedupe_key
    canonical_event_url = canonicalize_url(event_url) or event_url.strip()
    dedupe_key = f"{source_site}|{canonical_event_url}"

    # Generate canonical fingerprint ID
    canonical_id = compute_fingerprint(
        title=title,
        organizer=organizer or college,
        event_start_date=event_start_date,
        city=city,
        event_url=canonical_event_url,
    )

    raw_hash = compute_raw_hash(raw_dict)

    # Provenance conversion helpers
    def to_provenance(val: Any) -> ProvenanceInfo:
        if isinstance(val, ProvenanceInfo):
            return val
        if isinstance(val, dict):
            return ProvenanceInfo(**val)
        if isinstance(val, str):
            return ProvenanceInfo(type="event_page", raw_value=val)
        return ProvenanceInfo()

    record = Hackathon(
        id=canonical_id,
        title=title,
        organizer=organizer,
        college=college,
        description=raw_dict.get("description"),
        event_date=raw_dict.get("event_date"),
        event_start_date=event_start_date,
        event_end_date=raw_dict.get("event_end_date"),
        registration_deadline=raw_dict.get("registration_deadline"),
        event_date_raw=raw_dict.get("event_date_raw"),
        deadline_raw=raw_dict.get("deadline_raw"),
        registration_url=raw_dict.get("registration_url"),
        event_url=canonical_event_url,
        dedupe_key=dedupe_key,
        location=raw_dict.get("location"),
        city=city,
        state=raw_dict.get("state"),
        country=raw_dict.get("country"),
        mode=raw_dict.get("mode", "UNKNOWN"),
        eligibility=raw_dict.get("eligibility"),
        team_size=raw_dict.get("team_size"),
        prize=raw_dict.get("prize"),
        prize_currency=raw_dict.get("prize_currency", "INR"),
        skills=raw_dict.get("skills", []),
        technologies=raw_dict.get("technologies", []),
        tags=raw_dict.get("tags", []),
        source_site=source_site,
        source_sites=[source_site],
        source_url=raw_dict.get("source_url") or event_url,
        event_date_source=to_provenance(raw_dict.get("event_date_source")),
        deadline_source=to_provenance(raw_dict.get("deadline_source")),
        organizer_source=to_provenance(raw_dict.get("organizer_source")),
        college_source=to_provenance(raw_dict.get("college_source")),
        location_source=to_provenance(raw_dict.get("location_source")),
        registration_url_source=to_provenance(raw_dict.get("registration_url_source")),
        confidence=0.5,
        raw_data_hash=raw_hash,
    )

    # Validate & calculate confidence
    record, missing, warnings = validate_hackathon(record)
    record.confidence = calculate_confidence(record)

    return record
