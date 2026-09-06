"""
Text processing and cleaning helper functions.
"""

import re
from typing import Optional


def clean_text(text: Optional[str]) -> Optional[str]:
    """Cleans up messy text, stripping HTML entities, extra whitespace, and newlines."""
    if not text:
        return None
    # Replace multiple whitespaces/newlines with a single space
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None


def extract_currency(text: Optional[str]) -> str:
    """Detects currency symbol/code from text, default to INR for Indian contexts or USD."""
    if not text:
        return "INR"
    text_upper = text.upper()
    if "$" in text or "USD" in text:
        return "USD"
    if "EUR" in text or "€" in text:
        return "EUR"
    if "GBP" in text or "£" in text:
        return "GBP"
    if "₹" in text or "INR" in text or "RUPEES" in text or "RS" in text:
        return "INR"
    return "INR"
