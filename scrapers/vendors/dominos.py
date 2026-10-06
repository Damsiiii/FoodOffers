import os
import json
import logging
import hashlib
import re
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper
from scrapers.browser import intercept_api_deals

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "dominos_cache.json")

class DominosScraper(BaseScraper):
    vendor_id = "dominos"
    vendor_name = "Domino's Pizza Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://pizzaonline.dominoslk.com/"
    categories = ["Value Combos", "Pizza Deals", "Sides", "Desserts"]

    def _generate_stable_id(self, image_url: str, title: str) -> str:
        """Generate a deterministic, stable offer ID from image URL or title."""
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
                logger.warning(f"Failed to read Domino's cache file: {e}")
        return []

    def _save_cache(self, deals: List[Dict[str, Any]]) -> None:
        """Persist valid scraped deals to cache."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(deals)} Domino's deals to cache")
        except Exception as e:
            logger.error(f"Failed to save Domino's cache: {e}")

    def _validate_deals(self, new_deals: List[Dict[str, Any]], cached_deals: List[Dict[str, Any]]) -> bool:
        """Sanity-check scraped deals before accepting them."""
        if not new_deals:
            logger.warning("Scraped 0 deals from Domino's - validation failed")
            return False

        # If we scraped deals, verify they aren't all duplicates
        titles = [d.get("title", "").strip().lower() for d in new_deals if d.get("title")]
        if not titles:
            return False

        unique_titles = set(titles)
        if len(unique_titles) < len(titles) * 0.4:
            logger.warning(f"High duplicate rate in Domino's deals ({len(unique_titles)} unique / {len(titles)} total)")
            return False

        return True

    def _extract_deals_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse deals and promo banners from Domino's website HTML."""
        offers = []
        seen_urls = set()
        
        # Domino's injects component props as HTML encoded JSON in module-props attributes
        # and has other scattered image URLs for banners.
        
        # We will regex search for images in the HTML that look like banners
        images = re.findall(r'(https://apis\.dominoslk\.com/[^"\']*?(?:Banner|Party_Pack|Offer|Promo)[^"\']*?\.(?:jpg|png|jpeg))', html, re.IGNORECASE)
        
        # Try to parse the HTML encoded JSON as well for more structured data
        props_matches = re.findall(r'module-props="([^"]+)"', html)
        for prop_str in props_matches:
            try:
                decoded = prop_str.replace('&quot;', '"')
                prop_data = json.loads(decoded)
                
                # If prop_data is a list of banners
                if isinstance(prop_data, list):
                    for item in prop_data:
                        img = item.get('imageUrl', '')
                        if img and 'apis.dominoslk.com' in img:
                            images.append(img)
            except Exception:
                pass
                
        idx = 1
        for img_url in set(images):
            if img_url in seen_urls:
                continue
            seen_urls.add(img_url)
            
            # Since we only get the banner images from the initial HTML, we construct generic offers
            # which the BaseScraper will enhance with Vision OCR
            title = "Domino's Pizza Promotion"
            if "Party_Pack" in img_url:
                title = "Domino's Party Pack"
            elif "Banners" in img_url:
                title = "Domino's Special Offer"
                
            offers.append({
                "id": self._generate_stable_id(img_url, title),
                "title": title,
                "description": f"Domino's Sri Lanka promotion. See website for full details.",
                "category": "Pizza Deals",
                "image_url": img_url,
                "deal_type": "Special Promotion",
                "valid_until": "Limited Time",
                "source_url": self.website_url,
                "location": "colombo",
                "is_fallback": False
            })
            idx += 1
            
        return offers

    def _fetch_api_deals(self) -> List[Dict[str, Any]]:
        """Scrape live deals dynamically from Domino's website HTML and APIs."""
        scraped_deals = []
        try:
            resp = requests.get(
                self.website_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                verify=False,
                timeout=12
            )
            if resp.status_code == 200:
                scraped_deals = self._extract_deals_from_html(resp.text)
            else:
                logger.warning(f"Domino's website returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch Domino's website: {e}")
            
        return scraped_deals

    def scrape_live(self) -> List[Dict[str, Any]]:
        cached_deals = self._load_cache()
        scraped_deals = self._fetch_api_deals()
        
        # If custom extraction fails to find deals, fallback to Playwright XHR interception
        if not scraped_deals:
            logger.info("Custom Domino's HTML scrape yielded 0 results. Falling back to Playwright interception.")
            try:
                # Use intercept_api_deals but map the results to include stable IDs and flags
                raw_deals = intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
                for deal in raw_deals:
                    deal["id"] = self._generate_stable_id(deal.get("image_url", ""), deal.get("title", ""))
                    deal["is_fallback"] = True
                scraped_deals = raw_deals
            except Exception as e:
                logger.error(f"Domino's Playwright fallback failed: {e}")
                
        if self._validate_deals(scraped_deals, cached_deals):
            self._save_cache(scraped_deals)
            return scraped_deals

        if cached_deals:
            logger.info(f"Returning {len(cached_deals)} cached Domino's deals after validation check")
            return cached_deals

        return scraped_deals
