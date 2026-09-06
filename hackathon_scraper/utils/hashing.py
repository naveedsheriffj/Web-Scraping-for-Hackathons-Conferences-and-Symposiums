"""
Hashing and fingerprinting utilities for deduplication and provenance verification.
"""

import hashlib
import json
import re
from typing import Any, Dict, Optional


def compute_raw_hash(data: Any) -> str:
    """Computes a SHA-256 hash of raw record payload."""
    if isinstance(data, (dict, list)):
        serialized = json.dumps(data, sort_keys=True, default=str)
    else:
        serialized = str(data)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def normalize_text_for_fingerprint(text: Optional[str]) -> str:
    """Normalizes string for comparison (lowercase, strip special chars & spaces)."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def compute_fingerprint(
    title: str,
    organizer: Optional[str] = None,
    event_start_date: Optional[str] = None,
    city: Optional[str] = None,
    event_url: Optional[str] = None,
) -> str:
    """
    Generates a deterministic fingerprint for deduplicating hackathons across sources.
    Combines normalized title, organizer, start date, city, and canonical domain/path if available.
    """
    norm_title = normalize_text_for_fingerprint(title)
    norm_org = normalize_text_for_fingerprint(organizer or "")
    norm_date = (event_start_date or "").strip()
    norm_city = normalize_text_for_fingerprint(city or "")

    parts = [norm_title, norm_org, norm_date, norm_city]
    fingerprint_raw = "|".join(parts)
    return hashlib.sha256(fingerprint_raw.encode("utf-8")).hexdigest()
