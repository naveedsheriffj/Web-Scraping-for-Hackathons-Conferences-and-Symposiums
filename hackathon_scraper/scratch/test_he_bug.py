from hackathon_scraper.scrapers.hackerearth import HackerEarthScraper
from hackathon_scraper.pipelines.normalize import normalize_record

scraper = HackerEarthScraper()
discovered = scraper.discover(limit=3)
print("Discovered:", len(discovered))

for d in discovered:
    print("Fetching details for:", d["event_url"])
    try:
        det = scraper.fetch_details(d)
        print("Fetched details keys:", list(det.keys()))
        norm = normalize_record(det)
        print("Normalized title:", norm.title, "status:", norm.status)
    except Exception as e:
        import traceback
        print("ERROR:", e)
        traceback.print_exc()
