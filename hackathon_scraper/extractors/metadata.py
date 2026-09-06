"""
Metadata extractors for Mode, Location, Team Size, and Prizes without generic fallbacks.
"""

import re
from typing import Optional, Tuple


def normalize_mode(text: Optional[str], location_text: Optional[str] = None) -> str:
    """
    Normalizes event mode to ONLINE, OFFLINE, HYBRID, or UNKNOWN.
    Does NOT infer ONLINE or OFFLINE without explicit text evidence.
    """
    if not text and not location_text:
        return "UNKNOWN"

    combined = f"{text or ''} {location_text or ''}".upper()

    if "HYBRID" in combined:
        return "HYBRID"
    if "ONLINE" in combined or "VIRTUAL" in combined or "REMOTE" in combined:
        if "OFFLINE" in combined or "IN-PERSON" in combined or "ONSITE" in combined or "ON-SITE" in combined:
            return "HYBRID"
        return "ONLINE"
    if "OFFLINE" in combined or "IN-PERSON" in combined or "ONSITE" in combined or "ON-SITE" in combined or "PHYSICAL" in combined:
        return "OFFLINE"

    return "UNKNOWN"


def parse_location(location_str: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Parses location string into (full_location, city, state, country).
    Preserves exact location strings without reducing specific cities to 'India'.
    Returns (None, None, None, None) if location is not present.
    """
    if not location_str:
        return None, None, None, None

    cleaned = location_str.strip()
    if not cleaned or cleaned.upper() in ("ONLINE", "VIRTUAL", "REMOTE", "N/A", "NONE"):
        return None, None, None, None

    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    city, state, country = None, None, None

    if len(parts) == 1:
        city = parts[0]
        if city.lower() in ("india", "usa", "united states", "uk"):
            country = city
            city = None
    elif len(parts) == 2:
        city, country = parts[0], parts[1]
    elif len(parts) >= 3:
        country = parts[-1]
        state = parts[-2]
        candidate_city = parts[-3]
        if candidate_city.lower() in ("india", "usa", "united states", "uk"):
            candidate_city = parts[-4] if len(parts) >= 4 else parts[0]
        city = candidate_city

    return cleaned, city, state, country



COLLEGE_KEYWORDS = [
    "university", "institute", "college", "campus", "school of",
    "academy", "iit", "nit", "iiit", "bits", "gnit", "tiu", "glbim", "rvu"
]


def extract_college(text: Optional[str]) -> Optional[str]:
    """
    Extracts explicit college/university name from location or organizer strings.
    Returns None if no educational institution is found.
    """
    if not text:
        return None

    parts = [p.strip() for p in re.split(r"[,;\n]", text) if p.strip()]
    for part in parts:
        lower = part.lower()
        if any(kw in lower for kw in COLLEGE_KEYWORDS):
            return part
    return None



def parse_team_size(text: Optional[str]) -> Tuple[Optional[int], Optional[int], Optional[bool], Optional[str]]:
    """
    Parses team size text into (team_size_min, team_size_max, solo_allowed, team_size_str).
    Returns (None, None, None, None) if text is missing or generic.
    """
    if not text:
        return None, None, None, None

    cleaned = text.strip()
    
    # Range format: "2 - 4 Members", "1 to 5 people"
    range_match = re.search(r"(\d+)\s*(?:to|-)\s*(\d+)\s*(?:members|people|participants|team)?", cleaned, re.IGNORECASE)
    if range_match:
        min_s, max_s = int(range_match.group(1)), int(range_match.group(2))
        solo = min_s == 1
        return min_s, max_s, solo, f"{min_s}-{max_s}"

    # Single team size format: "up to 4 members", "Teams of 3"
    single_match = re.search(r"(?:up\s+to|max|teams?\s+of)\s+(\d+)", cleaned, re.IGNORECASE)
    if single_match:
        max_s = int(single_match.group(1))
        return 1, max_s, True, f"1-{max_s}"

    if "solo" in cleaned.lower() or "individual" in cleaned.lower():
        return 1, 1, True, "1"

    return None, None, None, None


def parse_prize(text: Optional[str]) -> Tuple[Optional[float], Optional[str], Optional[str], Optional[str]]:
    """
    Parses prize string into (prize_amount, prize_currency, prize_description, prize_str).
    Returns (None, None, None, None) if prize is absent or generic.
    """
    if not text:
        return None, None, None, None

    cleaned = text.strip()
    if not cleaned or cleaned.lower() in ("n/a", "none"):
        return None, None, None, None

    currency = "INR"
    if "$" in cleaned or "USD" in cleaned:
        currency = "USD"
    elif "EUR" in cleaned or "€" in cleaned:
        currency = "EUR"
    elif "GBP" in cleaned or "£" in cleaned:
        currency = "GBP"
    elif "₹" in cleaned or "INR" in cleaned or "RS" in cleaned.upper() or "RUPEES" in cleaned.upper():
        currency = "INR"

    # Extract numerical amount e.g. $138,000 or ₹1,00,000
    amount = None
    num_match = re.search(r"(?:[\$₹€£]|INR|USD|RS\.?)\s*([\d,]+(?:\.\d+)?)", cleaned, re.IGNORECASE)
    if not num_match:
        num_match = re.search(r"([\d,]+(?:\.\d+)?)\s*(?:lakh|crore|k|usd|inr|rupees)", cleaned, re.IGNORECASE)

    if num_match:
        raw_num = num_match.group(1).replace(",", "")
        try:
            amount = float(raw_num)
            if "lakh" in cleaned.lower():
                amount *= 100000
            elif "k" in cleaned.lower() and amount < 1000:
                amount *= 1000
        except ValueError:
            amount = None

    return amount, currency, cleaned, cleaned
