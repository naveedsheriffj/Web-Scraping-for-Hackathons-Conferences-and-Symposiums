from scrapling import Fetcher
import json

fetcher = Fetcher()
opp_id = "1737808"
url = f"https://unstop.com/api/public/competition/{opp_id}"

res = fetcher.get(url)
data = res.json()
comp = data.get("data", {}).get("competition", {})

print("regnRequirements:", comp.get("regnRequirements"))
print("locations:", comp.get("locations"))
print("organisation:", comp.get("organisation"))
