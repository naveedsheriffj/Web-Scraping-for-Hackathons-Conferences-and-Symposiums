"""
Scrapers module initializers.
"""

from hackathon_scraper.scrapers.base_scraper import BaseHackathonScraper
from hackathon_scraper.scrapers.devfolio import DevfolioScraper
from hackathon_scraper.scrapers.unstop import UnstopScraper
from hackathon_scraper.scrapers.sih import SIHScraper
from hackathon_scraper.scrapers.hackerearth import HackerEarthScraper
from hackathon_scraper.scrapers.knowafest import KnowAFestScraper
from hackathon_scraper.scrapers.devpost import DevpostScraper

SCRAPER_REGISTRY = {
    "devfolio": DevfolioScraper,
    "unstop": UnstopScraper,
    "sih": SIHScraper,
    "hackerearth": HackerEarthScraper,
    "knowafest": KnowAFestScraper,
    "devpost": DevpostScraper,
}

__all__ = [
    "BaseHackathonScraper",
    "DevfolioScraper",
    "UnstopScraper",
    "SIHScraper",
    "HackerEarthScraper",
    "KnowAFestScraper",
    "DevpostScraper",
    "SCRAPER_REGISTRY",
]
