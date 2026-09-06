import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, ".")

from hackathon_scraper.scrapers.devfolio import DevfolioScraper
from hackathon_scraper.scrapers.unstop import UnstopScraper
from hackathon_scraper.models.hackathon import Hackathon
from hackathon_scraper.validators.hackathon_validator import validate_hackathon, calculate_confidence
from hackathon_scraper.utils.hashing import compute_fingerprint, compute_raw_hash

dev_scraper = DevfolioScraper()
unstop_scraper = UnstopScraper()

targets = [
    # Devfolio
    {"type": "devfolio", "url": "https://hackrit2026.devfolio.co/", "title": "Hackrit"},
    {"type": "devfolio", "url": "https://metamorph-2.devfolio.co/", "title": "Metamorph 2.0"},
    {"type": "devfolio", "url": "https://webcraft24.devfolio.co/", "title": "WebCraft24"},
    # Unstop
    {"type": "unstop", "url": "https://unstop.com/hackathons/hackcelestial-30-pillai-university-navi-mumbai-1737808", "title": "HackCelestial 3.0"},
    {"type": "unstop", "url": "https://unstop.com/hackathons/singularity-hackathon-aj-institute-of-engineering-and-technology-ajiet-mangalore-karnataka-1735180", "title": "Singularity Hackathon"},
    {"type": "unstop", "url": "https://unstop.com/competitions/code-clash-rv-university-rvu-bangalore-1749224", "title": "Code Clash"},
]

results = []

for t in targets:
    print(f"\n==================== PROCESSING: {t['title']} ({t['url']}) ====================")
    if t["type"] == "devfolio":
        raw = dev_scraper.fetch_details({"event_url": t["url"], "source_url": t["url"], "raw_item": {}})
    else:
        raw = unstop_scraper.fetch_details({"event_url": t["url"], "source_url": t["url"]})

    rec_id = compute_fingerprint(raw["title"], raw.get("organizer"), raw.get("event_start_date"), raw.get("city"), raw.get("event_url"))
    raw_hash = compute_raw_hash(raw)

    raw["id"] = rec_id
    raw["raw_data_hash"] = raw_hash

    h_obj = Hackathon(**raw)
    h_obj, missing, warnings = validate_hackathon(h_obj)
    h_obj.confidence = calculate_confidence(h_obj)

    dump = h_obj.model_dump()
    results.append(dump)

    print(json.dumps(dump, indent=2))

with open("hackathon_scraper/scratch/six_records_output.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
