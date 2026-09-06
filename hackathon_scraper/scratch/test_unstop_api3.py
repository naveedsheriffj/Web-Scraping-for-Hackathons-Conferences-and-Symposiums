from scrapling import Fetcher
import json

fetcher = Fetcher()
opp_id = "1737808"
url = f"https://unstop.com/api/public/competition/{opp_id}"

res = fetcher.get(url)
data = res.json()

print("Top keys:", list(data.keys()))
comp = data.get("data", {}).get("competition", {})
print("Comp keys:", list(comp.keys()))
print("Title:", comp.get("title"))
print("Organisation:", comp.get("organisation", {}).get("name"))
print("Start Date:", comp.get("start_date"))
print("End Date:", comp.get("end_date"))
print("Regn End Date:", comp.get("regn_requirements", {}).get("end_regn_date"))
print("Regn Start Date:", comp.get("regn_requirements", {}).get("start_regn_date"))
print("Location:", comp.get("job_location"))
print("City:", comp.get("city"))
print("State:", comp.get("state"))
print("Country:", comp.get("country"))
print("Prizes:", comp.get("prizes"))
print("Eligible:", comp.get("eligible"))
print("Team size:", comp.get("min_team_size"), comp.get("max_team_size"))
