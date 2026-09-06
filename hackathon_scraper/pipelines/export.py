"""
Export pipeline writing raw, partitioned, and normalized JSON, JSONL, CSV artifacts and validation reports.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List
from hackathon_scraper.config import CURRENT_DATE, NORMALIZED_OUTPUT_DIR, OUTPUT_DIR, RAW_OUTPUT_DIR
from hackathon_scraper.extractors.dates import is_past_event
from hackathon_scraper.models.hackathon import Hackathon


def export_raw_records(source_name: str, raw_records: List[Dict[str, Any]]) -> Path:
    """Exports raw dictionary payload per source to output/raw/{source}_raw.json."""
    out_path = RAW_OUTPUT_DIR / f"{source_name}_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw_records, f, indent=2, default=str)
    return out_path


def export_normalized_records(records: List[Hackathon]) -> Dict[str, Path]:
    """
    Exports normalized Hackathon models to JSON, JSONL, CSV, partitioned JSONs,
    and generates output/validation_report.json.
    """
    all_json_path = NORMALIZED_OUTPUT_DIR / "all.json"
    hackathons_json_path = NORMALIZED_OUTPUT_DIR / "hackathons.json"  # Alias
    upcoming_json_path = NORMALIZED_OUTPUT_DIR / "upcoming.json"
    incomplete_json_path = NORMALIZED_OUTPUT_DIR / "incomplete.json"
    invalid_json_path = NORMALIZED_OUTPUT_DIR / "invalid.json"
    past_json_path = NORMALIZED_OUTPUT_DIR / "past.json"
    conflicts_json_path = NORMALIZED_OUTPUT_DIR / "conflicts.json"
    duplicates_json_path = NORMALIZED_OUTPUT_DIR / "duplicates.json"
    report_json_path = OUTPUT_DIR / "validation_report.json"

    jsonl_path = NORMALIZED_OUTPUT_DIR / "hackathons.jsonl"
    csv_path = NORMALIZED_OUTPUT_DIR / "hackathons.csv"

    dicts = [r.model_dump() for r in records]

    # Partition lists
    upcoming_records = []
    incomplete_records = []
    invalid_records = []
    past_records = []
    conflicts_records = []
    duplicates_records = []

    for r, d in zip(records, dicts):
        st = r.status.upper()
        if st == "DUPLICATE":
            duplicates_records.append(d)
        elif st == "PAST":
            past_records.append(d)
        elif st == "CONFLICT":
            conflicts_records.append(d)
        elif st == "INVALID":
            invalid_records.append(d)
        elif st == "INCOMPLETE":
            incomplete_records.append(d)
        elif st == "VALID":
            # Strict upcoming rule: status == VALID AND page_type == EVENT AND not past
            if r.page_type == "EVENT" and not is_past_event(r.event_end_date, r.event_start_date):
                upcoming_records.append(d)
            else:
                past_records.append(d)

    # Helper for JSON saving
    def _save_json(filepath: Path, data: List[Dict[str, Any]]):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    _save_json(all_json_path, dicts)
    _save_json(hackathons_json_path, dicts)
    _save_json(upcoming_json_path, upcoming_records)
    _save_json(incomplete_json_path, incomplete_records)
    _save_json(invalid_json_path, invalid_records)
    _save_json(past_json_path, past_records)
    _save_json(conflicts_json_path, conflicts_records)
    _save_json(duplicates_json_path, duplicates_records)

    # Save JSONL
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for d in dicts:
            f.write(json.dumps(d, default=str) + "\n")

    # Save CSV
    if dicts:
        flat_dicts = []
        for d in dicts:
            flat = d.copy()
            for k in ["skills", "technologies", "tags", "source_sites", "missing_fields", "validation_warnings"]:
                if isinstance(flat.get(k), list):
                    flat[k] = ", ".join(flat[k])
            for k in ["event_date_source", "deadline_source", "organizer_source", "college_source", "location_source", "registration_url_source", "team_size_source", "prize_source"]:
                if isinstance(flat.get(k), dict):
                    flat[k] = json.dumps(flat[k])
            flat_dicts.append(flat)

        headers = list(flat_dicts[0].keys())
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(flat_dicts)

    # Calculate Field Coverage Statistics
    total_count = len(records)
    coverage = {}
    if total_count > 0:
        fields_to_track = [
            "title", "organizer", "college", "description", "event_start_date", "event_end_date",
            "registration_deadline", "location", "city", "state", "mode", "team_size",
            "team_size_min", "team_size_max", "prize", "prize_amount", "eligibility",
            "registration_url", "skills", "technologies"
        ]
        for field in fields_to_track:
            present = sum(
                1 for r in records
                if getattr(r, field, None) not in (None, "", [], {})
            )
            coverage[field] = {
                "count": present,
                "percentage": round((present / total_count) * 100, 1)
            }

    # Generate Validation Report
    report = {
        "execution_date": str(CURRENT_DATE),
        "total_records_processed": total_count,
        "summary_counts": {
            "valid_upcoming": len(upcoming_records),
            "incomplete": len(incomplete_records),
            "invalid": len(invalid_records),
            "past": len(past_records),
            "conflicts": len(conflicts_records),
            "duplicates": len(duplicates_records),
        },
        "field_coverage": coverage
    }
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    # Save DataFrame CSV Exports
    try:
        import pandas as pd
        df_all = pd.json_normalize(dicts)
        df_upcoming = pd.json_normalize(upcoming_records)
        df_all.to_csv(NORMALIZED_OUTPUT_DIR / "all_dataframe.csv", index=False)
        df_upcoming.to_csv(NORMALIZED_OUTPUT_DIR / "upcoming_dataframe.csv", index=False)
    except Exception:
        pass


    return {
        "all_json": all_json_path,
        "upcoming_json": upcoming_json_path,
        "report_json": report_json_path,
        "jsonl": jsonl_path,
        "csv": csv_path,
        "upcoming_dataframe_csv": NORMALIZED_OUTPUT_DIR / "upcoming_dataframe.csv",
        "all_dataframe_csv": NORMALIZED_OUTPUT_DIR / "all_dataframe.csv",
    }

