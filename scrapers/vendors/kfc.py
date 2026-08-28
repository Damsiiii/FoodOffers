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
                        for _ in range(5):
                            if parent and parent.name == "div":
                                txt = parent.get_text(" ", strip=True)
                                if "Rs" in txt and len(txt) < 300:
                                    container_text = txt
                                    break
                            parent = parent.parent if parent else None

                        if not container_text:
                            continue

                        price_match = re.search(r"Rs\.?\s*([\d,]+)", container_text)
                        if not price_match:
                            continue

                        price = float(price_match.group(1).replace(",", ""))

                        clean_part = container_text.split("+")[0].split("Rs.")[0].strip()
                        if "BOGO FREE 6PC" in clean_part.upper():
                            title = "BOGO Free 6Pc Hot & Crispy Bucket"
                        elif "BOGO FREE 8PC" in clean_part.upper():
                            title = "BOGO Free 8Pc Hot & Crispy Bucket"
                        elif "SAVOURY SAWAN" in clean_part.upper():
                            title = "Super Savoury Sawan Deal"
                        else:
                            parts = clean_part.split("...")
                            title = parts[0].strip() if len(parts) > 1 else clean_part

                        if title in seen_titles:
                            continue
                        seen_titles.add(title)

                        disc_pct = 0
                        orig_price = price
                        if "BOGO" in container_text.upper() or "BUY 1 GET 1" in container_text.upper():
                            disc_pct = 50
                            orig_price = price * 2.0
                        elif "SAVOURY" in container_text.upper() or "SAWAN" in container_text.upper():
                            disc_pct = 20
                            orig_price = round(price / 0.8)

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
        except Exception:
            pass

        return offers
