"""
Deduplication & Cross-Source Record Merging Pipeline.
"""

from typing import Dict, List, Tuple
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.models.hackathon import Hackathon, ProvenanceInfo


def merge_hackathon_records(primary: Hackathon, secondary: Hackathon) -> Hackathon:
    """
    Merges two matching hackathon records, preferring non-empty/higher confidence field values
    while recording candidate_values and selection_reason in provenance info when conflicts occur.
    """
    # Merge source_sites
    all_sources = list(dict.fromkeys(primary.source_sites + secondary.source_sites))
    primary.source_sites = all_sources

    # Check for conflicts in essential fields (e.g. event_start_date or registration_deadline)
    if primary.event_start_date and secondary.event_start_date and primary.event_start_date != secondary.event_start_date:
        # Conflicting event dates
        prov = primary.event_date_source if isinstance(primary.event_date_source, ProvenanceInfo) else ProvenanceInfo()
        prov.candidate_values.append({
            "source_site": secondary.source_site,
            "event_start_date": secondary.event_start_date,
            "event_end_date": secondary.event_end_date
        })
        prov.selection_reason = f"Primary source ({primary.source_site}) value retained; secondary source ({secondary.source_site}) value recorded in candidate_values."
        primary.event_date_source = prov
        primary.validation_warnings.append(
            f"Date conflict between {primary.source_site} ({primary.event_start_date}) and {secondary.source_site} ({secondary.event_start_date})"
        )

    if primary.registration_deadline and secondary.registration_deadline and primary.registration_deadline != secondary.registration_deadline:
        prov = primary.deadline_source if isinstance(primary.deadline_source, ProvenanceInfo) else ProvenanceInfo()
        prov.candidate_values.append({
            "source_site": secondary.source_site,
            "registration_deadline": secondary.registration_deadline
        })
        prov.selection_reason = f"Primary source ({primary.source_site}) deadline retained; secondary source ({secondary.source_site}) deadline recorded in candidate_values."
        primary.deadline_source = prov

    # Prefer non-null fields
    if not primary.description and secondary.description:
        primary.description = secondary.description
    if not primary.organizer and secondary.organizer:
        primary.organizer = secondary.organizer
        primary.organizer_source = secondary.organizer_source
    if not primary.college and secondary.college:
        primary.college = secondary.college
        primary.college_source = secondary.college_source
    if not primary.registration_deadline and secondary.registration_deadline:
        primary.registration_deadline = secondary.registration_deadline
        primary.deadline_source = secondary.deadline_source
    if not primary.event_start_date and secondary.event_start_date:
        primary.event_start_date = secondary.event_start_date
        primary.event_end_date = secondary.event_end_date
        primary.event_date_source = secondary.event_date_source

    # Take maximum confidence score
    primary.confidence = max(primary.confidence, secondary.confidence)
    return primary


def deduplicate_records(records: List[Hackathon]) -> Tuple[List[Hackathon], int]:
    """
    Deduplicates a list of normalized Hackathon models based on dedupe_key, canonical URL, or fingerprint ID.
    Returns (deduplicated_list, duplicate_count).
    """
    unique_map: Dict[str, Hackathon] = {}
    url_map: Dict[str, str] = {}  # canonical_url -> record_id
    key_map: Dict[str, str] = {}  # dedupe_key -> record_id
    duplicate_count = 0

    for rec in records:
        canonical_url = canonicalize_url(rec.event_url)
        dedupe_key = rec.dedupe_key or (f"{rec.source_site.lower()}|{canonical_url}" if canonical_url else None)
        target_id = None

        if rec.id in unique_map:
            target_id = rec.id
        elif dedupe_key and dedupe_key in key_map:
            target_id = key_map[dedupe_key]
        elif canonical_url and canonical_url in url_map:
            target_id = url_map[canonical_url]

        if target_id and target_id in unique_map:
            duplicate_count += 1
            existing = unique_map[target_id]
            unique_map[target_id] = merge_hackathon_records(existing, rec)
        else:
            unique_map[rec.id] = rec
            if canonical_url:
                url_map[canonical_url] = rec.id
            if dedupe_key:
                key_map[dedupe_key] = rec.id

    return list(unique_map.values()), duplicate_count
