"""
Pydantic Hackathon Model defining the updated common normalized schema.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class ProvenanceInfo(BaseModel):
    type: str = Field(default="unknown", description="Source type: visible_event_page, json_ld, embedded_json, api_response, page_metadata, registration_section, unknown")
    url: Optional[str] = None
    label: Optional[str] = None
    raw_value: Optional[str] = None
    evidence_text: Optional[str] = Field(default=None, description="Snippets of text evidence extracted from source")
    selection_reason: Optional[str] = Field(default=None, description="Reason why this candidate value was chosen")
    candidate_values: List[Dict[str, Any]] = Field(default_factory=list, description="All candidate values collected from multiple sources/methods")


class Hackathon(BaseModel):
    id: str = Field(..., description="Unique canonical identifier / hash for the hackathon record")
    title: str = Field(..., description="Actual hackathon/event title")
    organizer: Optional[str] = Field(default=None, description="Organizing company/community/college (null if unknown)")
    college: Optional[str] = Field(default=None, description="Associated college/university if explicitly stated (null if unknown)")
    description: Optional[str] = Field(default=None, description="Clean readable description (null if unknown)")

    # Event Page & Classification
    page_type: str = Field(default="EVENT", description="EVENT, LISTING, CATEGORY, SEARCH, ARCHIVE, UNKNOWN")
    event_type: str = Field(default="HACKATHON", description="HACKATHON, BUILDATHON, CHALLENGE, PROBLEM_STATEMENT, PROGRAM, COMPETITION, OTHER")

    # Dates & Milestones
    event_date: Optional[str] = Field(default=None, description="Event date summary string")
    event_start_date: Optional[str] = Field(default=None, description="ISO event start date YYYY-MM-DD")
    event_end_date: Optional[str] = Field(default=None, description="ISO event end date YYYY-MM-DD")
    registration_start: Optional[str] = Field(default=None, description="ISO registration start date YYYY-MM-DD")
    registration_deadline: Optional[str] = Field(default=None, description="ISO registration deadline YYYY-MM-DD")
    submission_start: Optional[str] = Field(default=None, description="ISO submission start date YYYY-MM-DD")
    submission_deadline: Optional[str] = Field(default=None, description="ISO submission deadline YYYY-MM-DD")
    screening_start: Optional[str] = Field(default=None, description="ISO screening start date YYYY-MM-DD")
    screening_end: Optional[str] = Field(default=None, description="ISO screening end date YYYY-MM-DD")
    grand_finale_date: Optional[str] = Field(default=None, description="ISO grand finale date YYYY-MM-DD")

    event_date_raw: Optional[str] = Field(default=None, description="Raw unparsed event date string")
    deadline_raw: Optional[str] = Field(default=None, description="Raw unparsed deadline string")

    # URLs & Deduplication
    registration_url: Optional[str] = Field(default=None, description="Direct URL to register or apply")
    event_url: str = Field(..., description="Canonical public details page URL")
    dedupe_key: Optional[str] = Field(default=None, description="Stable deduplication key: <normalized_source_site>|<canonical_event_url>")

    # Location & Mode
    location: Optional[str] = Field(default=None, description="Full location text (null if unknown)")
    city: Optional[str] = Field(default=None, description="City name (null if unknown)")
    state: Optional[str] = Field(default=None, description="State/Province name (null if unknown)")
    country: Optional[str] = Field(default=None, description="Country name (null if unknown)")
    mode: str = Field(default="UNKNOWN", description="ONLINE, OFFLINE, HYBRID, UNKNOWN")

    # Eligibility & Team Size
    eligibility: Optional[str] = Field(default=None, description="Eligibility requirements/restrictions")
    team_size_min: Optional[int] = Field(default=None, description="Minimum team members")
    team_size_max: Optional[int] = Field(default=None, description="Maximum team members")
    solo_allowed: Optional[bool] = Field(default=None, description="True if solo participation is allowed")
    team_size: Optional[str] = Field(default=None, description="Formatted team size string e.g. 2-4")

    # Prizes
    prize_amount: Optional[float] = Field(default=None, description="Numerical prize amount")
    prize_currency: Optional[str] = Field(default=None, description="Currency ISO code (INR, USD, EUR, GBP)")
    prize_description: Optional[str] = Field(default=None, description="Text description of prizes")
    prize: Optional[str] = Field(default=None, description="Formatted prize string")

    # Tags & Categories
    skills: List[str] = Field(default_factory=list, description="Target skills required")
    technologies: List[str] = Field(default_factory=list, description="Technologies/frameworks used")
    tags: List[str] = Field(default_factory=list, description="Category tags")

    # Sources
    source_site: str = Field(..., description="Origin site: devfolio, unstop, sih, hackerearth, knowafest, devpost")
    source_sites: List[str] = Field(default_factory=list, description="All origin sites if merged from multiple sources")
    source_url: str = Field(..., description="Original URL scraped from")

    # Provenance Tracking
    event_date_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    deadline_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    organizer_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    college_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    location_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    registration_url_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    team_size_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    prize_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())

    # Confidence & Hash
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Evidence-based confidence score 0.0 to 1.0")
    scraped_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO UTC scraping timestamp")
    raw_data_hash: str = Field(..., description="SHA-256 hash of raw extracted data")

    # Status & Audit
    status: str = Field(default="VALID", description="DUPLICATE, PAST, CONFLICT, INVALID, INCOMPLETE, VALID")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing optional/essential fields")
    validation_warnings: List[str] = Field(default_factory=list, description="List of non-fatal validation warnings")

    @model_validator(mode="after")
    def populate_source_sites(self):
        if not self.source_sites and self.source_site:
            self.source_sites = [self.source_site]
        return self
