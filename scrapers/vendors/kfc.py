import logging
import json
import os
import re
import hashlib
from typing import List, Dict, Any, Optional
from html import unescape

import requests

from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "kfc_cache.json")

# KFC product images are hosted on this domain
KFC_IMAGE_HOST = "admin-kfc-web.azurewebsites.net"

# Pages that contain actual promotional deals (not regular menu items)
KFC_PROMO_PAGES = [
    "/menu/promotions",
]

# Pages that contain menu deals (combos, meals, etc.) that are also worth scraping
KFC_DEAL_PAGES = [
    "/menu/meals-and-beverages",
]

# Minimum number of deals we expect from a successful scrape.
# If we get fewer, the scrape is considered suspect.
MIN_EXPECTED_DEALS = 1

# Maximum ratio of deals we can lose between scrapes before we refuse to overwrite
MAX_DEAL_DROP_RATIO = 0.5


class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Promotions", "Bucket Deals", "Burgers & Combos", "Rice Bowls", "Meal Combos"]

    REQUEST_TIMEOUT = 20
    MAX_RETRIES = 2

    def _get_session(self) -> requests.Session:
        """Create a requests session with proper headers and cookies."""
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-LK,en-US;q=0.9,en;q=0.8",
        })
        # Visit the homepage first to obtain session cookies
        try:
            session.get("https://www.kfc.lk/", timeout=self.REQUEST_TIMEOUT)
        except requests.RequestException as e:
            logger.warning(f"KFC: Failed to initialize session: {e}")
        return session

    def _fetch_page(self, session: requests.Session, path: str) -> Optional[str]:
        """Fetch a KFC page with retries, returning the HTML or None on failure."""
        url = f"https://www.kfc.lk{path}"
        last_error = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                resp = session.get(url, timeout=self.REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    return resp.text
                else:
                    logger.warning(f"KFC: {url} returned status {resp.status_code} (attempt {attempt})")
                    last_error = f"HTTP {resp.status_code}"
            except requests.RequestException as e:
                logger.warning(f"KFC: Request to {url} failed (attempt {attempt}): {e}")
                last_error = str(e)
        logger.error(f"KFC: All {self.MAX_RETRIES} attempts failed for {url}: {last_error}")
        return None

    def _extract_items_from_html(self, html: str, page_path: str) -> List[Dict[str, Any]]:
        """
        Extract product/deal items from the KFC server-rendered HTML.

        The KFC website uses a consistent card structure:
        - Each card is in a div with class 'itemContainer'
        - Cards contain: <img> with product image and alt text
        - <h3 class="menu-item-name"> with the title
        - <span class="price"> with the price
        - Optional data attributes on add-to-cart buttons: data-price, data-main-menu-name
        """
        items = []

        # Split on the itemContainer marker to isolate each card
        containers = html.split('itemContainer">')
        if len(containers) <= 1:
            return items

        for card_chunk in containers[1:]:
            # Limit to a reasonable size for one card
            card_html = card_chunk[:4000]

            # Extract image URL and alt text
            img_match = re.search(
                r'<img\s+src="([^"]*)"[^>]*alt="([^"]*)"',
                card_html
            )
            if not img_match:
                continue

            image_url = img_match.group(1).strip()
            alt_text = unescape(img_match.group(2).strip())

            # Only accept images from the KFC image host
            if KFC_IMAGE_HOST not in image_url:
                continue

            # Extract title from h3.menu-item-name (desktop version has full text)
            title = ""
            title_match = re.search(
                r'<h3\s+class="menu-item-name\s+hidden-sm\s+hidden-xs"[^>]*'
                r'title="([^"]*)"[^>]*>([^<]*)',
                card_html
            )
            if title_match:
                title = unescape(title_match.group(1).strip())
                if not title:
                    title = unescape(title_match.group(2).strip())

            # Fallback: use alt text as the title
            if not title:
                title = alt_text

            if not title:
                continue

            # Extract price from span.price
            price_text = ""
            price_val = None
            price_span = re.search(r'<span\s+class="price"[^>]*>([^<]*)</span>', card_html)
            if price_span:
                price_text = price_span.group(1).strip()
                price_num = re.search(r'Rs\.?\s*([\d,]+)', price_text)
                if price_num:
                    try:
                        price_val = float(price_num.group(1).replace(",", ""))
                    except ValueError:
                        pass

            # Also check data-price on the add-to-cart button
            if price_val is None:
                data_price = re.search(r'data-price="([\d.]+)"', card_html)
                if data_price:
                    try:
                        price_val = float(data_price.group(1))
                    except ValueError:
                        pass

            # Extract description from the hidden-xs paragraph
            description = ""
            desc_match = re.search(
                r'<p\s+class="[^"]*menu-item-desc[^"]*"[^>]*title="([^"]*)"',
                card_html
            )
            if desc_match:
                description = unescape(desc_match.group(1).strip())

            items.append({
                "title": title,
                "description": description or title,
                "image_url": image_url,
                "price": price_val,
                "source_page": page_path,
            })

        return items

    def _determine_category(self, title: str, description: str, source_page: str) -> str:
        """Determine the deal category based on the item's title, description, and source page."""
        text = f"{title} {description}".lower()

        # Items from the promotions page are always promotions
        if "promotions" in source_page:
            return "Promotions"

        if any(k in text for k in ["burger", "combo", "twister", "decker", "wrap", "submarine", "zinger"]):
            return "Burgers & Combos"
        elif any(k in text for k in ["bucket", "pc", "hot & crispy", "hot and crispy", "h&c"]):
            return "Bucket Deals"
        elif any(k in text for k in ["rice", "biryani"]):
            return "Rice Bowls"
        elif any(k in text for k in ["meal", "combo", "pepsi", "drink"]):
            return "Meal Combos"
        return "Promotions"

    def _generate_stable_id(self, title: str, source_page: str) -> str:
        """Generate a stable, deterministic ID for a deal based on its content."""
        key = f"{title}|{source_page}".lower().strip()
        hash_suffix = hashlib.md5(key.encode("utf-8")).hexdigest()[:8]
        return f"kfc-{hash_suffix}"

    def _is_promotional_deal(self, item: Dict[str, Any]) -> bool:
        """
        Determine if an item is a promotional deal rather than a regular menu item.

        Items from /menu/promotions are always deals.
        Items from other pages are deals if they show deal-like characteristics:
        - Combo meals (multiple items bundled)
        - Special pricing mentioned in the title
        - "For Rs." pricing pattern (indicates a special price)
        """
        title = item.get("title", "").lower()
        source = item.get("source_page", "")

        # Items from the promotions page are definitively deals
        if "promotions" in source:
            return True

        # Items from meal pages that are combos/bundles are deals
        if "meals" in source or "beverages" in source:
            deal_keywords = ["combo", "meal", "bundle", "for rs", "special", "offer", "deal",
                             "save", "free", "bucket"]
            if any(kw in title for kw in deal_keywords):
                return True
            # Combos with drinks are deals
            if "+" in title or "pepsi" in title or "drink" in title:
                return True

        # Items with "FOR RS." in the title indicate special pricing
        if "for rs" in title:
            return True

        return False

    def _validate_deals(self, new_deals: List[Dict], cached_deals: List[Dict]) -> bool:
        """
        Validate that the scraped deals are reasonable.
        Returns True if the deals pass validation and should be saved.
        """
        if len(new_deals) == 0:
            logger.warning("KFC: Scrape returned 0 deals — refusing to overwrite cache")
            return False

        if len(new_deals) < MIN_EXPECTED_DEALS:
            logger.warning(f"KFC: Only {len(new_deals)} deals found (minimum: {MIN_EXPECTED_DEALS})")
            # Still accept if we have no cache
            if not cached_deals:
                return True
            return False

        # Check for a huge unexplained drop in deals
        if cached_deals and len(cached_deals) > 0:
            ratio = len(new_deals) / len(cached_deals)
            if ratio < MAX_DEAL_DROP_RATIO:
                logger.warning(
                    f"KFC: Deal count dropped from {len(cached_deals)} to {len(new_deals)} "
                    f"(ratio {ratio:.2f} < {MAX_DEAL_DROP_RATIO}) — refusing to overwrite"
                )
                return False

        # Check for duplicate titles
        titles = [d.get("title", "") for d in new_deals]
        unique_titles = set(titles)
        if len(unique_titles) < len(titles) * 0.5:
            logger.warning("KFC: More than 50% duplicate titles detected — data may be corrupt")
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
                logger.warning(f"KFC: Failed to read cache: {e}")
        return []

    def _save_cache(self, deals: List[Dict]) -> None:
        """Save deals to the cache file."""
        try:
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            logger.info(f"KFC: Cached {len(deals)} deals to {CACHE_FILE}")
        except IOError as e:
            logger.warning(f"KFC: Failed to write cache: {e}")

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Scrape KFC Sri Lanka deals using direct HTTP requests to parse server-rendered HTML.

        Strategy:
        1. Fetch the /menu/promotions page for explicit promotions
        2. Fetch /menu/meals-and-beverages for combo/meal deals
        3. Parse the HTML for product cards using the itemContainer structure
        4. Filter to only include promotional deals (not regular menu items)
        5. Validate results before saving to cache
        6. Fall back to cache if the live scrape fails validation
        """
        session = self._get_session()
        all_items = []
        seen_titles = set()

        # Scrape both promo and deal pages
        pages_to_scrape = KFC_PROMO_PAGES + KFC_DEAL_PAGES

        for page_path in pages_to_scrape:
            html = self._fetch_page(session, page_path)
            if not html:
                continue

            items = self._extract_items_from_html(html, page_path)
            logger.info(f"KFC: Extracted {len(items)} items from {page_path}")

            for item in items:
                title = item["title"]

                # Deduplicate by title
                title_key = title.lower().strip()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                # Only include items that are actual deals/promos
                if not self._is_promotional_deal(item):
                    logger.debug(f"KFC: Skipping non-deal item: {title}")
                    continue

                category = self._determine_category(title, item["description"], item["source_page"])
                stable_id = self._generate_stable_id(title, item["source_page"])

                offer = {
                    "id": stable_id,
                    "title": title,
                    "description": f"KFC Sri Lanka: {item['description']}",
                    "category": category,
                    "image_url": item["image_url"],
                    "deal_type": "Special Promotion" if "promotions" in item["source_page"] else "Meal Deal",
                    "valid_until": "Limited Time",
                    "source_url": f"https://www.kfc.lk{item['source_page']}",
                    "location": "island-wide",
                }

                if item["price"] is not None and item["price"] > 0:
                    offer["discounted_price"] = item["price"]

                all_items.append(offer)

        # Sort for deterministic output
        all_items.sort(key=lambda x: (x["category"], x["title"]))

        # Validate against cache
        cached = self._load_cache()

        if self._validate_deals(all_items, cached):
            self._save_cache(all_items)
            logger.info(f"KFC: Successfully scraped {len(all_items)} deals")
            return all_items
        else:
            if cached:
                logger.info(f"KFC: Using {len(cached)} cached deals (live scrape failed validation)")
                return cached
            else:
                logger.warning("KFC: No cached deals available and live scrape failed validation")
                return all_items  # Return what we have even if it's suspect
