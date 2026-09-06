-- Hackathon Scraper Database Schema (Supabase / PostgreSQL Ready)
-- Run this in your Supabase SQL Editor to create or upgrade the hackathons table.

--------------------------------------------------------------------------------
-- 1. TABLE CREATION SCHEMA
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hackathons (
    id VARCHAR(64) PRIMARY KEY,
    dedupe_key VARCHAR(255),
    title TEXT NOT NULL,
    organizer TEXT,
    college TEXT,
    description TEXT,

    page_type VARCHAR(30) DEFAULT 'EVENT',
    event_type VARCHAR(30) DEFAULT 'HACKATHON',

    event_date TEXT,
    event_start_date DATE,
    event_end_date DATE,
    registration_start DATE,
    registration_deadline DATE,
    submission_start DATE,
    submission_deadline DATE,
    screening_start DATE,
    screening_end DATE,
    grand_finale_date DATE,

    event_date_raw TEXT,
    deadline_raw TEXT,

    registration_url TEXT,
    event_url TEXT NOT NULL,

    location TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'India',

    mode VARCHAR(20) DEFAULT 'UNKNOWN',

    eligibility TEXT,
    team_size_min INT,
    team_size_max INT,
    solo_allowed BOOLEAN,
    team_size VARCHAR(50),

    prize_amount NUMERIC,
    prize_currency VARCHAR(10) DEFAULT 'INR',
    prize_description TEXT,
    prize TEXT,

    skills TEXT[],
    technologies TEXT[],
    tags TEXT[],

    source_site VARCHAR(50) NOT NULL,
    source_sites TEXT[],
    source_url TEXT NOT NULL,

    event_date_source JSONB,
    deadline_source JSONB,
    organizer_source JSONB,
    college_source JSONB,
    location_source JSONB,
    registration_url_source JSONB,
    team_size_source JSONB,
    prize_source JSONB,

    confidence NUMERIC(3, 2) DEFAULT 0.50,
    scraped_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ DEFAULT NOW(),
    raw_data_hash VARCHAR(64) NOT NULL,

    status VARCHAR(20) DEFAULT 'VALID',
    missing_fields TEXT[],
    validation_warnings TEXT[]
);

--------------------------------------------------------------------------------
-- 2. SAFE MIGRATION SCRIPT FOR EXISTING TABLES (Run this in Supabase SQL Editor)
--------------------------------------------------------------------------------
-- Step A: Add missing columns safely if they do not exist
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(255);
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE hackathons ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMPTZ DEFAULT NOW();

-- Step B: Populate dedupe_key for existing records using source_site and canonicalized event_url
UPDATE hackathons
SET dedupe_key = LOWER(source_site) || '|' || LOWER(REGEXP_REPLACE(event_url, '/+$', ''))
WHERE dedupe_key IS NULL OR dedupe_key = '';

-- Step C: Create Unique Index for dedupe_key (enforces deduplication without duplicate constraints)
CREATE UNIQUE INDEX IF NOT EXISTS idx_hackathons_dedupe_key ON hackathons(dedupe_key);

--------------------------------------------------------------------------------
-- 3. PERFORMANCE & QUERY INDEXES
--------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_hackathons_source_site ON hackathons(source_site);
CREATE INDEX IF NOT EXISTS idx_hackathons_start_date ON hackathons(event_start_date);
CREATE INDEX IF NOT EXISTS idx_hackathons_deadline ON hackathons(registration_deadline);
CREATE INDEX IF NOT EXISTS idx_hackathons_city ON hackathons(city);
CREATE INDEX IF NOT EXISTS idx_hackathons_country ON hackathons(country);
CREATE INDEX IF NOT EXISTS idx_hackathons_mode ON hackathons(mode);
CREATE INDEX IF NOT EXISTS idx_hackathons_confidence ON hackathons(confidence);
CREATE INDEX IF NOT EXISTS idx_hackathons_status ON hackathons(status);
