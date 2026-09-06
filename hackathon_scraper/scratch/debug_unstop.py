from scrapling import StealthyFetcher
import json

fetcher = StealthyFetcher()
url = "https://unstop.com/hackathons/hackcelestial-30-pillai-university-navi-mumbai-1737808"
res = fetcher.fetch(url)

print("Status:", res.status)

# Check JSON-LD or Next Data
scripts = res.xpath("//script[@type='application/ld+json']//text() | //script[@id='__NEXT_DATA__']//text()").getall()
print("Found scripts:", len(scripts))
for s in scripts:
    print("Script snippet:", s[:300])

# Check meta tags
meta_dates = res.xpath("//meta[contains(@property, 'date') or contains(@name, 'date') or contains(@property, 'time')]/@content").getall()
print("Meta dates:", meta_dates)

# Check headings or divs with dates
text_nodes = res.xpath("//*[contains(text(), 'Deadline') or contains(text(), 'Ends') or contains(text(), 'Starts') or contains(text(), 'Registration')]/text()").getall()
print("Date text nodes:", [t.strip() for t in text_nodes if len(t.strip()) < 100][:10])
