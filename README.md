# 🚀 Web Scraping for Hackathons, Conferences, and Symposiums

A production-grade, multi-source web scraping and automated daily synchronization pipeline built to collect, normalize, validate, and persist hackathon and technical event data into a **Supabase** backend.

Supported platforms:
1. **Devfolio** (`https://devfolio.co/hackathons`)
2. **Unstop** (`https://unstop.com/hackathons`)
3. **Smart India Hackathon (SIH)** (`https://sih.gov.in`)
4. **HackerEarth** (`https://www.hackerearth.com/challenges/`)
5. **KnowAFest** (`https://www.knowafest.com/`)
6. **Devpost** (`https://devpost.com/hackathons`)

---

## 🏗️ Architecture & Data Flow

```
+-----------------------------------------------------------------------+
|                             DAILY SCHEDULER                           |
|                       (GitHub Actions Workflow)                       |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                      EXISTING HACKATHON SCRAPER                       |
|          (Devfolio, Unstop, SIH, HackerEarth, KnowAFest, Devpost)       |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                        DATA NORMALIZATION & VALIDATION                |
|           (Semantic Milestone Dates, Locations, Team Sizes, Prizes)   |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                   URL CANONICALIZATION & DEDUPE KEY                   |
|        Format: <normalized_source_site>|<canonical_event_url>          |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                  INCREMENTAL SUPABASE SYNC (PostgREST)                |
|      • Compare dedupe_key against existing database records           |
|      • INSERT new events with created_at, updated_at, last_scraped_at   |
|      • UPDATE existing events                                         |
|      • PRESERVE existing reliable values when new scrape is null      |
+-----------------------------------------------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                      SUPABASE PERSISTENT DATABASE                     |
|            (Website queries upcoming VALID events for display)        |
+-----------------------------------------------------------------------+
```

---

## ✨ Key Features

- **6 Target Platforms Supported**: Specialized scrapers for Devfolio, Unstop, SIH, HackerEarth, KnowAFest, and Devpost.
- **Semantic Date Mapping**: Accurately extracts separate lifecycle dates (Event Start/End, Registration Start/Deadline, Submission, Screening, Finale) without flattening multi-stage events.
- **URL Canonicalization & Deduplication**: Strips tracking parameters (`utm_*`, `ref`, `gclid`), fragments (`#`), and trailing slashes to generate a unique `dedupe_key`.
- **Intelligent Upsert & Null Preservation**: Updating existing records preserves reliable historical values if a new scrape temporarily fails to extract specific fields.
- **Fault Isolation**: Single-source scraper failures log errors and allow remaining scrapers to proceed without deleting or corrupting existing database records.
- **Automated Daily Sync**: Configured with GitHub Actions (`.github/workflows/daily-scraper.yml`) for automated daily execution and manual triggers (`workflow_dispatch`).
- **Confidence Scoring & Provenance Tracking**: Tracks evidence snippets, candidate values, and extraction confidence for every record.

---

## 📁 Repository Structure

```
.github/workflows/
  └── daily-scraper.yml        # GitHub Actions automated daily workflow
hackathon_scraper/
  ├── __main__.py              # CLI Entrypoint & formatted run logging
  ├── config.py                # System settings & environment variables
  ├── .env.example              # Template for local environment configuration
  ├── database/
  │   └── schema.sql           # PostgreSQL / Supabase Schema & Migration DDL
  ├── models/
  │   └── hackathon.py         # Pydantic v2 Normalized Data Model
  ├── scrapers/                # Scrapers for 6 platforms
  │   ├── base_scraper.py
  │   ├── devfolio.py
  │   ├── unstop.py
  │   ├── sih.py
  │   ├── hackerearth.py
  │   ├── knowafest.py
  │   └── devpost.py
  ├── extractors/              # Field-level extraction logic
  │   ├── dates.py             # ISO YYYY-MM-DD date parser
  │   ├── deadlines.py         # Deadline parser
  │   ├── urls.py              # Canonical URL normalizer
  │   └── metadata.py          # Location, mode, prizes & team size
  ├── pipelines/
  │   ├── normalize.py         # Record normalization & dedupe_key generator
  │   ├── deduplicate.py       # Cross-source deduplication logic
  │   ├── supabase_pipeline.py # Incremental PostgREST UPSERT pipeline
  │   └── export.py            # Local JSON/CSV export pipeline
  ├── validators/              # Validation & confidence scoring
  └── tests/                   # Test suite (20/20 unit & regression tests)
```

---

## ⚡ Quickstart

### 1. Installation & Environment Setup

```bash
# Clone repository
git clone https://github.com/naveedsheriffj/Web-Scraping-for-Hackathons-Conferences-and-Symposiums.git
cd Web-Scraping-for-Hackathons-Conferences-and-Symposiums

# Install package & dependencies
pip install -e .

# Install Playwright browser binaries
python -m playwright install chromium
```

### 2. Environment Credentials Setup

Create a `.env` file or export environment variables:

```bash
SUPABASE_URL=https://your-supabase-project.supabase.co
SUPABASE_KEY=your-supabase-anon-or-service-role-key
MAX_EVENTS=25
```

---

## 🗄️ Database Setup & Migration

Run the following SQL in your **Supabase SQL Editor** to create or upgrade the `hackathons` table with unique deduplication constraint and tracking indexes:

```sql
-- 1. Add missing columns safely if they do not exist
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(255);
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMPTZ DEFAULT NOW();

-- 2. Populate dedupe_key for existing records using source_site and canonicalized event_url
UPDATE hackathons
SET dedupe_key = LOWER(source_site) || '|' || LOWER(REGEXP_REPLACE(event_url, '/+$', ''))
WHERE dedupe_key IS NULL OR dedupe_key = '';

-- 3. Create Unique Index for dedupe_key
CREATE UNIQUE INDEX IF NOT EXISTS idx_hackathons_dedupe_key ON hackathons(dedupe_key);
```

---

## 🖥️ Usage

### Run Scraper Pipeline Locally

```bash
# Run all scrapers and sync results to Supabase
python -m hackathon_scraper --source all --max-events 25

# Run a specific scraper source
python -m hackathon_scraper --source devfolio --max-events 10
python -m hackathon_scraper --source unstop --max-events 10
```

### Run Test Suite

```bash
python -m unittest discover -s hackathon_scraper/tests
```

### Export Data to Pandas DataFrame / CSV

```bash
python hackathon_scraper/to_dataframe.py
```

---

## 📊 Sample Execution Log Output

```text
=====================================
HACKATHON SCRAPER RUN
=====================================
Sources: 6
Scraped: 30
New: 0
Updated: 26
Unchanged: 0
Duplicates: 4
Invalid: 0
Conflicts: 0
Failed sources: 0
=====================================
```

---

## 🔍 Upcoming Events Database Query Example

To retrieve upcoming valid hackathons for a website backend from Supabase:

```sql
SELECT *
FROM hackathons
WHERE status = 'VALID'
  AND (event_end_date >= CURRENT_DATE OR event_end_date IS NULL)
ORDER BY event_start_date ASC;
```

---

## 🛡️ License

Distributed under the MIT License.
