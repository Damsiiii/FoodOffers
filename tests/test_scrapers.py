import json
from pathlib import Path
import pytest
from scrapers.manager import ScraperManager

EXPECTED_VENDORS = [
    "kfc", "pizzahut", "dominos", "tacobell", "burgerking", "popeyes",
    "fullerburgers", "creperunner", "subway", "dinemore", "pereraandsons",
    "chinesedragon", "baskinrobbins", "breadtalk"
]

def test_scraper_manager_registered_vendors():
    manager = ScraperManager()
    vendors = manager.get_registered_vendors()
    vendor_ids = [v["id"] for v in vendors]
    for expected in EXPECTED_VENDORS:
        assert expected in vendor_ids, f"Vendor {expected} not registered in manager"

def test_fetch_all_offers_live():
    manager = ScraperManager()
    result = manager.fetch_all_offers()
    assert result["total_vendors"] == len(EXPECTED_VENDORS)
    assert "all_offers" in result

def test_update_offers_script():
    import subprocess
    import sys
    import os
    env = dict(os.environ)
    env["PYTHONPATH"] = "."
    res = subprocess.run([sys.executable, "scripts/update_offers.py"], capture_output=True, text=True, env=env)
    assert res.returncode == 0, f"update_offers.py failed: {res.stderr}"
    offers_json = Path("src/data/offers.json")
    assert offers_json.exists()
    with open(offers_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "last_updated" in data
