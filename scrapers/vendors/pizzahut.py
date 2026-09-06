import os
import json
import logging
import hashlib
import warnings
from typing import List, Dict, Any, Optional

import requests

from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "pizzahut_cache.json")

# Pizza Hut API endpoints
PH_TOKEN_URL = "https://phapis.pizzahut.lk/gettoken"
PH_BANNER_URL = "https://phapis.pizzahut.lk/api/home/banner"
PH_PROMO_ITEMS_URL = "https://phapis.pizzahut.lk/api/menu/items?webCategory=promo&menuCategory=meal-deal"

# Image base URL
PH_IMAGE_BASE = "https://adminsc.pizzahut.lk/"

# Minimum number of promo deals we expect from a successful API call
MIN_EXPECTED_DEALS = 1

# Maximum ratio of deals we can lose between scrapes before we refuse to overwrite
MAX_DEAL_DROP_RATIO = 0.5

# These classification names from the API indicate actual promotional deals
PROMO_CLASSIFICATIONS = {
    "Weekend Vibes", "Cyber Savings", "Thrilling Thursday",
    "Grand Dipper Deals", "Add-ons", "Meal Deals", "Pizza Deals",
}

# Map API ClassificationName to display categories
CLASSIFICATION_TO_CATEGORY = {
    "Weekend Vibes": "Meal Deals",
    "Thrilling Thursday": "Thrilling Thursday",
    "Grand Dipper Deals": "Grand Dipper Deals",
    "Cyber Savings": "Cyber Savings",
    "Add-ons": "Add-ons",
}


class PizzaHutScraper(BaseScraper):
    vendor_id = "pizzahut"
    vendor_name = "Pizza Hut Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.pizzahut.lk"
    categories = ["Thrilling Thursday", "Grand Dipper Deals", "Cyber Savings", "Add-ons", "Pizza Deals", "Meal Deals"]

    REQUEST_TIMEOUT = 15
    MAX_RETRIES = 2

    def _get_token(self) -> Optional[str]:
        """
        Obtain an OAuth2 access token from the Pizza Hut API.

        The Pizza Hut website uses a public OAuth2 token with hardcoded credentials
        (JustWebUser) that the frontend uses to authenticate API requests.
        """
        auth_data = {
            "username": os.getenv("PIZZAHUT_API_USER", "JustWebUser"),
            "password": os.getenv("PIZZAHUT_API_PASS", "nxNCtHIDOJVbGBa"),
            "grant_type": "password",
            "scope": "/vQFtb6VBYg",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    PH_TOKEN_URL, data=auth_data, headers=headers,
                    verify=False, timeout=self.REQUEST_TIMEOUT
                )
                if resp.status_code == 200:
                    token = resp.json().get("access_token")
                    if token:
                        return token
                    else:
                        logger.warning(f"Pizza Hut: Token response missing access_token (attempt {attempt})")
                else:
                    logger.warning(f"Pizza Hut: Token request returned {resp.status_code} (attempt {attempt})")
            except requests.RequestException as e:
                logger.warning(f"Pizza Hut: Token request failed (attempt {attempt}): {e}")

        logger.error(f"Pizza Hut: Failed to obtain access token after {self.MAX_RETRIES} attempts")
        return None

    def _api_request(self, url: str, token: str) -> Optional[Any]:
        """Make an authenticated API request with retries."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = requests.post(
                    url, json={}, headers=headers,
                    verify=False, timeout=self.REQUEST_TIMEOUT
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    logger.warning(f"Pizza Hut API: {url} returned {resp.status_code} (attempt {attempt})")
            except requests.RequestException as e:
                logger.warning(f"Pizza Hut API: {url} failed (attempt {attempt}): {e}")

        return None

    def _normalize_image_url(self, raw_url: Optional[str]) -> str:
        """
        Normalize an image URL from the API.

        The API sometimes returns relative URLs or URLs with double slashes.
        """
        if not raw_url or not isinstance(raw_url, str):
            return ""

        url = raw_url.strip()

        # Handle relative URLs
        if url.startswith("/"):
            url = PH_IMAGE_BASE.rstrip("/") + url

        # Fix double slashes in the path (but not in https://)
        if url.startswith("https://"):
            protocol, rest = url.split("://", 1)
            rest = rest.replace("//", "/")
            url = f"{protocol}://{rest}"

        if not url.startswith("http"):
            return ""

        return url

    def _normalize_deal_url(self, raw_url: Optional[str], item_url_slug: Optional[str]) -> str:
        """Build a proper deal URL from API data."""
        if item_url_slug:
            slug = item_url_slug.strip()
            # Clean up URL-encoded non-breaking spaces
            slug = slug.replace("\xa0", "-").replace(" ", "-")
            return f"https://www.pizzahut.lk/menu/promo/{slug}"
        if raw_url and isinstance(raw_url, str) and "pizzahut.lk" in raw_url:
            return raw_url
        return "https://www.pizzahut.lk/menu/promo/meal-deal"

    def _generate_stable_id(self, code: str, web_name: str) -> str:
        """Generate a stable, deterministic ID for a deal based on its API code."""
        if code:
            return f"pizzahut-{code.lower()}"
        key = web_name.lower().strip()
        hash_suffix = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
        return f"pizzahut-{hash_suffix}"

    def _determine_category(self, classification_name: str, web_name: str) -> str:
        """Determine the display category from the API's ClassificationName."""
        if classification_name in CLASSIFICATION_TO_CATEGORY:
            return CLASSIFICATION_TO_CATEGORY[classification_name]

        # Fallback: inspect the title
        lower_name = web_name.lower()
        if "thrilling" in lower_name or "thursday" in lower_name:
            return "Thrilling Thursday"
        elif "grand dipper" in lower_name or "dipper" in lower_name:
            return "Grand Dipper Deals"
        elif "cyber" in lower_name:
            return "Cyber Savings"
        elif "add on" in lower_name or "addon" in lower_name or "pasta" in lower_name or "melts" in lower_name:
            return "Add-ons"
        elif "pizza" in lower_name:
            return "Pizza Deals"
        return "Meal Deals"

    def _parse_promo_items(self, api_items: list) -> List[Dict[str, Any]]:
        """Parse the promo items from the Pizza Hut API response."""
        offers = []
        seen_codes = set()

        for item in api_items:
            if not isinstance(item, dict):
                continue

            code = item.get("Code", "")
            web_name = item.get("WebName", "")

            if not web_name:
                continue

            # Deduplicate by code
            if code and code in seen_codes:
                continue
            seen_codes.add(code)

            classification = item.get("ClassificationName", "")
            category = self._determine_category(classification, web_name)

            image_url = self._normalize_image_url(
                item.get("FullImageUrl") or item.get("ImageURL")
            )

            deal_url = self._normalize_deal_url(None, item.get("Url"))

            # Parse price - the promo items often have Price: "0.00" because they
            # are meal deals with customizable sub-items. This is expected.
            price_str = item.get("Price", "0.00")
            try:
                price_val = float(price_str) if price_str else 0.0
            except (ValueError, TypeError):
                price_val = 0.0

            description = item.get("Description") or item.get("DescriptionShort") or web_name

            offer = {
                "id": self._generate_stable_id(code, web_name),
                "title": web_name,
                "description": f"Pizza Hut Sri Lanka: {description}" if description != web_name else f"Pizza Hut Sri Lanka promotion: {web_name}",
                "category": category,
                "image_url": image_url,
                "deal_type": classification or "Special Promotion",
                "valid_until": "Limited Time",
                "source_url": deal_url,
            }

            # Only set price if it's meaningful (> 0)
            if price_val > 0:
                offer["discounted_price"] = price_val

            offers.append(offer)

        return offers

    def _parse_banner(self, banner_data: Any) -> Optional[Dict[str, Any]]:
        """Parse a banner item from the Pizza Hut banner API."""
        if not isinstance(banner_data, dict):
            return None

        banner_img = self._normalize_image_url(
            banner_data.get("FullImageUrl") or banner_data.get("ImageURL")
        )
        if not banner_img:
            return None

        title = banner_data.get("Tiltle") or banner_data.get("Name") or banner_data.get("Description") or ""

        # Skip banners with no meaningful title
        if not title or title.strip().lower() in ["new", "", "banner"]:
            # Use the description as a fallback
            desc = banner_data.get("Description", "")
            if desc and desc.strip().lower() not in ["new", "", "banner"]:
                title = desc
            else:
                title = "Pizza Hut Featured Promotion"

        banner_url = banner_data.get("Url", "")
        if "azurewebsites.net" in banner_url or not banner_url.startswith("http"):
            banner_url = "https://www.pizzahut.lk"

        return {
            "id": self._generate_stable_id("", f"banner-{title}"),
            "title": title,
            "description": f"Pizza Hut Sri Lanka: Featured promotion",
            "category": "Cyber Savings",
            "image_url": banner_img,
            "deal_type": "Featured Promotion",
            "valid_until": "Limited Time",
            "source_url": banner_url,
        }

    def _validate_deals(self, new_deals: List[Dict], cached_deals: List[Dict]) -> bool:
        """
        Validate that the scraped deals are reasonable.
        Returns True if the deals pass validation and should be saved.
        """
        if len(new_deals) == 0:
            logger.warning("Pizza Hut: Scrape returned 0 deals — refusing to overwrite cache")
            return False

        if len(new_deals) < MIN_EXPECTED_DEALS:
            logger.warning(f"Pizza Hut: Only {len(new_deals)} deals found (minimum: {MIN_EXPECTED_DEALS})")
            if not cached_deals:
                return True
            return False

        # Check for a huge unexplained drop in deals
        if cached_deals and len(cached_deals) > 0:
            ratio = len(new_deals) / len(cached_deals)
            if ratio < MAX_DEAL_DROP_RATIO:
                logger.warning(
                    f"Pizza Hut: Deal count dropped from {len(cached_deals)} to {len(new_deals)} "
                    f"(ratio {ratio:.2f} < {MAX_DEAL_DROP_RATIO}) — refusing to overwrite"
                )
                return False

        # Check for duplicate titles
        titles = [d.get("title", "") for d in new_deals]
        unique_titles = set(titles)
        if len(unique_titles) < len(titles) * 0.5:
            logger.warning("Pizza Hut: More than 50% duplicate titles detected — data may be corrupt")
            return False

        return True

    def _load_cache(self) -> List[Dict]:
        """Load the cached deals, returning an empty list on failure."""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Pizza Hut: Failed to read cache: {e}")
        return []

    def _save_cache(self, deals: List[Dict]) -> None:
        """Save deals to the cache file."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            logger.info(f"Pizza Hut: Cached {len(deals)} deals to {CACHE_FILE}")
        except IOError as e:
            logger.warning(f"Pizza Hut: Failed to write cache: {e}")

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Scrape Pizza Hut Sri Lanka deals using their official REST API.

        Strategy:
        1. Obtain an OAuth2 access token using the public web credentials
        2. Fetch promotional items from the promo/meal-deal API endpoint
        3. Optionally fetch the homepage banner for featured promotions
        4. Parse and normalize all deal data
        5. Validate results before saving to cache
        6. Fall back to cache if the live scrape fails
        """
        offers = []
        seen_titles = set()

        # Step 1: Get auth token
        token = self._get_token()
        if not token:
            logger.error("Pizza Hut: Cannot scrape without a valid token")
            cached = self._load_cache()
            if cached:
                logger.info(f"Pizza Hut: Using {len(cached)} cached deals (token failure)")
                return cached
            return []

        # Step 2: Fetch promo/meal-deal items from the API
        try:
            promo_data = self._api_request(PH_PROMO_ITEMS_URL, token)
            if promo_data is not None:
                # The API returns a list directly for this endpoint
                if isinstance(promo_data, list):
                    items = promo_data
                elif isinstance(promo_data, dict):
                    items = promo_data.get("Data", [])
                    if not isinstance(items, list):
                        items = []
                else:
                    items = []

                parsed = self._parse_promo_items(items)
                for offer in parsed:
                    title_key = offer["title"].lower().strip()
                    if title_key not in seen_titles:
                        seen_titles.add(title_key)
                        offers.append(offer)

                logger.info(f"Pizza Hut: Parsed {len(parsed)} items from promo API")
            else:
                logger.warning("Pizza Hut: Promo API returned no data")
        except Exception as e:
            logger.error(f"Pizza Hut: Error fetching promo items: {e}")

        # Step 3: Fetch banner (optional — don't fail if this doesn't work)
        try:
            banner_data = self._api_request(PH_BANNER_URL, token)
            if banner_data and isinstance(banner_data, dict):
                raw_banner = banner_data.get("Data")
                banners = [raw_banner] if isinstance(raw_banner, dict) else (
                    raw_banner if isinstance(raw_banner, list) else []
                )
                for b in banners:
                    parsed_banner = self._parse_banner(b)
                    if parsed_banner:
                        title_key = parsed_banner["title"].lower().strip()
                        if title_key not in seen_titles:
                            seen_titles.add(title_key)
                            offers.append(parsed_banner)
        except Exception as e:
            logger.warning(f"Pizza Hut: Banner API error (non-fatal): {e}")

        # Sort for deterministic output
        offers.sort(key=lambda x: (x["category"], x["title"]))

        # Step 4: Validate and cache
        cached = self._load_cache()

        if self._validate_deals(offers, cached):
            self._save_cache(offers)
            logger.info(f"Pizza Hut: Successfully scraped {len(offers)} deals")
            return offers
        else:
            if cached:
                logger.info(f"Pizza Hut: Using {len(cached)} cached deals (live scrape failed validation)")
                return cached
            else:
                logger.warning("Pizza Hut: No cached deals available and live scrape failed validation")
                return offers
