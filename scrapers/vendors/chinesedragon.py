import requests
import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class ChineseDragonScraper(BaseScraper):
    vendor_id = "chinesedragon"
    vendor_name = "Chinese Dragon Cafe"
    vendor_logo = "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=100&h=100&fit=crop"
    website_url = "https://chinesedragoncafe.com"
    categories = ["Chinese Family Meals", "Express Lunch", "Seafood Special"]

    def scrape_live(self):
        url = "https://chinesedragoncafe.com/products.json"
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=8)
            if resp.status_code != 200:
                return []
            data = resp.json()
            offers = []
            for p in data.get("products", []):
                title = p.get("title")
                variants = p.get("variants", [])
                if not title or not variants:
                    continue
                price = float(variants[0].get("price", 0))
                if price <= 0:
                    continue
                compare_at_price_raw = variants[0].get("compare_at_price")
                if compare_at_price_raw:
                    try:
                        compare_at = float(compare_at_price_raw)
                        if compare_at > price:
                            orig_price = compare_at
                            disc_pct = int(round((orig_price - price) / orig_price * 100))
                        else:
                            orig_price = price
                            disc_pct = 0
                    except (ValueError, TypeError):
                        orig_price = price
                        disc_pct = 0
                else:
                    orig_price = price
                    disc_pct = 0

                img = p["images"][0]["src"] if p.get("images") else "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=500&fit=crop"
                offers.append({
                    "id": f"cdc-live-{p['id']}",
                    "title": title,
                    "description": f"Chinese Dragon Cafe special: {title}",
                    "category": p.get("product_type") or "Chinese Family Meals",
                    "original_price": orig_price,
                    "discounted_price": price,
                    "discount_percentage": disc_pct,
                    "image_url": img,
                    "deal_type": "Live Offer",
                    "valid_until": "Limited Time",
                    "source_url": f"https://chinesedragoncafe.com/products/{p.get('handle', '')}"
                })
            return offers
        except Exception:
            return []
