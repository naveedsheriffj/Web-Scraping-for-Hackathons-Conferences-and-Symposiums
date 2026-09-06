"""
Pipelines initializers.
"""

from hackathon_scraper.pipelines.normalize import normalize_record
from hackathon_scraper.pipelines.deduplicate import deduplicate_records
from hackathon_scraper.pipelines.export import export_raw_records, export_normalized_records
from hackathon_scraper.pipelines.supabase_pipeline import sync_to_supabase

__all__ = [
    "normalize_record",
    "deduplicate_records",
    "export_raw_records",
    "export_normalized_records",
    "sync_to_supabase",
]
