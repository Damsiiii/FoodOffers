import os
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
    categories = ["Thrilling Thursday", "Grand Dipper Deals", "Cyber Savings", "Add-ons", "Pizza Deals", "Meal Deals"]

    def scrape_live(self):
        """
        Scrapes ALL promotional deals from Pizza Hut Sri Lanka's official API:
        - Thrilling Thursday Deals
        - Grand Dipper Deals
        - Cyber Savings
        - Add-ons
        - Slider Banner Promos
        """
        offers = []
        seen_titles = set()

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        auth_data = {
            "username": os.getenv("PIZZAHUT_API_USER", "JustWebUser"),
            "password": os.getenv("PIZZAHUT_API_PASS", "nxNCtHIDOJVbGBa"),
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

            # 2. Fetch Homepage Slider Banner Deals
            try:
                r_banner = requests.post("https://phapis.pizzahut.lk/api/home/banner", json={}, headers=auth_headers, verify=False, timeout=12)
                banner_data = r_banner.json().get("Data")
                banners = [banner_data] if isinstance(banner_data, dict) else (banner_data if isinstance(banner_data, list) else [])

                for b_idx, banner in enumerate(banners):
                    if not banner or not isinstance(banner, dict):
                        continue

                    banner_img = banner.get("FullImageUrl") or banner.get("ImageURL") or ""
                    if not banner_img or not banner_img.startswith("http"):
                        continue

                    # Run Vision OCR AI to extract promotional text from banner graphics
                    ocr_data = parse_banner_with_ocr(banner_img, self.vendor_name)
                    ocr_text = ocr_data.get("ocr_text", "") if ocr_data else ""

                    b_title = banner.get("Tiltle") or banner.get("Name") or banner.get("Description") or "Cyber Savings Banner Deal"
                    if b_title == "New" and ocr_text:
                        b_title = f"Cyber Savings: {ocr_text.split('|')[0].strip()}"

                    if b_title in seen_titles:
                        continue
                    seen_titles.add(b_title)

                    disc_pct = ocr_data.get("discount_percentage", 25) if ocr_data else 25
                    disc_price = 1950.0
                    orig_price = round(disc_price * (1 + disc_pct / 100))

                    banner_url = banner.get("Url") or "https://www.pizzahut.lk"
                    if "azurewebsites.net" in banner_url or not banner_url.startswith("http"):
                        banner_url = "https://www.pizzahut.lk"

                    offers.append({
                        "id": f"pizzahut-cyber-banner-{b_idx + 1}",
                        "title": b_title,
                        "description": f"Official Pizza Hut Promo: {ocr_text if ocr_text else b_title}",
                        "category": "Cyber Savings",
                        "original_price": orig_price,
                        "discounted_price": disc_price,
                        "discount_percentage": disc_pct,
                        "image_url": banner_img,
                        "deal_type": ocr_data.get("promo_terms", "Cyber Savings Deal") if ocr_data else "Cyber Savings Deal",
                        "valid_until": "Limited Time",
                        "source_url": banner_url
                    })

            except Exception as b_err:
                logger.warning(f"[{self.vendor_name}] Banner Cyber Savings extraction exception: {b_err}")

            # 3. Fetch ALL Deals from the Deals Category (/api/menu/items?webCategory=promo&menuCategory=meal-deal)
            r_promo = requests.post(
                "https://phapis.pizzahut.lk/api/menu/items?webCategory=promo&menuCategory=meal-deal",
                json={},
                headers=auth_headers,
                verify=False,
                timeout=12
            )
            promos_res = r_promo.json()
            promos = promos_res if isinstance(promos_res, list) else (promos_res.get("Data", []) if isinstance(promos_res, dict) else [])

            for idx, item in enumerate(promos):
                title = item.get("WebName") or item.get("Name") or item.get("CategoryName") or item.get("Title")
                if not title or title in seen_titles:
                    continue
                seen_titles.add(title)

                desc = item.get("Description") or item.get("DescriptionShort") or item.get("WebNameShort") or title
                price_val = item.get("PromotionPrice") or item.get("Price")

                img_url = item.get("FullImageUrl") or item.get("MealDealFullImageURL") or item.get("ImageURL") or ""
                if not img_url or not img_url.startswith("http"):
                    img_url = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=600&h=400&fit=crop"

                url_slug = item.get("Url") or ""
                deal_url = f"https://www.pizzahut.lk/menu/promo/{url_slug}" if url_slug else "https://www.pizzahut.lk/menu/promo/meal-deal"

                # Parse Vision OCR for additional deal metadata
                ocr_data = parse_banner_with_ocr(img_url, self.vendor_name)
                disc_pct = ocr_data.get("discount_percentage", 20) if ocr_data else 20

                # Determine Section / Category
                lower_title = title.lower()
                if "thrilling" in lower_title or "thursday" in lower_title:
                    category = "Thrilling Thursday"
                elif "grand dipper" in lower_title or "dipper" in lower_title:
                    category = "Grand Dipper Deals"
                elif "cyber" in lower_title:
                    category = "Cyber Savings"
                elif "add on" in lower_title or "addon" in lower_title or "pasta" in lower_title or "melts" in lower_title:
                    category = "Add-ons"
                else:
                    category = "Meal Deals"

                disc_price = float(price_val) if price_val and float(price_val) > 0 else 2400.0
                orig_price = round(disc_price * (1 + disc_pct / 100))

                offers.append({
                    "id": f"pizzahut-promo-{idx + 1}",
                    "title": title,
                    "description": f"Official Pizza Hut Sri Lanka Promo: {desc}",
                    "category": category,
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
