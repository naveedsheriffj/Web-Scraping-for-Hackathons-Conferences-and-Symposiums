import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

urls = [
    "https://hackrit2026.devfolio.co/",
    "https://metamorph-2.devfolio.co/",
    "https://webcraft24.devfolio.co/"
]

for url in urls:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            idx1 = html.find('id="__NEXT_DATA__"')
            if idx1 != -1:
                s_start = html.find('>', idx1) + 1
                s_end = html.find('</script>', s_start)
                data = json.loads(html[s_start:s_end])
                page_props = data.get('props', {}).get('pageProps', {})
                hack = page_props.get('hackathon', {})
                print(f"=== EVENT PAGE {url} HACKATHON OBJECT ===")
                print("  keys:", list(hack.keys()))
                print("  name:", hack.get('name'))
                print("  starts_at:", hack.get('starts_at'))
                print("  ends_at:", hack.get('ends_at'))
                print("  settings:", hack.get('settings'))
                print("  location:", hack.get('location'))
                print("  address/venue:", hack.get('address'), hack.get('venue'), hack.get('city'))
                print("  desc/tagline:", hack.get('tagline'))
                print("  min_team_size/max_team_size:", hack.get('min_team_size'), hack.get('max_team_size'))
                print("  team_min/team_max:", hack.get('team_min'), hack.get('team_max'))
    except Exception as e:
        print(f"Err {url}: {e}")
