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
    event_start_date = raw_dict.get("event_start_date") or raw_dict.get("start_date")
    event_end_date = raw_dict.get("event_end_date") or raw_dict.get("end_date")
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

    # Themes and Technologies
    themes = raw_dict.get("themes") or raw_dict.get("tags") or []
    technologies = raw_dict.get("technologies") or raw_dict.get("skills") or []
    if isinstance(themes, str):
        themes = [themes]
    if isinstance(technologies, str):
        technologies = [technologies]

    # Structured other_deadlines
    other_deadlines = []
    if isinstance(raw_dict.get("other_deadlines"), list):
        for d in raw_dict["other_deadlines"]:
            if isinstance(d, dict) and "name" in d and "date" in d:
                other_deadlines.append({"name": str(d["name"]), "date": str(d["date"])})

    if raw_dict.get("screening_start"):
        other_deadlines.append({"name": "Screening Start", "date": str(raw_dict["screening_start"])})
    if raw_dict.get("screening_end"):
        other_deadlines.append({"name": "Screening End", "date": str(raw_dict["screening_end"])})
    if raw_dict.get("grand_finale_date"):
        other_deadlines.append({"name": "Grand Finale", "date": str(raw_dict["grand_finale_date"])})

    record = Hackathon(
        id=canonical_id,
        title=title,
        source_site=source_site,
        event_url=canonical_event_url,
        registration_url=raw_dict.get("registration_url"),
        event_type=raw_dict.get("event_type", "HACKATHON"),
        start_date=event_start_date,
        end_date=event_end_date,
        mode=raw_dict.get("mode", "UNKNOWN"),
        location=raw_dict.get("location"),
        city=city,
        state=raw_dict.get("state"),
        country=raw_dict.get("country", "India"),
        organizer=organizer,
        college=college,
        eligibility=raw_dict.get("eligibility"),
        team_size_min=raw_dict.get("team_size_min"),
        team_size_max=raw_dict.get("team_size_max"),
        solo_allowed=raw_dict.get("solo_allowed"),
        prize_amount=raw_dict.get("prize_amount"),
        prize_currency=raw_dict.get("prize_currency", "INR"),
        prize_description=raw_dict.get("prize_description"),
        registration_start=raw_dict.get("registration_start"),
        registration_deadline=raw_dict.get("registration_deadline"),
        submission_deadline=raw_dict.get("submission_deadline"),
        other_deadlines=other_deadlines,
        description=raw_dict.get("description"),
        themes=list(dict.fromkeys(themes)),
        technologies=list(dict.fromkeys(technologies)),
        dedupe_key=dedupe_key,
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
