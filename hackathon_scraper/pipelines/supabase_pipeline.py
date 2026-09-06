"""
Supabase Database Pipeline for remote incremental sync.
"""

from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import urllib.request
import urllib.error

# Resolve sys.path for standalone execution
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from hackathon_scraper.config import NORMALIZED_OUTPUT_DIR, SUPABASE_KEY, SUPABASE_URL
from hackathon_scraper.extractors.urls import canonicalize_url
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.utils.logging import logger


def get_supabase_credentials() -> Tuple[str, str]:
    """Retrieves Supabase URL and Key from environment or config defaults."""
    url = os.getenv("SUPABASE_URL") or SUPABASE_URL
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY") or SUPABASE_KEY
    return url, key


def fetch_existing_supabase_records(url: str, key: str) -> List[Dict[str, Any]]:
    """Fetches all existing records from Supabase hackathons table."""
    try:
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "User-Agent": "HackathonScraper/1.0",
        }
        endpoint = f"{url.rstrip('/')}/rest/v1/hackathons?select=*"
        req = urllib.request.Request(endpoint, headers=headers, method="GET")

        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                logger.info(f"[SUPABASE] Fetched {len(data)} existing records from database.")
                return data
    except Exception as e:
        logger.warning(f"[SUPABASE] Could not fetch existing records: {e}")
    return []


def is_empty_value(val: Any) -> bool:
    """Checks if a field value is considered null/empty."""
    if val is None:
        return True
    if isinstance(val, str) and val.strip() == "":
        return True
    if isinstance(val, (list, dict)) and len(val) == 0:
        return True
    return False


def build_dedupe_key(source_site: str, event_url: str) -> str:
    """Generates canonical dedupe_key in format <normalized_source_site>|<canonical_event_url>."""
    norm_site = (source_site or "unknown").strip().lower()
    canonical_url = canonicalize_url(event_url) or (event_url or "").strip()
    return f"{norm_site}|{canonical_url}"


def sync_dicts_to_supabase(dicts: List[Dict[str, Any]]) -> Tuple[bool, str, Dict[str, int]]:
    """
    Syncs normalized dictionaries to Supabase hackathons table with:
    - Deduplication by dedupe_key and canonical ID
    - Preservation of existing reliable values when new scrape temporarily returns null
    - Dynamic adaptation to existing database columns
    - Statistics tracking (scraped, new, updated, unchanged)
    """
    url, key = get_supabase_credentials()
    stats = {"scraped": len(dicts), "new": 0, "updated": 0, "unchanged": 0}

    if not url or not key:
        msg = "Offline mode - SUPABASE_URL and SUPABASE_KEY not configured."
        logger.info(f"[SUPABASE] {msg}")
        return False, msg, stats

    # 1. Fetch existing database records
    existing_records = fetch_existing_supabase_records(url, key)
    existing_map: Dict[str, Dict[str, Any]] = {}
    known_db_columns: Set[str] = set()

    if existing_records:
        known_db_columns = set(existing_records[0].keys())

    for item in existing_records:
        rec_id = item.get("id")
        rec_key = item.get("dedupe_key")
        if not rec_key:
            rec_key = build_dedupe_key(item.get("source_site", ""), item.get("event_url", ""))
            item["dedupe_key"] = rec_key

        if rec_key:
            existing_map[rec_key] = item
        if rec_id:
            existing_map[rec_id] = item

    now_iso = datetime.now(timezone.utc).isoformat()
    raw_merged_list: List[Dict[str, Any]] = []

    # 2. Perform field-level merging with null preservation
    for new_item in dicts:
        d_key = new_item.get("dedupe_key") or build_dedupe_key(new_item.get("source_site", ""), new_item.get("event_url", ""))
        new_item["dedupe_key"] = d_key
        rec_id = new_item.get("id")

        existing = existing_map.get(d_key) or (existing_map.get(rec_id) if rec_id else None)

        if existing:
            merged = dict(existing)
            has_substantive_change = False

            for k, new_val in new_item.items():
                old_val = existing.get(k)
                if is_empty_value(new_val):
                    # PRESERVE EXISTING GOOD DATA
                    if not is_empty_value(old_val):
                        merged[k] = old_val
                    else:
                        merged[k] = new_val
                else:
                    if old_val != new_val:
                        has_substantive_change = True
                    merged[k] = new_val

            # Timestamps if supported in remote DB schema
            if "last_scraped_at" in known_db_columns:
                merged["last_scraped_at"] = now_iso
            if "created_at" in known_db_columns:
                merged["created_at"] = existing.get("created_at") or now_iso

            if has_substantive_change:
                if "updated_at" in known_db_columns:
                    merged["updated_at"] = now_iso
                stats["updated"] += 1
            else:
                if "updated_at" in known_db_columns:
                    merged["updated_at"] = existing.get("updated_at") or now_iso
                stats["unchanged"] += 1

            raw_merged_list.append(merged)
        else:
            # New event
            if "created_at" in known_db_columns:
                new_item["created_at"] = now_iso
            if "updated_at" in known_db_columns:
                new_item["updated_at"] = now_iso
            if "last_scraped_at" in known_db_columns:
                new_item["last_scraped_at"] = now_iso

            stats["new"] += 1
            raw_merged_list.append(new_item)

    if not raw_merged_list:
        return True, "No records to sync.", stats

    # 3. Filter keys strictly to match known remote DB schema
    records_to_upsert: List[Dict[str, Any]] = []
    for item in raw_merged_list:
        if known_db_columns:
            # Exclude keys that do not exist in remote DB schema yet
            filtered = {k: v for k, v in item.items() if k in known_db_columns}
            records_to_upsert.append(filtered)
        else:
            records_to_upsert.append(item)

    # 4. PostgREST UPSERT
    try:
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates",
            "User-Agent": "HackathonScraper/1.0",
        }
        endpoint = f"{url.rstrip('/')}/rest/v1/hackathons"
        payload_bytes = json.dumps(records_to_upsert, default=str).encode("utf-8")

        req = urllib.request.Request(endpoint, data=payload_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as res:
            status_code = res.status
            response_text = res.read().decode("utf-8")

        if status_code in (200, 201, 204):
            msg = f"Synced {len(records_to_upsert)} records to Supabase (New: {stats['new']}, Updated: {stats['updated']}, Unchanged: {stats['unchanged']})."
            logger.info(f"[SUPABASE] {msg}")
            return True, msg, stats
        else:
            msg = f"Sync returned status {status_code}: {response_text}"
            logger.warning(f"[SUPABASE] {msg}")
            return False, msg, stats

    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        msg = f"HTTP {err.code} Error syncing to Supabase: {error_body or err.reason}"
        logger.warning(f"[SUPABASE] {msg}")
        return False, msg, stats
    except Exception as e:
        msg = f"Error syncing to Supabase: {e}"
        logger.warning(f"[SUPABASE] {msg}")
        return False, msg, stats


def sync_to_supabase(records: List[Hackathon]) -> Tuple[bool, str, Dict[str, int]]:
    """Syncs normalized Hackathon objects to Supabase."""
    dicts = [r.model_dump() for r in records]
    return sync_dicts_to_supabase(dicts)


def push_json_to_supabase(filename: str = "all.json") -> Tuple[bool, str, Dict[str, int]]:
    """Reads normalized JSON output file and pushes all records to Supabase."""
    json_file = NORMALIZED_OUTPUT_DIR / filename
    if not json_file.exists():
        return False, f"File {json_file} does not exist. Run scraper first.", {"scraped": 0, "new": 0, "updated": 0, "unchanged": 0}

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"[SUPABASE PUSH] Read {len(data)} records from {json_file}")
    success, msg, stats = sync_dicts_to_supabase(data)
    print(f"[SUPABASE PUSH] Result: {msg}")
    return success, msg, stats


if __name__ == "__main__":
    push_json_to_supabase("all.json")
