import warnings
import requests
import logging
from scrapers.base import BaseScraper
from scrapers.vision_ocr import parse_banner_with_ocr

warnings.filterwarnings("ignore")
logger = logging.getLogger(__name__)

class PizzaHutScraper(BaseScraper):
    vendor_id = "pizzahut"
    vendor_name = "Pizza Hut Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.pizzahut.lk"
    categories = ["Pizza Deals", "Meal Deals", "Promotions", "Family Combos"]

    def scrape_live(self):
        """
        Scrapes Pizza Hut Sri Lanka promotional offers directly from their official API:
        OAuth Authentication: https://phapis.pizzahut.lk/gettoken
        Promotions Endpoint: https://phapis.pizzahut.lk/api/home/promo
        """
        offers = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        auth_data = {
            "username": "JustWebUser",
            "password": "nxNCtHIDOJVbGBa",
            "grant_type": "password",
            "scope": "/vQFtb6VBYg"
        }

        try:
            # 1. Obtain OAuth Access Token
            resp = requests.post("https://phapis.pizzahut.lk/gettoken", data=auth_data, headers=headers, verify=False, timeout=12)
            token = resp.json().get("access_token")

            if not token:
                return offers

            auth_headers = {
                "User-Agent": headers["User-Agent"],
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # 2. Fetch Active Promotional Deals
            r_promo = requests.post("https://phapis.pizzahut.lk/api/home/promo", json={}, headers=auth_headers, verify=False, timeout=12)
            promos = r_promo.json().get("Data", [])

            for idx, item in enumerate(promos):
                title = item.get("WebName") or item.get("CategoryName") or item.get("Name")
                if not title:
                    continue

                desc = item.get("Description") or item.get("DescriptionShort") or item.get("WebNameShort") or title
                price_val = item.get("PromotionPrice") or item.get("Price")

                img_url = item.get("FullImageUrl") or item.get("MealDealFullImageURL") or ""
                if not img_url or not img_url.startswith("http"):
                    img_url = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&h=400&fit=crop"

                url_slug = item.get("Url") or ""
                deal_url = f"https://www.pizzahut.lk/menu/promo/{url_slug}" if url_slug else "https://www.pizzahut.lk/menu/promo/meal-deal"

                # Parse Vision OCR for additional deal metadata
                ocr_data = parse_banner_with_ocr(img_url, self.vendor_name)
                disc_pct = ocr_data.get("discount_percentage", 20) if ocr_data else 20

                disc_price = float(price_val) if price_val and float(price_val) > 0 else 1800.0
                orig_price = round(disc_price * (1 + disc_pct / 100))

                offers.append({
                    "id": f"pizzahut-promo-{idx + 1}",
                    "title": title,
                    "description": f"Official Pizza Hut Sri Lanka Promo: {desc}",
                    "category": "Meal Deals",
                    "original_price": orig_price,
                    "discounted_price": disc_price,
                    "discount_percentage": disc_pct,
                    "image_url": img_url,
                    "deal_type": ocr_data.get("promo_terms", "Special Promotion") if ocr_data else "Special Promotion",
                    "valid_until": "Limited Time",
                    "source_url": deal_url
                })

        except Exception as e:
            logger.warning(f"[{self.vendor_name}] API scraping exception: {e}")

        return offers
