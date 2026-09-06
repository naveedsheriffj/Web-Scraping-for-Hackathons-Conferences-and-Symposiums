import json
from scrapling import Fetcher

fetcher = Fetcher()
url = "https://webcraft24.devfolio.co/"
res = fetcher.get(url)
script = res.xpath("//script[@id='__NEXT_DATA__']//text()").get()
if script:
    data = json.loads(script)
    hack = data.get("props", {}).get("pageProps", {}).get("hackathon", {})
    print("WebCraft24 JSON:")
    print("starts_at:", hack.get("starts_at"))
    print("ends_at:", hack.get("ends_at"))
    print("location:", hack.get("location"))
    print("team_min/max:", hack.get("team_min"), hack.get("team_max"))
    print("settings:", hack.get("settings"))
