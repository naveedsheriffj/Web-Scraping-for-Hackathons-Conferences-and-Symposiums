"""
Date parsing and ISO normalization extractor with past-event validation.
"""

from datetime import datetime, date
import re
from typing import Optional, Tuple
from hackathon_scraper.config import CURRENT_DATE


def parse_single_date(date_str: Optional[str], default_year: Optional[int] = None) -> Optional[str]:
    """
    Parses a single date string into YYYY-MM-DD format.
    Returns None if date cannot be parsed confidently.
    """
    if not date_str:
        return None

    cleaned = date_str.strip()
    if not cleaned or len(cleaned) < 4:
        return None

    year_to_use = default_year or CURRENT_DATE.year

    # Try explicit ISO formats YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS
    iso_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", cleaned)
    if iso_match:
        y, m, d = iso_match.groups()
        try:
            dt = datetime(int(y), int(m), int(d))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Try DD/MM/YYYY or DD-MM-YYYY
    dmy_match = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", cleaned)
    if dmy_match:
        d, m, y = dmy_match.groups()
        try:
            dt = datetime(int(y), int(m), int(d))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    months = {
        "jan": 1, "january": 1,
        "feb": 2, "february": 2,
        "mar": 3, "march": 3,
        "apr": 4, "april": 4,
        "may": 5,
        "jun": 6, "june": 6,
        "jul": 7, "july": 7,
        "aug": 8, "august": 8,
        "sep": 9, "september": 9, "sept": 9,
        "oct": 10, "october": 10,
        "nov": 11, "november": 11,
        "dec": 12, "december": 12,
    }

    month_pattern = r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"

    # 20 Sep 2026
    m1 = re.search(r"(\d{1,2})(?:st|nd|rd|th)?\s+" + month_pattern + r"\s*(\d{4})?", cleaned, re.IGNORECASE)
    if m1:
        d_str, m_str, y_str = m1.groups()
        m_val = months.get(m_str.lower())
        y_val = int(y_str) if y_str else year_to_use
        if m_val and y_val:
            try:
                dt = datetime(y_val, m_val, int(d_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Sep 20, 2026
    m2 = re.search(month_pattern + r"\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s*(\d{4}))?", cleaned, re.IGNORECASE)
    if m2:
        m_str, d_str, y_str = m2.groups()
        m_val = months.get(m_str.lower())
        y_val = int(y_str) if y_str else year_to_use
        if m_val and y_val:
            try:
                dt = datetime(y_val, m_val, int(d_str))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    return None


def extract_event_dates(raw_date_str: Optional[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Extracts start date and end date from an event date string.
    Returns (event_start_date, event_end_date, event_date_raw, warning).
    """
    if not raw_date_str:
        return None, None, None, "Missing raw date text"

    raw = raw_date_str.strip()

    delimiters = r"\s*(?:-|–|—|to|until)\s*"
    parts = re.split(delimiters, raw, maxsplit=1)

    if len(parts) == 2:
        start_raw, end_raw = parts[0], parts[1]
        year_match = re.search(r"\b(20\d{2})\b", end_raw)
        year = int(year_match.group(1)) if year_match else CURRENT_DATE.year

        start_date = parse_single_date(start_raw, default_year=year)
        end_date = parse_single_date(end_raw, default_year=year)

        if start_date and not end_date:
            end_date = start_date

        return start_date, end_date, raw, None
    else:
        single_date = parse_single_date(raw)
        return single_date, single_date, raw, None


def is_past_event(event_end_date: Optional[str], event_start_date: Optional[str] = None) -> bool:
    """
    Checks if an event has already ended before CURRENT_DATE.
    Returns True if past, False if upcoming/current or unknown.
    """
    check_date_str = event_end_date or event_start_date
    if not check_date_str:
        return False

    try:
        dt = datetime.strptime(check_date_str, "%Y-%m-%d").date()
        return dt < CURRENT_DATE
    except ValueError:
        return False
