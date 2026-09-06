"""
Registration deadline extractor with explicit label checking.
"""

import re
from typing import Optional, Tuple
from hackathon_scraper.extractors.dates import parse_single_date


DEADLINE_PATTERNS = [
    r"(?:registration|apply|application|last\s+date|ends)\s*(?:deadline|closes|by|ends)?[:\s]*([^\n,]+)",
    r"apply\s+by\s*[:\s]*([^\n,]+)",
    r"registration\s+closes\s*[:\s]*([^\n,]+)",
    r"last\s+date\s+to\s+register\s*[:\s]*([^\n,]+)",
]


def extract_registration_deadline(text: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extracts explicit registration deadline from text content.
    Returns (registration_deadline_iso, deadline_raw, warning).
    """
    if not text:
        return None, None, "No text provided for deadline extraction"

    for pattern in DEADLINE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_deadline_str = match.group(1).strip()
            parsed_iso = parse_single_date(raw_deadline_str)
            if parsed_iso:
                return parsed_iso, raw_deadline_str, None

    # If text is already a short date string (e.g. from an API deadline field)
    iso_direct = parse_single_date(text)
    if iso_direct:
        return iso_direct, text, None

    return None, text, "Could not confidently extract registration deadline"
