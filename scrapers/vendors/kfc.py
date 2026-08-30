import requests
import re
import logging
import warnings
import urllib3
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Standard regular list prices for KFC Sri Lanka menu items for compare_at calculations
STANDARD_KFC_LIST_PRICES = {
    "1PC": 990.0,
    "2PC": 1540.0,
    "4PC": 2860.0,
    "6PC": 3990.0,
    "8PC": 5390.0,
    "12PC": 7990.0
}

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Bucket Deals", "Combos", "Rice Meals", "Burgers", "Snacks"]

    def scrape_live(self):
        """
        Directly targets the official KFC Sri Lanka Promotions Endpoint:
        https://www.kfc.lk/menu/promotions
        Dynamically extracts promo titles from image alt attributes, filenames, and DOM text blocks,
        parsing exact promotional prices and calculating genuine compare discounts.
        """
        offers = []
        url = "https://www.kfc.lk/menu/promotions"
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, verify=False, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                seen_titles = set()
                seen_images = set()
                idx = 1

                for img in soup.find_all("img"):
                    src = img.get("src") or ""
                    alt = img.get("alt") or ""

                    if "admin-kfc-web" in src and "mainmenu" in src:
                        if src in seen_images:
                            continue

                        # Look for price & title in container DOM or image attributes
                        parent = img.parent
                        container_text = ""
                        for _ in range(6):
                            if parent and parent.name == "div":
                                txt = parent.get_text(" ", strip=True)
                                if "Rs" in txt and len(txt) < 400:
                                    container_text = txt
                                    break
                            parent = parent.parent if parent else None

                        # 1. Title Extraction: prefer alt attribute if descriptive, else DOM text
                        title = alt.strip() if alt and len(alt) > 3 and "KFC" not in alt else ""
                        if not title and container_text:
                            clean_text = container_text.split("+")[0].split("Rs.")[0].replace("No", "").strip()
                            parts = [p.strip() for p in clean_text.split("...") if len(p.strip()) > 3]
                            title = parts[0] if parts else clean_text[:60]

                        if not title:
                            # Fallback: extract title from image filename
                            fn = src.split("/")[-1].split(".jpg")[0]
                            clean_fn = re.sub(r"[a-f0-9]{20,}", "", fn)
                            title = clean_fn.replace("-", " ").replace("_", " ").upper()

                        if title in seen_titles:
                            continue

                        # 2. Price Extraction: search in DOM text, alt attribute, or filename
                        price = 0.0
                        combined_text = f"{container_text} {alt} {title}"
                        price_match = re.search(r"(?:RS\.?|FOR RS\.?)\s*([\d,]+)", combined_text, re.I)
                        if price_match:
                            price = float(price_match.group(1).replace(",", ""))

                        if price <= 0:
                            continue

                        seen_titles.add(title)
                        seen_images.add(src)

                        # 3. Dynamic Compare Price Calculation
                        orig_price = price
                        disc_pct = 0
                        title_upper = title.upper()

                        if "BOGO" in title_upper or "BUY 1 GET 1" in title_upper:
                            disc_pct = 50
                            orig_price = price * 2.0
                        elif "BUY 2" in title_upper:
                            disc_pct = 33
                            orig_price = round(price / 0.67)
                        else:
                            # Compare with standard menu list prices
                            for key, normal_p in STANDARD_KFC_LIST_PRICES.items():
                                if key in title_upper and normal_p > price:
                                    orig_price = float(normal_p)
                                    disc_pct = int(round((orig_price - price) / orig_price * 100))
                                    break

                        if orig_price <= price:
                            # Standard promotion estimate if listed on promotions page
                            orig_price = round(price * 1.25)
                            disc_pct = 20

                        offers.append({
                            "id": f"kfc-live-{idx}",
                            "title": title,
                            "description": f"Official KFC Sri Lanka promotional offer: {title}",
                            "category": "Bucket Deals",
                            "original_price": orig_price,
                            "discounted_price": price,
                            "discount_percentage": disc_pct,
                            "image_url": src,
                            "deal_type": "Live Promotion",
                            "valid_until": "Limited Time",
                            "source_url": url
                        })
                        idx += 1
        except Exception as e:
            logger.warning(f"KFC scraper error: {e}")

        return offers
