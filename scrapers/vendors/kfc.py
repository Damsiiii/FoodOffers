import re
import requests
import warnings
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Bucket Deals", "Combos", "Rice Meals", "Burgers", "Snacks"]

    def scrape_live(self):
        url = "https://www.kfc.lk"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            resp = requests.get(url, headers=headers, timeout=8)
        except Exception:
            return []
        if resp.status_code != 200:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        offers = []
        cards = soup.find_all(class_=re.compile(r"card|item|product|promo|deal", re.I))
        idx = 1
        for card in cards:
            title_elem = card.find(["h2", "h3", "h4", "h5", "strong", "span"])
            price_elem = card.find(string=re.compile(r"Rs\.?|LKR|\b\d{3,5}\b", re.I))
            if title_elem and price_elem:
                title = title_elem.get_text(strip=True)
                if len(title) > 3:
                    price_match = re.search(r"(\d[\d,]+)", str(price_elem))
                    if price_match:
                        price = float(price_match.group(1).replace(",", ""))
                        offers.append({
                            "id": f"kfc-live-{idx}",
                            "title": title,
                            "description": f"Featured KFC deal: {title}",
                            "category": "Promotions",
                            "original_price": round(price * 1.15),
                            "discounted_price": price,
                            "discount_percentage": 13,
                            "image_url": "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=500&fit=crop",
                            "deal_type": "Live Offer",
                            "valid_until": "Limited Time",
                            "source_url": url
                        })
                        idx += 1
        return offers
