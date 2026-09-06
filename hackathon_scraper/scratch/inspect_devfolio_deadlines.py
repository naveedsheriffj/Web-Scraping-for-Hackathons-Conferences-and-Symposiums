import json
import re
from scrapling import Fetcher
from hackathon_scraper.utils.text import clean_text

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
    page_text = " ".join([clean_text(t) for t in res.xpath("//body//text()").getall() if clean_text(t)])
    
    # Find all occurrences of deadline/regn/application/apply/starts/ends
    matches = re.findall(r".{0,50}(?:deadline|apply|registration|starts|ends|apply by|applications close).{0,50}", page_text, re.IGNORECASE)
    for m in matches[:15]:
        print("  MATCH:", m.strip())
