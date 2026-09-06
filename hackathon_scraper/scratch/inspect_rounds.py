import json
from scrapling import Fetcher

fetcher = Fetcher()

for opp_id in ["1737808", "1735180"]:
    url = f"https://unstop.com/api/public/competition/{opp_id}"
    res = fetcher.get(url)
    data = res.json().get("data", {}).get("competition", {})
    print("=" * 60)
    print("ID:", opp_id, "Title:", data.get("title"))
    rounds = data.get("rounds", [])
    for r in rounds:
        print("  Round:", r.get("round_order"), r.get("status"))
        for d in r.get("details", []):
            print("    Subround title:", d.get("title"))
            print("    Start:", d.get("start_date"))
            print("    End:", d.get("end_date"))
