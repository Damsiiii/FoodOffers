import os
import json
import logging
import hashlib
import re
from typing import List, Dict, Any

import requests
from bs4 import BeautifulSoup
import urllib3

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Suppress insecure request warnings for Crepe Runner
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "creperunner_cache.json")


class CrepeRunnerScraper(BaseScraper):
    vendor_id = "creperunner"
    vendor_name = "Crepe Runner"
    vendor_logo = "https://images.unsplash.com/photo-1519671282429-b44660ead0a7?w=100&h=100&fit=crop"
    website_url = "https://creperunner.lk/menu/"
    categories = ["Signature Crepes", "Sweet Crepes", "Savoury Crepes", "Drinks"]

    def _generate_stable_id(self, image_url: str, title: str) -> str:
        """Generate a deterministic, stable offer ID."""
        key = f"{self.vendor_id}:{image_url.strip()}:{title.strip()}".lower()
        hash_str = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
        return f"{self.vendor_id}-{hash_str}"

    def _load_cache(self) -> List[Dict[str, Any]]:
        """Load previously cached deals."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read Crepe Runner cache file: {e}")
        return []

    def _save_cache(self, deals: List[Dict[str, Any]]) -> None:
        """Persist valid scraped deals to cache."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(deals)} Crepe Runner deals to cache")
        except Exception as e:
            logger.error(f"Failed to save Crepe Runner cache: {e}")

    def _validate_deals(self, new_deals: List[Dict[str, Any]], cached_deals: List[Dict[str, Any]]) -> bool:
        """Ensure we extract at least 3 menu images before accepting."""
        if not new_deals:
            logger.warning("Scraped 0 deals from Crepe Runner - validation failed")
            return False

        if len(new_deals) < 3:
            logger.warning(f"Crepe Runner validation failed: found only {len(new_deals)} menu items (expected >= 3)")
            return False

        return True

    def _fetch_api_deals(self) -> List[Dict[str, Any]]:
        """Fetch Crepe Runner menu page and extract high-res menu images."""
        offers = []
        try:
            resp = requests.get(
                self.website_url,
                headers={"User-Agent": "Mozilla/5.0"},
                verify=False,
                timeout=15
            )
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                seen = set()
                
                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    filename_only = src.split('/')[-1].lower()
                    if 'wp-content/uploads' in src and ('crepe' in filename_only or 'drinks' in filename_only or 'mojito' in filename_only or 'chips' in filename_only or 'coffee' in filename_only):
                        # Convert thumbnail URL (e.g. image-300x300.png) to full size URL (image.png)
                        full_src = re.sub(r'-\d+x\d+(\.\w+)$', r'\1', src)
                        if full_src in seen:
                            continue
                        seen.add(full_src)
                        
                        # Generate a clean title from the filename
                        filename = full_src.split('/')[-1].split('.')[0].replace('-', ' ').title()
                        
                        offers.append({
                            "id": self._generate_stable_id(full_src, filename),
                            "title": f"{filename}",
                            "description": "Crepe Runner Sri Lanka Menu Item. Prices and details included in image.",
                            "category": "Signature Crepes",
                            "image_url": full_src,
                            "deal_type": "Menu",
                            "valid_until": "Ongoing",
                            "source_url": self.website_url,
                            "location": "colombo",
                            "is_fallback": False
                        })
            else:
                logger.warning(f"Crepe Runner website returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch Crepe Runner: {e}")
            
        return offers

    def scrape_live(self) -> List[Dict[str, Any]]:
        cached_deals = self._load_cache()
        scraped_deals = self._fetch_api_deals()
        
        if self._validate_deals(scraped_deals, cached_deals):
            self._save_cache(scraped_deals)
            return scraped_deals
            
        if cached_deals:
            logger.info(f"Returning {len(cached_deals)} cached Crepe Runner deals after validation failure/empty scrape")
            return cached_deals
            
        return scraped_deals
