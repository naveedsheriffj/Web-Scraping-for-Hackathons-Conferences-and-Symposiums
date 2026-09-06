from scrapling import Fetcher
import json

fetcher = Fetcher()

# Test Unstop public opportunity API
opp_id = "1737808"
api_url = f"https://unstop.com/api/public/opportunity/get-opportunity-details/{opp_id}"

res = fetcher.get(api_url)
print("API Status:", res.status)
if res.status == 200:
    try:
        data = res.json()
        print("API Keys:", list(data.keys()))
        data_obj = data.get("data", {}).get("opportunity", {})
        print("Title:", data_obj.get("title"))
        print("Organisation:", data_obj.get("organisation", {}).get("name"))
        print("Dates:", data_obj.get("start_date"), data_obj.get("end_date"), data_obj.get("regn_requirements", {}).get("end_regn_date"))
        print("Prizes:", data_obj.get("prizes"))
        print("Eligibility:", data_obj.get("eligibility"))
    except Exception as e:
        print("Error parsing API json:", e)
