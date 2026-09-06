-- Hackathon Scraper Database Schema (Supabase / PostgreSQL Ready)
-- Target: 33 fields for hackathons table
-- Run this in your Supabase SQL Editor to create or upgrade the hackathons table.

--------------------------------------------------------------------------------
-- 1. TABLE CREATION SCHEMA (Target 33 Fields)
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hackathons (
    -- 1. Identity (6)
    id VARCHAR(64) PRIMARY KEY,
    title TEXT NOT NULL,
    source_site VARCHAR(50) NOT NULL,
    event_url TEXT NOT NULL,
    registration_url TEXT,
    event_type VARCHAR(30) DEFAULT 'HACKATHON',

    -- 2. Details (7)
    start_date DATE,
    end_date DATE,
    mode VARCHAR(20) DEFAULT 'UNKNOWN',
    location TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'India',

    -- 3. Org (2)
    organizer TEXT,
    college TEXT,

    -- 4. Participation (4)
    eligibility TEXT,
    team_size_min INT,
    team_size_max INT,
    solo_allowed BOOLEAN,

    -- 5. Prizes (3)
    prize_amount NUMERIC,
    prize_currency VARCHAR(10) DEFAULT 'INR',
    prize_description TEXT,

    -- 6. Deadlines (4)
    registration_start DATE,
    registration_deadline DATE,
    submission_deadline DATE,
    other_deadlines JSONB DEFAULT '[]'::jsonb,

    -- 7. Content (3)
    description TEXT,
    themes TEXT[],
    technologies TEXT[],

    -- 8. Sync Metadata (4)
    dedupe_key VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- 2. SAFE MIGRATION SCRIPT FOR EXISTING TABLES (Run in Supabase SQL Editor)
--------------------------------------------------------------------------------
-- Step A: Add missing columns safely
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS start_date DATE;
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS end_date DATE;
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS themes TEXT[];
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS technologies TEXT[];
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS other_deadlines JSONB DEFAULT '[]'::jsonb;
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(255);
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMPTZ DEFAULT NOW();

-- Step B: Populate dedupe_key for existing records using source_site and canonicalized event_url
UPDATE hackathons
SET dedupe_key = LOWER(source_site) || '|' || LOWER(REGEXP_REPLACE(event_url, '/+$', ''))
WHERE dedupe_key IS NULL OR dedupe_key = '';

-- Step C: Check & Remove Existing Duplicates before creating Unique Index
DELETE FROM hackathons h1
USING hackathons h2
WHERE h1.dedupe_key = h2.dedupe_key
  AND h1.dedupe_key IS NOT NULL
  AND (h1.last_scraped_at < h2.last_scraped_at OR (h1.last_scraped_at = h2.last_scraped_at AND h1.ctid < h2.ctid));

-- Step D: Create Unique Index for dedupe_key (enforces upsert on dedupe_key)
CREATE UNIQUE INDEX IF NOT EXISTS idx_hackathons_dedupe_key ON hackathons(dedupe_key);

-- Step E: Safely drop deprecated columns no longer in the target 33 fields schema
ALTER TABLE hackathons DROP COLUMN IF EXISTS page_type;
ALTER TABLE hackathons DROP COLUMN IF EXISTS event_date;
ALTER TABLE hackathons DROP COLUMN IF EXISTS event_start_date;
ALTER TABLE hackathons DROP COLUMN IF EXISTS event_end_date;
ALTER TABLE hackathons DROP COLUMN IF EXISTS submission_start;
ALTER TABLE hackathons DROP COLUMN IF EXISTS screening_start;
ALTER TABLE hackathons DROP COLUMN IF EXISTS screening_end;
ALTER TABLE hackathons DROP COLUMN IF EXISTS grand_finale_date;
ALTER TABLE hackathons DROP COLUMN IF EXISTS event_date_raw;
ALTER TABLE hackathons DROP COLUMN IF EXISTS deadline_raw;
ALTER TABLE hackathons DROP COLUMN IF EXISTS team_size;
ALTER TABLE hackathons DROP COLUMN IF EXISTS prize;
ALTER TABLE hackathons DROP COLUMN IF EXISTS skills;
ALTER TABLE hackathons DROP COLUMN IF EXISTS tags;
ALTER TABLE hackathons DROP COLUMN IF EXISTS source_sites;
ALTER TABLE hackathons DROP COLUMN IF EXISTS source_url;
ALTER TABLE hackathons DROP COLUMN IF EXISTS event_date_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS deadline_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS organizer_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS college_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS location_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS registration_url_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS team_size_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS prize_source;
ALTER TABLE hackathons DROP COLUMN IF EXISTS confidence;
ALTER TABLE hackathons DROP COLUMN IF EXISTS scraped_at;
ALTER TABLE hackathons DROP COLUMN IF EXISTS raw_data_hash;
ALTER TABLE hackathons DROP COLUMN IF EXISTS status;
ALTER TABLE hackathons DROP COLUMN IF EXISTS missing_fields;
ALTER TABLE hackathons DROP COLUMN IF EXISTS validation_warnings;

--------------------------------------------------------------------------------
-- 3. PERFORMANCE & QUERY INDEXES
--------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_hackathons_source_site ON hackathons(source_site);
CREATE INDEX IF NOT EXISTS idx_hackathons_start_date ON hackathons(start_date);
CREATE INDEX IF NOT EXISTS idx_hackathons_registration_deadline ON hackathons(registration_deadline);
CREATE INDEX IF NOT EXISTS idx_hackathons_city ON hackathons(city);
CREATE INDEX IF NOT EXISTS idx_hackathons_country ON hackathons(country);
CREATE INDEX IF NOT EXISTS idx_hackathons_mode ON hackathons(mode);

