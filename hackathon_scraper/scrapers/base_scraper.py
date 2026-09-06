"""
Abstract Base Hackathon Scraper establishing standard two-stage scraping lifecycle.
"""

from abc import ABC, abstractmethod
import time
from typing import Any, Dict, List, Optional
from scrapling import Fetcher, DynamicFetcher, StealthyFetcher
from hackathon_scraper.config import MAX_EVENTS, REQUEST_DELAY, TIMEOUT
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.utils.logging import logger


class BaseHackathonScraper(ABC):
    """Base class for all site-specific hackathon scrapers."""

    source_name: str = "base"
    base_url: str = ""

    def __init__(self, delay: float = REQUEST_DELAY, timeout: int = TIMEOUT):
        self.delay = delay
        self.timeout = timeout
        self.fetcher = Fetcher()
        self.dynamic_fetcher = DynamicFetcher()
        self.stealthy_fetcher = StealthyFetcher()

    def _sleep(self):
        if self.delay > 0:
            time.sleep(self.delay)

    @abstractmethod
    def discover(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Stage 1: Discover listing cards/APIs and return basic event data dicts."""
        pass

    @abstractmethod
    def fetch_details(self, event_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 2: Visit detail page/fetch detailed payload for a single event."""
        pass

    def run(self, limit: int = MAX_EVENTS) -> List[Dict[str, Any]]:
        """Executes full two-stage discovery & detail extraction pipeline."""
        logger.info(f"[{self.source_name.upper()}] Starting scraper (limit={limit})...")
        
        # Stage 1: Discovery
        try:
            discovered = self.discover(limit=limit)
        except Exception as e:
            logger.error(f"[{self.source_name.upper()}] Discovery failed: {e}")
            discovered = []

        logger.info(f"[{self.source_name.upper()}] discovered {len(discovered)} events")

        detailed_records: List[Dict[str, Any]] = []
        processed_count = 0

        # Stage 2: Detail Extraction
        for item in discovered:
            if processed_count >= limit:
                break
            try:
                self._sleep()
                detailed = self.fetch_details(item)
                if detailed:
                    detailed_records.append(detailed)
                    processed_count += 1
            except Exception as e:
                logger.error(f"[{self.source_name.upper()}] Detail fetch failed for {item.get('event_url', 'unknown')}: {e}")
                # Save partial data if available
                detailed_records.append(item)
                processed_count += 1

        logger.info(f"[{self.source_name.upper()}] processed {processed_count} detail pages")
        return detailed_records
