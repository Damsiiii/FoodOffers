import logging
import json
import os
import re
import hashlib
from typing import List, Dict, Any, Optional
import requests
import urllib3
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "popeyes_cache.json")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Known deal patterns for Popeyes Sri Lanka promo graphics
POPEYES_PROMO_PATTERNS = [
    {
        "pattern": r"sandwich_bogo",
        "title": "Spicy Double Deal - Buy 1 Get 1 FREE",
        "description": "Every Tuesday: Buy One Get One FREE Spicy Chicken Sandwich for just Rs. 1,600. Valid for delivery and dine-in.",
        "category": "Sandwiches & Burgers",
        "discounted_price": 1600.0,
        "original_price": 3200.0,
        "discount_percentage": 50,
        "deal_type": "Day Specific Deal",
        "valid_until": "Every Tuesday",
    },
    {
        "pattern": r"drumstick_deal",
        "title": "Drumstick Deal - Buy 4 Get 4 FREE",
        "description": "Every Friday: Buy 4 Get 4 FREE Drumsticks for just Rs. 2,800. Save Rs. 1,920! Valid for delivery and dine-in.",
        "category": "Chicken Buckets",
        "discounted_price": 2800.0,
        "original_price": 4720.0,
        "discount_percentage": 41,
        "deal_type": "Day Specific Deal",
        "valid_until": "Every Friday",
    },
    {
        "pattern": r"bogo_kv",
        "title": "Why Stop at 1? Make it Double - Buy 1 Get 1 FREE",
        "description": "Every Saturday: Buy One Get One FREE Spicy Chicken Sandwich or Grilled Chicken Burger for just Rs. 1,600. Exclusively for delivery.",
        "category": "Sandwiches & Burgers",
        "discounted_price": 1600.0,
        "original_price": 3200.0,
        "discount_percentage": 50,
        "deal_type": "Day Specific Deal",
        "valid_until": "Every Saturday",
    },
    {
        "pattern": r"big_box",
        "title": "Big Box - 10 Ways to Go Big",
        "description": "Choose your box, feast your way and save up to Rs. 2,070 with Popeyes signature Big Box meal combinations. Dine-in, takeaway or delivery.",
        "category": "Chicken Buckets",
        "deal_type": "Combo Deal",
        "discount_percentage": 25,
        "valid_until": "Limited Time",
    },
    {
        "pattern": r"header_banner",
        "title": "Popeyes Louisiana Chicken Promotion",
        "description": "Freshly prepared bold Louisiana style fried chicken, sandwiches, tenders and big box feasts.",
        "category": "Chicken Buckets",
        "deal_type": "Official Promotion",
        "valid_until": "Ongoing",
    },
]


class PopeyesScraper(BaseScraper):
    vendor_id = "popeyes"
    vendor_name = "Popeyes Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=100&h=100&fit=crop"
    website_url = "https://popeyes.com.lk"
    categories = ["Sandwiches & Burgers", "Chicken Buckets", "Tenders"]

    def _generate_stable_id(self, image_url: str, title: str) -> str:
        """Generate a deterministic, stable offer ID from image URL or title."""
        key = f"{self.vendor_id}:{image_url.strip()}:{title.strip()}".lower()
        hash_str = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
        return f"popeyes-{hash_str}"

    def _load_cache(self) -> List[Dict[str, Any]]:
        """Load previously cached deals."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read Popeyes cache file: {e}")
        return []

    def _save_cache(self, deals: List[Dict[str, Any]]) -> None:
        """Persist valid scraped deals to cache."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(deals)} Popeyes deals to cache")
        except Exception as e:
            logger.error(f"Failed to save Popeyes cache: {e}")

    def _validate_deals(self, new_deals: List[Dict[str, Any]], cached_deals: List[Dict[str, Any]]) -> bool:
        """Sanity-check scraped deals before accepting them."""
        if not new_deals:
            logger.warning("Scraped 0 deals from Popeyes - validation failed")
            return False

        titles = [d.get("title", "").strip().lower() for d in new_deals if d.get("title")]
        if not titles:
            return False

        unique_titles = set(titles)
        if len(unique_titles) < len(titles) * 0.4:
            logger.warning(f"High duplicate rate in Popeyes deals ({len(unique_titles)} unique / {len(titles)} total)")
            return False

        return True

    def _parse_generic_banner(self, img_url: str, alt_text: str) -> Dict[str, Any]:
        """Extract deal metadata dynamically for new or unrecognized banners."""
        filename = img_url.split("/")[-1]
        name_clean = re.sub(r"_[a-f0-9]{8,}\.\w+$", "", filename, flags=re.IGNORECASE)
        tokens = [t for t in re.split(r"[_\-\s]+", name_clean) if t.lower() not in ["plk", "kv", "copy", "01", "02", "03", "04", "05"]]
        
        title = alt_text.strip() if alt_text and len(alt_text) > 3 else " ".join(tokens).title()
        if not title or len(title) < 4:
            title = "Popeyes Louisiana Chicken Deal"

        category = "Chicken Buckets"
        lower_name = f"{filename} {alt_text}".lower()
        if any(w in lower_name for w in ["burger", "sandwich"]):
            category = "Sandwiches & Burgers"
        elif any(w in lower_name for w in ["tender", "strip", "wing"]):
            category = "Tenders"

        deal_type = "Special Promotion"
        if "bogo" in lower_name or "buy 1 get 1" in lower_name:
            deal_type = "Buy 1 Get 1 Free"
        elif "combo" in lower_name or "box" in lower_name:
            deal_type = "Combo Deal"

        return {
            "id": self._generate_stable_id(img_url, title),
            "title": title,
            "description": f"Popeyes Sri Lanka promotion: {title}.",
            "category": category,
            "image_url": img_url,
            "deal_type": deal_type,
            "valid_until": "Limited Time",
            "source_url": self.website_url,
            "location": "colombo, kandy, negombo",
        }

    def _extract_deals_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse deals and promo banners from Popeyes website HTML."""
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        offers = []
        seen_urls = set()

        # Gather all candidate images (desktop & mobile)
        for img in soup.find_all("img"):
            src = img.get("data-src") or img.get("src") or ""
            img_id = (img.get("id") or "").lower()
            alt = img.get("alt") or ""

            if not src or "logo" in src.lower() or "artboard" in src.lower() or "images/" in src:
                continue

            # Must be inside uploads or identified as a promo / premium selection image
            is_deal_image = (
                img_id in ["premium_selection_img", "header-banner", "mobilehead-banner"] or
                "uploads" in src or
                "banner" in img_id
            )

            if not is_deal_image:
                continue

            # Filter out non-deal static images like menu panels or icons
            if any(ignore in src for ignore in ["Header_80x130", "Menu_Panel", "Jaffna_Menu", "Menu_0"]):
                continue

            full_url = src if src.startswith("http") else f"{self.website_url}/{src.lstrip('/')}"
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Match against known promotional deal patterns
            matched = False
            for rule in POPEYES_PROMO_PATTERNS:
                if re.search(rule["pattern"], full_url, re.IGNORECASE):
                    deal = {
                        "id": self._generate_stable_id(full_url, rule["title"]),
                        "title": rule["title"],
                        "description": rule["description"],
                        "category": rule["category"],
                        "image_url": full_url,
                        "deal_type": rule["deal_type"],
                        "valid_until": rule["valid_until"],
                        "source_url": self.website_url,
                        "location": "colombo, kandy, negombo",
                    }
                    if "discounted_price" in rule:
                        deal["discounted_price"] = rule["discounted_price"]
                    if "original_price" in rule:
                        deal["original_price"] = rule["original_price"]
                    if "discount_percentage" in rule:
                        deal["discount_percentage"] = rule["discount_percentage"]
                    offers.append(deal)
                    matched = True
                    break

            if not matched:
                offers.append(self._parse_generic_banner(full_url, alt))

        return offers

    def scrape_live(self) -> List[Dict[str, Any]]:
        """Scrape live deals dynamically from Popeyes website."""
        cached_deals = self._load_cache()
        scraped_deals = []

        try:
            resp = requests.get(
                self.website_url,
                headers=DEFAULT_HEADERS,
                verify=False,
                timeout=12
            )
            if resp.status_code == 200:
                scraped_deals = self._extract_deals_from_html(resp.text)
            else:
                logger.warning(f"Popeyes website returned HTTP {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed to fetch Popeyes website: {e}")

        # Validate and return
        if self._validate_deals(scraped_deals, cached_deals):
            self._save_cache(scraped_deals)
            return scraped_deals

        if cached_deals:
            logger.info(f"Returning {len(cached_deals)} cached Popeyes deals after validation check")
            return cached_deals

        return scraped_deals
