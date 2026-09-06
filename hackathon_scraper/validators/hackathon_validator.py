"""
Validation and evidence-based confidence scoring for Hackathon records.
"""

from typing import List, Tuple
from hackathon_scraper.extractors.dates import is_past_event
from hackathon_scraper.models.hackathon import Hackathon

ALLOWED_SOURCES = {"devfolio", "unstop", "sih", "hackerearth", "knowafest", "devpost"}
ALLOWED_MODES = {"ONLINE", "OFFLINE", "HYBRID", "UNKNOWN"}


def calculate_confidence(record: Hackathon) -> float:
    """
    Computes a transparent, evidence-based confidence score strictly between 0.0 and 1.0.
    Points are awarded ONLY when actual evidence exists:
    +0.15 title verified
    +0.20 event start date verified
    +0.10 event end date verified
    +0.15 registration deadline verified
    +0.10 organizer verified
    +0.05 college verified
    +0.05 location verified
    +0.05 mode verified (ONLINE/OFFLINE/HYBRID)
    +0.05 team size verified
    +0.05 prize verified
    +0.05 registration URL verified
    """
    score = 0.0

    if record.title and len(record.title.strip()) > 2:
        score += 0.15
    if record.event_start_date:
        score += 0.20
    if record.event_end_date:
        score += 0.10
    if record.registration_deadline:
        score += 0.15
    if record.organizer and len(record.organizer.strip()) > 1:
        score += 0.10
    if record.college and len(record.college.strip()) > 1:
        score += 0.05
    if record.location or record.city:
        score += 0.05
    if record.mode in ("ONLINE", "OFFLINE", "HYBRID"):
        score += 0.05
    if record.team_size_min is not None or record.team_size:
        score += 0.05
    if record.prize_amount is not None or record.prize:
        score += 0.05
    if record.registration_url and record.registration_url.startswith(("http://", "https://")):
        score += 0.05

    return round(min(max(score, 0.0), 1.0), 2)


def validate_hackathon(record: Hackathon) -> Tuple[Hackathon, List[str], List[str]]:
    """
    Validates a Hackathon record and assigns a status adhering to strict precedence:
    DUPLICATE -> PAST -> CONFLICT -> INVALID -> INCOMPLETE -> VALID

    Note: Missing optional fields (organizer, college, city, state, prize, team size, description)
    do NOT make an otherwise valid record INCOMPLETE or INVALID.
    """
    missing: List[str] = []
    warnings: List[str] = []

    # 1. Check essential required fields for VALID
    if not record.title or not record.title.strip():
        missing.append("title")
    if not record.event_url:
        missing.append("event_url")
    if not record.source_site or record.source_site not in ALLOWED_SOURCES:
        missing.append("source_site")
    if not record.event_start_date and not record.event_date:
        missing.append("event_date")

    # 2. Check optional fields inventory for auditing
    if not record.organizer:
        record.missing_fields.append("organizer")
    if not record.college:
        record.missing_fields.append("college")
    if not record.location and record.mode != "ONLINE":
        record.missing_fields.append("location")
    if not record.registration_deadline:
        record.missing_fields.append("registration_deadline")

    # 3. Validation Warnings & Cross-field Consistency
    if record.mode not in ALLOWED_MODES:
        warnings.append(f"Unrecognized mode: {record.mode}")

    if record.registration_deadline and record.event_start_date:
        if record.registration_deadline > record.event_start_date:
            warnings.append(f"Registration deadline ({record.registration_deadline}) is after event start date ({record.event_start_date})")

    if record.event_start_date and record.event_end_date:
        if record.event_end_date < record.event_start_date:
            warnings.append(f"Event end date ({record.event_end_date}) precedes event start date ({record.event_start_date})")

    record.missing_fields = missing
    record.validation_warnings = warnings

    # 4. Status Precedence Assignment: DUPLICATE -> PAST -> CONFLICT -> INVALID -> INCOMPLETE -> VALID
    if record.status == "DUPLICATE":
        pass  # Preserved from deduplication pipeline
    elif is_past_event(record.event_end_date, record.event_start_date):
        record.status = "PAST"
    elif record.status == "CONFLICT" or any("CONFLICT" in w.upper() or "disagrees" in w.lower() for w in warnings):
        record.status = "CONFLICT"
    elif record.page_type != "EVENT" or not record.event_url.startswith(("http://", "https://")):
        record.status = "INVALID"
    elif missing:
        # Missing essential fields (title, url, source_site, or date)
        record.status = "INCOMPLETE"
    else:
        # All essential fields present and upcoming
        record.status = "VALID"

    return record, missing, warnings
