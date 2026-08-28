import requests
import warnings
import urllib3
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore")

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
}

class BreadTalkScraper(BaseScraper):
    vendor_id = "breadtalk"
    vendor_name = "BreadTalk Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=100&h=100&fit=crop"
    website_url = "https://breadtalk.lk"
    categories = ["Pastries & Bread", "Cakes & Desserts", "Flosss Buns"]

    def scrape_live(self):
        offers = []
        try:
            from scrapers.browser import intercept_api_deals
            offers = intercept_api_deals("https://breadtalk.lk/shop/", self.vendor_id, self.vendor_name)
        except Exception:
            pass

        if not offers:
            try:
                resp = requests.get(self.website_url, headers=DEFAULT_HEADERS, verify=False, timeout=8)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    idx = 1
                    for img in soup.find_all("img"):
                        src = img.get("src") or ""
                        alt = img.get("alt") or ""
                        if src.startswith("http") and ("bundle" in src.lower() or "slider" in src.lower()):
                            title = alt.strip() if alt and len(alt) > 3 and not "removebg" in alt else "BreadTalk Pastry Bundle"
                            offers.append({
                                "id": f"bt-promo-{idx}",
                                "title": title,
                                "description": "BreadTalk Sri Lanka artisan bakery bundle promotion.",
                                "category": "Pastries & Bread",
                                "original_price": 1450.0,
                                "discounted_price": 1450.0,
                                "discount_percentage": 0,
                                "image_url": src,
                                "deal_type": "Official Banner",
                                "valid_until": "Limited Time",
                                "source_url": self.website_url
                            })
                            idx += 1
            except Exception:
                pass
        return offers
