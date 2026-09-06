import json
from scrapling import Fetcher

fetcher = Fetcher()

# Fetch API payload for HackCelestial 3.0 (1737808), Singularity (1735180), Code Clash (1749224)
opp_ids = ["1737808", "1735180", "1749224"]

for opp_id in opp_ids:
    url = f"https://unstop.com/api/public/competition/{opp_id}"
    res = fetcher.get(url)
    data = res.json().get("data", {}).get("competition", {})
    print("=" * 60)
    print("ID:", opp_id, "Title:", data.get("title"))
    print("Type / Subtype:", data.get("type"), "/", data.get("subtype"))
    print("Start Date:", data.get("start_date"))
    print("End Date:", data.get("end_date"))
    print("Regn reqs:", data.get("regnRequirements"))
    print("Rounds:", json.dumps(data.get("rounds"), indent=2))
    print("Location / Address:", data.get("location"), data.get("address_with_country_logo"))
    print("Organisation:", data.get("organisation"))
