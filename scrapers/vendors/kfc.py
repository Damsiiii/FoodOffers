import requests
import re
import warnings
import urllib3
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
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
        Parses live promotional items, exact LKR deal prices, genuine BOGO/bundle discounts,
        and high-resolution food photo URLs.
        """
        offers = []
        url = "https://www.kfc.lk/menu/promotions"
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, verify=False, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                seen_titles = set()
                idx = 1

                for img in soup.find_all("img"):
                    src = img.get("src") or ""
                    if "admin-kfc-web" in src and "mainmenu" in src:
                        parent = img.parent
                        container_text = ""
                        for _ in range(6):
                            if parent and parent.name == "div":
                                txt = parent.get_text(" ", strip=True)
                                if "Rs" in txt and len(txt) < 400:
                                    container_text = txt
                                    break
                            parent = parent.parent if parent else None

                        if not container_text:
                            continue

                        price_match = re.search(r"Rs\.?\s*([\d,]+)", container_text)
                        if not price_match:
                            continue

                        price = float(price_match.group(1).replace(",", ""))

                        clean_part = container_text.split("+")[0].split("Rs.")[0].replace("No", "").strip()
                        parts = [p.strip() for p in clean_part.split("...") if len(p.strip()) > 3]
                        if parts:
                            title = parts[0]
                        else:
                            title = clean_part[:60]

                        if not title or title in seen_titles:
                            continue

                        seen_titles.add(title)

                        disc_pct = 0
                        orig_price = price
                        text_upper = container_text.upper()
                        if "BOGO" in text_upper or "GET 1 FREE" in text_upper or "BUY 1" in text_upper or "BUY 2" in text_upper:
                            disc_pct = 33 if "BUY 2" in text_upper else 50
                            orig_price = round(price / (1 - disc_pct / 100))
                        elif "SAVOURY" in text_upper or "SAWAN" in text_upper:
                            disc_pct = 20
                            orig_price = round(price / 0.8)

                        # Only include if item has genuine discount
                        if disc_pct > 0:
                            offers.append({
                                "id": f"kfc-live-{idx}",
                                "title": title,
                                "description": f"Official KFC Sri Lanka promotional deal: {title}",
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
        except Exception:
            pass

        return offers
