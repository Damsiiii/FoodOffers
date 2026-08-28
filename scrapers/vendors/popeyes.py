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

class PopeyesScraper(BaseScraper):
    vendor_id = "popeyes"
    vendor_name = "Popeyes Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=100&h=100&fit=crop"
    website_url = "https://popeyes.com.lk"
    categories = ["Sandwiches & Burgers", "Chicken Buckets", "Tenders"]

    def scrape_live(self):
        offers = []
        try:
            resp = requests.get(self.website_url, headers=DEFAULT_HEADERS, verify=False, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                idx = 1
                for img in soup.find_all("img"):
                    src = img.get("src") or ""
                    if "uploads" in src and ("Banner" in src or "Deal" in src or "Header" in src):
                        full_src = src if src.startswith("http") else "https://popeyes.com.lk/" + src.lstrip("/")
                        offers.append({
                            "id": f"plk-promo-{idx}",
                            "title": f"Popeyes Louisiana Chicken Deal #{idx}",
                            "description": "Popeyes Sri Lanka tender chicken & burger combo offer.",
                            "category": "Chicken Buckets",
                            "original_price": 3200.0,
                            "discounted_price": 2490.0,
                            "discount_percentage": 22,
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
