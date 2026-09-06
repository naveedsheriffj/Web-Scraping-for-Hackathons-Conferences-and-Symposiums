"""
CLI Entrypoint for running hackathon scrapers with automated database sync & run logging.
"""

import argparse
from datetime import datetime, timezone
import sys
from typing import Dict, List
from hackathon_scraper.config import MAX_EVENTS
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.pipelines.deduplicate import deduplicate_records
from hackathon_scraper.pipelines.export import export_normalized_records, export_raw_records
from hackathon_scraper.pipelines.normalize import normalize_record
from hackathon_scraper.pipelines.supabase_pipeline import sync_to_supabase
from hackathon_scraper.scrapers import SCRAPER_REGISTRY
from hackathon_scraper.utils.logging import logger


def run_pipeline(sources: List[str], max_events: int = MAX_EVENTS):
    run_started_at = datetime.now(timezone.utc).isoformat()
    logger.info("==================================================")
    logger.info("  STARTING HACKATHON SCRAPER PIPELINE")
    logger.info(f"  Start Time: {run_started_at}")
    logger.info("==================================================")

    all_normalized: List[Hackathon] = []
    summary_reports = []
    
    total_raw_scraped = 0
    total_duplicates = 0
    invalid_records = 0
    conflict_records = 0
    failed_sources = 0

    for source_key in sources:
        scraper_cls = SCRAPER_REGISTRY.get(source_key)
        if not scraper_cls:
            logger.warning(f"Unknown source key: {source_key}")
            continue

        logger.info(f"\n---> Scraping source: {source_key.upper()}")

        try:
            scraper = scraper_cls()
            # Execute Stage 1 & 2
            raw_records = scraper.run(limit=max_events)
            export_raw_records(source_key, raw_records)
            total_raw_scraped += len(raw_records)

            # Normalize records
            normalized_source: List[Hackathon] = []
            is_structured = source_key in ("devfolio", "unstop")

            for r in raw_records:
                try:
                    norm = normalize_record(r, is_structured=is_structured)
                    normalized_source.append(norm)
                except Exception as e:
                    logger.error(f"[{source_key.upper()}] Error normalizing record: {e}")

            # Deduplicate per-source
            dedup_source, dup_cnt = deduplicate_records(normalized_source)
            all_normalized.extend(dedup_source)
            total_duplicates += dup_cnt

            st_counts = {}
            for rec in dedup_source:
                st = rec.status
                st_counts[st] = st_counts.get(st, 0) + 1

            invalid_records += st_counts.get("INVALID", 0)
            conflict_records += st_counts.get("CONFLICT", 0)

            report = (
                f"SOURCE: {source_key.upper()}\n"
                f"  URL: {scraper.base_url}\n"
                f"  EVENTS DISCOVERED: {len(raw_records)}\n"
                f"  VALID UPCOMING: {st_counts.get('VALID', 0)}\n"
                f"  INCOMPLETE: {st_counts.get('INCOMPLETE', 0)}\n"
                f"  PAST: {st_counts.get('PAST', 0)}\n"
                f"  INVALID: {st_counts.get('INVALID', 0)}\n"
                f"  CONFLICT: {st_counts.get('CONFLICT', 0)}\n"
                f"  DUPLICATES: {dup_cnt}"
            )
            summary_reports.append(report)
            logger.info(
                f"[{source_key.upper()}] Valid Upcoming: {st_counts.get('VALID', 0)} | "
                f"Past: {st_counts.get('PAST', 0)} | Incomplete: {st_counts.get('INCOMPLETE', 0)} | "
                f"Duplicates: {dup_cnt}"
            )

        except Exception as e:
            failed_sources += 1
            logger.error(f"[{source_key.upper()}] FAILED TO SCRAPE SOURCE: {e}", exc_info=True)
            logger.warning(f"[{source_key.upper()}] Continuing pipeline for other sources without touching existing database records.")

    # Cross-source deduplication
    final_records, cross_source_dups = deduplicate_records(all_normalized)
    total_duplicates += cross_source_dups

    # Export results
    export_paths = export_normalized_records(final_records)
    
    # Sync to Supabase
    sync_success, sync_msg, sync_stats = sync_to_supabase(final_records)

    run_finished_at = datetime.now(timezone.utc).isoformat()

    # Formatted Scraper Run Summary Logging (Requirement 10)
    print("\n=====================================")
    print("HACKATHON SCRAPER RUN")
    print("=====================================")
    print(f"Sources: {len(sources)}")
    print(f"Scraped: {total_raw_scraped}")
    print(f"New: {sync_stats.get('new', 0)}")
    print(f"Updated: {sync_stats.get('updated', 0)}")
    print(f"Unchanged: {sync_stats.get('unchanged', 0)}")
    print(f"Duplicates: {total_duplicates}")
    print(f"Invalid: {invalid_records}")
    print(f"Conflicts: {conflict_records}")
    print(f"Failed sources: {failed_sources}")
    print("=====================================\n")

    logger.info("\n==================================================")
    logger.info("  FINAL PIPELINE SUMMARY")
    logger.info("==================================================")
    for r in summary_reports:
        logger.info("\n" + r)

    logger.info("--------------------------------------------------")
    logger.info(f"TOTAL PROCESSED: {len(final_records)}")
    logger.info(f"TOTAL CROSS-SOURCE DUPLICATES MERGED: {cross_source_dups}")
    logger.info(f"ALL RECORDS SAVED TO: {export_paths['all_json']}")
    logger.info(f"VALID UPCOMING SAVED TO: {export_paths['upcoming_json']}")
    logger.info(f"VALIDATION REPORT SAVED TO: {export_paths['report_json']}")
    logger.info(f"SUPABASE SYNC RESULT: {sync_msg}")
    logger.info("==================================================")

    return final_records


def main():
    parser = argparse.ArgumentParser(description="Hackathon Scraper CLI")
    parser.add_argument(
        "--source",
        type=str,
        default="all",
        choices=list(SCRAPER_REGISTRY.keys()) + ["all"],
        help="Target scraper source or 'all' to run all scrapers",
    )
    parser.add_argument(
        "--max-events",
        type=int,
        default=MAX_EVENTS,
        help="Maximum events to scrape per source",
    )
    args = parser.parse_args()

    if args.source == "all":
        sources = list(SCRAPER_REGISTRY.keys())
    else:
        sources = [args.source]

    run_pipeline(sources=sources, max_events=args.max_events)


if __name__ == "__main__":
    main()
