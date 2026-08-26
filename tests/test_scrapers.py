import json
from pathlib import Path
import pytest
from scrapers.manager import ScraperManager
from scrapers.base import BaseScraper, FALLBACK_FILE

EXPECTED_VENDORS = [
    "kfc", "pizzahut", "dominos", "tacobell", "burgerking", "popeyes",
    "fullerburgers", "creperunner", "subway", "dinemore", "pereraandsons",
    "chinesedragon", "baskinrobbins", "breadtalk"
]

def test_fallback_file_exists_and_valid():
    assert FALLBACK_FILE.exists(), "fallback_dataset.json should exist"
    with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for v in EXPECTED_VENDORS:
        assert v in data, f"Vendor {v} missing in fallback_dataset.json"

def test_scraper_manager_registered_vendors():
    manager = ScraperManager()
    vendors = manager.get_registered_vendors()
    vendor_ids = [v["id"] for v in vendors]
    for expected in EXPECTED_VENDORS:
        assert expected in vendor_ids, f"Vendor {expected} not registered in manager"

def test_all_scrapers_fallback_offers():
    manager = ScraperManager()
    for vendor_id, scraper in manager.scrapers.items():
        fallback_offers = scraper.get_fallback_offers()
        assert len(fallback_offers) > 0, f"Vendor {vendor_id} returned no fallback offers"
        for offer in fallback_offers:
            assert offer["is_fallback"] is True
            assert offer["vendor_id"] == vendor_id
            assert "title" in offer
            assert "discounted_price" in offer
            assert offer["discounted_price"] > 0
            assert "original_price" in offer

def test_fetch_all_offers_force_fallback():
    manager = ScraperManager()
    result = manager.fetch_all_offers(force_fallback=True)
    assert result["total_vendors"] == len(EXPECTED_VENDORS)
    assert result["fallback_vendors"] == len(EXPECTED_VENDORS)
    assert result["total_offers"] > 0
    assert len(result["all_offers"]) == result["total_offers"]

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
    assert data["total_offers"] > 0
