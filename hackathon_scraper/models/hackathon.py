"""
Pydantic Hackathon Model defining the simplified 33-field schema.
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
    # 1. Identity
    id: str = Field(..., description="Unique canonical identifier / hash for the hackathon record")
    title: str = Field(..., description="Actual hackathon/event title")
    source_site: str = Field(..., description="Origin site: devfolio, unstop, sih, hackerearth, knowafest, devpost")
    event_url: str = Field(..., description="Canonical public details page URL")
    registration_url: Optional[str] = Field(default=None, description="Direct URL to register or apply")
    event_type: str = Field(default="HACKATHON", description="HACKATHON, BUILDATHON, CHALLENGE, PROBLEM_STATEMENT, PROGRAM, COMPETITION, OTHER")

    # 2. Event Details
    start_date: Optional[str] = Field(default=None, description="ISO event start date YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="ISO event end date YYYY-MM-DD")
    mode: str = Field(default="UNKNOWN", description="ONLINE, OFFLINE, HYBRID, UNKNOWN")
    location: Optional[str] = Field(default=None, description="Full location text (null if unknown)")
    city: Optional[str] = Field(default=None, description="City name (null if unknown)")
    state: Optional[str] = Field(default=None, description="State/Province name (null if unknown)")
    country: Optional[str] = Field(default="India", description="Country name (null if unknown)")

    # 3. Organization
    organizer: Optional[str] = Field(default=None, description="Organizing company/community/college (null if unknown)")
    college: Optional[str] = Field(default=None, description="Associated college/university if explicitly stated (null if unknown)")

    # 4. Participation
    eligibility: Optional[str] = Field(default=None, description="Eligibility requirements/restrictions")
    team_size_min: Optional[int] = Field(default=None, description="Minimum team members")
    team_size_max: Optional[int] = Field(default=None, description="Maximum team members")
    solo_allowed: Optional[bool] = Field(default=None, description="True if solo participation is allowed")

    # 5. Prizes
    prize_amount: Optional[float] = Field(default=None, description="Numerical prize amount")
    prize_currency: Optional[str] = Field(default="INR", description="Currency ISO code (INR, USD, EUR, GBP)")
    prize_description: Optional[str] = Field(default=None, description="Text description of prizes")

    # 6. Deadlines
    registration_start: Optional[str] = Field(default=None, description="ISO registration start date YYYY-MM-DD")
    registration_deadline: Optional[str] = Field(default=None, description="ISO registration deadline YYYY-MM-DD")
    submission_deadline: Optional[str] = Field(default=None, description="ISO submission deadline YYYY-MM-DD")
    other_deadlines: List[Dict[str, str]] = Field(default_factory=list, description="Structured milestone deadlines e.g. [{'name': 'PPT Submission', 'date': '2026-09-09'}]")

    # 7. Content
    description: Optional[str] = Field(default=None, description="Clean readable description (null if unknown)")
    themes: List[str] = Field(default_factory=list, description="Category/domain themes")
    technologies: List[str] = Field(default_factory=list, description="Technologies/frameworks used")

    # 8. Database Metadata
    dedupe_key: Optional[str] = Field(default=None, description="Stable deduplication key: <normalized_source_site>|<canonical_event_url>")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of creation in database")
    updated_at: Optional[str] = Field(default=None, description="ISO timestamp of last database update")
    last_scraped_at: Optional[str] = Field(default=None, description="ISO timestamp when last verified by scraper")

    # Internal Validation & Quality Control (used internally, omitted from final DB dump)
    page_type: str = Field(default="EVENT", description="Internal classification: EVENT, CATEGORY, LISTING, OTHER")
    status: str = Field(default="VALID", description="DUPLICATE, PAST, CONFLICT, INVALID, INCOMPLETE, VALID")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Evidence-based confidence score 0.0 to 1.0")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing optional/essential fields")
    validation_warnings: List[str] = Field(default_factory=list, description="List of non-fatal validation warnings")
    raw_data_hash: Optional[str] = Field(default=None, description="SHA-256 hash of raw extracted data")

    # Internal Provenance Information
    event_date_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    deadline_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    organizer_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    college_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    location_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())
    registration_url_source: Union[ProvenanceInfo, Dict[str, Any]] = Field(default_factory=lambda: ProvenanceInfo())

    _source_sites: Optional[List[str]] = None

    @model_validator(mode="before")
    @classmethod
    def handle_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "event_start_date" in data and "start_date" not in data:
                data["start_date"] = data.pop("event_start_date")
            if "event_end_date" in data and "end_date" not in data:
                data["end_date"] = data.pop("event_end_date")
            if "event_date" in data and "start_date" not in data:
                val = data.pop("event_date")
                if val and not data.get("start_date"):
                    data["start_date"] = val
            if "tags" in data and "themes" not in data:
                data["themes"] = data.pop("tags")
            if "skills" in data and "technologies" not in data:
                data["technologies"] = data.pop("skills")
        return data

    # Backward-Compatibility Aliases
    @property
    def event_start_date(self) -> Optional[str]:
        return self.start_date

    @event_start_date.setter
    def event_start_date(self, value: Optional[str]):
        self.start_date = value

    @property
    def event_end_date(self) -> Optional[str]:
        return self.end_date

    @event_end_date.setter
    def event_end_date(self, value: Optional[str]):
        self.end_date = value

    @property
    def event_date(self) -> Optional[str]:
        return self.start_date

    @event_date.setter
    def event_date(self, value: Optional[str]):
        if value and not self.start_date:
            self.start_date = value

    @property
    def team_size(self) -> Optional[str]:
        if self.team_size_min is not None and self.team_size_max is not None:
            return f"{self.team_size_min}-{self.team_size_max}"
        return None

    @property
    def prize(self) -> Optional[str]:
        return self.prize_description or (str(self.prize_amount) if self.prize_amount is not None else None)

    @property
    def tags(self) -> List[str]:
        return self.themes

    @tags.setter
    def tags(self, value: List[str]):
        self.themes = value or []

    @property
    def skills(self) -> List[str]:
        return self.technologies

    @skills.setter
    def skills(self, value: List[str]):
        self.technologies = value or []

    @property
    def source_sites(self) -> List[str]:
        if self._source_sites is None:
            self._source_sites = [self.source_site]
        return self._source_sites

    @source_sites.setter
    def source_sites(self, value: List[str]):
        self._source_sites = value or []

    def to_db_dict(self) -> Dict[str, Any]:
        """Returns clean dictionary containing ONLY the target 33 database fields."""
        return {
            "id": self.id,
            "title": self.title,
            "source_site": self.source_site,
            "event_url": self.event_url,
            "registration_url": self.registration_url,
            "event_type": self.event_type,

            "start_date": self.start_date,
            "end_date": self.end_date,
            "mode": self.mode,
            "location": self.location,
            "city": self.city,
            "state": self.state,
            "country": self.country,

            "organizer": self.organizer,
            "college": self.college,

            "eligibility": self.eligibility,
            "team_size_min": self.team_size_min,
            "team_size_max": self.team_size_max,
            "solo_allowed": self.solo_allowed,

            "prize_amount": self.prize_amount,
            "prize_currency": self.prize_currency,
            "prize_description": self.prize_description,

            "registration_start": self.registration_start,
            "registration_deadline": self.registration_deadline,
            "submission_deadline": self.submission_deadline,
            "other_deadlines": self.other_deadlines if self.other_deadlines else None,

            "description": self.description,
            "themes": self.themes if self.themes else None,
            "technologies": self.technologies if self.technologies else None,

            "dedupe_key": self.dedupe_key,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_scraped_at": self.last_scraped_at,
        }
