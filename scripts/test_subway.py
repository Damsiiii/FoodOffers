import sys
import json
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from scrapers.browser import intercept_api_deals

try:
    print("Testing Subway with Playwright...")
    deals = intercept_api_deals("https://subway.lk", "subway", "Subway Sri Lanka", timeout=30000)
    print("Deals Found:", len(deals))
    print(json.dumps(deals, indent=2))
except Exception as e:
    print("Error:", e)
