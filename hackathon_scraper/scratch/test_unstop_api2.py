from scrapling import Fetcher, DynamicFetcher
import json

fetcher = Fetcher()

# Test different candidate API endpoints for Unstop
opp_id = "1737808"
slug = "hackcelestial-30-pillai-university-navi-mumbai-1737808"

endpoints = [
    f"https://unstop.com/api/public/competition/{opp_id}",
    f"https://unstop.com/api/public/competition/{slug}",
    f"https://unstop.com/api/public/opportunity/{opp_id}",
    f"https://unstop.com/api/public/opportunity/{slug}",
    f"https://unstop.com/api/public/opportunity/details/{opp_id}",
    f"https://unstop.com/api/public/opportunity/search-details/{opp_id}",
    f"https://unstop.com/api/public/opportunity/get-details/{opp_id}",
]

for url in endpoints:
    res = fetcher.get(url)
    print(f"URL: {url} -> Status: {res.status}")
    if res.status == 200:
        print("Response sample:", res.text[:200])
