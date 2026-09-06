"""
Configuration management for Hackathon Scraper.
"""

from datetime import datetime, timezone
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
RAW_OUTPUT_DIR = OUTPUT_DIR / "raw"
EVIDENCE_OUTPUT_DIR = OUTPUT_DIR / "evidence"
NORMALIZED_OUTPUT_DIR = OUTPUT_DIR / "normalized"
ERROR_OUTPUT_DIR = OUTPUT_DIR / "errors"

# Ensure output directories exist
RAW_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
NORMALIZED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ERROR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Scraper limits & defaults
MAX_PAGES = int(os.getenv("MAX_PAGES", "5"))
MAX_EVENTS = int(os.getenv("MAX_EVENTS", "25"))
MAX_DETAIL_PAGES = int(os.getenv("MAX_DETAIL_PAGES", "25"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "3"))
REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))  # Seconds between requests
TIMEOUT = int(os.getenv("TIMEOUT", "30"))  # Timeout in seconds

# Execution Date / Target Date for reproducible testing
TARGET_DATE_ENV = os.getenv("TARGET_DATE")
if TARGET_DATE_ENV:
    try:
        CURRENT_DATE = datetime.strptime(TARGET_DATE_ENV.strip(), "%Y-%m-%d").date()
    except ValueError:
        CURRENT_DATE = datetime.now(timezone.utc).date()
else:
    CURRENT_DATE = datetime.now(timezone.utc).date()

# Supabase Credentials (Optional)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Source Target URLs
TARGET_URLS = {
    "devfolio": "https://devfolio.co/hackathons",
    "unstop": "https://unstop.com/hackathons",
    "sih": "https://sih.gov.in",
    "hackerearth": "https://www.hackerearth.com/challenges/",
    "knowafest": "https://www.knowafest.com/",
    "devpost": "https://devpost.com/hackathons",
}
