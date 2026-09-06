# Hackathon Scraper — Production Hackathon Data Extractor

A robust, multi-source hackathon scraper built on top of the **Scrapling** framework. Collects accurate, normalized, and validated hackathon event records from 6 major platforms:

1. **Devfolio** (`https://devfolio.co/hackathons`)
2. **Unstop** (`https://unstop.com/hackathons`)
3. **Smart India Hackathon** (`https://sih.gov.in`)
4. **HackerEarth** (`https://www.hackerearth.com/challenges/`)
5. **KnowAFest** (`https://www.knowafest.com/`)
6. **Devpost** (`https://devpost.com/hackathons`)

---

## Architecture Overview

The application lives entirely in `hackathon_scraper/` and leaves the core Scrapling library untouched.

```
hackathon_scraper/
│
├── __init__.py
├── __main__.py               # CLI entrypoint
├── config.py                 # Configuration & limits
├── .env.example              # Environment variable template
├── README.md                 # Project documentation
│
├── models/                   # Strongly typed Pydantic models
│   ├── __init__.py
│   └── hackathon.py
│
├── scrapers/                 # Source-specific scrapers
│   ├── __init__.py
│   ├── base_scraper.py
│   ├── devfolio.py
│   ├── unstop.py
│   ├── sih.py
│   ├── hackerearth.py
│   ├── knowafest.py
│   └── devpost.py
│
├── extractors/               # Field extractors
│   ├── __init__.py
│   ├── dates.py              # ISO YYYY-MM-DD date normalizer
│   ├── deadlines.py          # Registration deadline parser
│   ├── urls.py               # Canonical URL normalizer
│   └── metadata.py           # Mode, location & team size extractor
│
├── validators/               # Schema & record validators
│   ├── __init__.py
│   └── hackathon_validator.py # Confidence scoring & warnings
│
├── pipelines/                # Data pipelines
│   ├── __init__.py
│   ├── normalize.py          # Model transformation
│   ├── deduplicate.py        # Fingerprint deduplication & merging
│   ├── export.py             # JSON, JSONL, CSV exporters
│   └── supabase_pipeline.py  # Offline-safe Supabase sync
│
├── utils/                    # Utility helpers
│   ├── __init__.py
│   ├── logging.py
│   ├── hashing.py            # SHA-256 raw hashing & fingerprinting
│   └── text.py
│
├── database/                 # Database DDL
│   └── schema.sql
│
├── output/                   # Output storage
│   ├── raw/                  # Per-source raw JSON outputs
│   ├── normalized/           # Final deduplicated dataset (.json, .jsonl, .csv)
│   └── errors/               # Logged errors
│
└── tests/                    # Unit test suite
    ├── test_dates.py
    ├── test_deadlines.py
    ├── test_validation.py
    ├── test_deduplication.py
    └── test_normalization.py
```

---

## Installation & Setup

### 1. Requirements
- Python 3.10+
- Scrapling (cloned locally)
- Playwright Chromium browsers

### 2. Environment Setup
```bash
# Install dependencies & scrapling
python -m pip install -e ".[all]" pydantic pandas requests

# Install Playwright chromium browser binaries
python -m playwright install chromium
```

---

## Usage & Commands

### Run Unit Tests
```bash
python -m unittest discover -s hackathon_scraper/tests
```

### Run Scrapers via CLI

#### Scrape a Single Source
```bash
python -m hackathon_scraper --source devfolio --max-events 10
python -m hackathon_scraper --source unstop --max-events 10
python -m hackathon_scraper --source knowafest --max-events 10
python -m hackathon_scraper --source sih --max-events 10
python -m hackathon_scraper --source hackerearth --max-events 10
python -m hackathon_scraper --source devpost --max-events 10
```

#### Scrape All Sources
```bash
python -m hackathon_scraper --source all --max-events 25
```

---

## Data Provenance & Accuracy

Accuracy is prioritized over quantity:
- Never hallucinates dates, deadlines, organizers, or colleges.
- Missing values are stored as `null` with explicit `missing_fields` tags.
- Every critical field tracks provenance (`event_date_source`, `deadline_source`, `organizer_source`, `college_source`, `location_source`, `registration_url_source`).

---

## Confidence Scoring Logic

Confidence is computed deterministically (0.0 to 1.0):
- `+0.20`: Verified Title
- `+0.20`: Extracted Event Start Date
- `+0.15`: Extracted Registration Deadline
- `+0.10`: Identified Organizer
- `+0.10`: Identified Location / Online Mode
- `+0.10`: Verified Registration URL
- `+0.10`: Successfully Processed Detail Page
- `+0.05`: Structured JSON / JSON-LD Source

---

## Output Files

Outputs are saved automatically to:
- `hackathon_scraper/output/raw/{source}_raw.json`
- `hackathon_scraper/output/normalized/hackathons.json`
- `hackathon_scraper/output/normalized/hackathons.jsonl`
- `hackathon_scraper/output/normalized/hackathons.csv`

---

## Troubleshooting

1. **Scrapling Import Errors**:
   Verify you run using the Python environment where `scrapling` was installed.
2. **Dynamic / Protected Pages**:
   `Devfolio`, `Unstop`, and `Devpost` automatically use `StealthyFetcher` or `DynamicFetcher` to bypass anti-bot and render JavaScript contents.
