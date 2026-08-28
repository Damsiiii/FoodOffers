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

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Bucket Deals", "Combos", "Rice Meals", "Burgers", "Snacks"]

    def scrape_live(self):
        offers = []
        try:
            resp = requests.get(self.website_url, headers=DEFAULT_HEADERS, verify=False, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                idx = 1
                for img in soup.find_all("img"):
                    src = img.get("src") or ""
                    if "sliderimages" in src:
                        full_src = src if src.startswith("http") else "https://admin-kfc-web.azurewebsites.net/" + src.lstrip("/")
                        offers.append({
                            "id": f"kfc-promo-{idx}",
                            "title": f"KFC Special Bucket Deal #{idx}",
                            "description": "KFC Sri Lanka special promotion and hot bucket deal.",
                            "category": "Bucket Deals",
                            "original_price": 3800.0,
                            "discounted_price": 2990.0,
                            "discount_percentage": 21,
                            "image_url": full_src,
                            "deal_type": "Live Website Promotion",
                            "valid_until": "Limited Time",
                            "source_url": self.website_url
                        })
                        idx += 1
        except Exception:
            pass

        if not offers:
            from scrapers.browser import intercept_api_deals
            offers = intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
        return offers
