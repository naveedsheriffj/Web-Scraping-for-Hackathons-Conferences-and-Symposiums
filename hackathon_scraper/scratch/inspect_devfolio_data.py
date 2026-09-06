import json
from scrapling import Fetcher

fetcher = Fetcher()

devfolio_urls = [
    "https://hackrit2026.devfolio.co/",
    "https://metamorph-2.devfolio.co/",
    "https://webcraft24.devfolio.co/"
]

for url in devfolio_urls:
    res = fetcher.get(url)
    print("=" * 60)
    print("URL:", url)
    script = res.xpath("//script[@id='__NEXT_DATA__']//text()").get()
    if script:
        data = json.loads(script)
        page_props = data.get("props", {}).get("pageProps", {})
        hackathon = page_props.get("hackathon", {})
        print("Title:", hackathon.get("name"))
        print("Location:", hackathon.get("location"))
        print("Is Online:", hackathon.get("is_online"))
        print("Starts at:", hackathon.get("starts_at"))
        print("Ends at:", hackathon.get("ends_at"))
        print("Regn Starts at:", hackathon.get("regn_starts_at"))
        print("Regn Ends at:", hackathon.get("regn_ends_at"))
        print("Rounds / Timeline:", hackathon.get("rounds"))
        print("Schedule:", hackathon.get("schedule"))
