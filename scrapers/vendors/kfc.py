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
            from scrapers.browser import intercept_api_deals
            offers = intercept_api_deals("https://www.kfc.lk/menu", self.vendor_id, self.vendor_name)
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
                        if "sliderimages" in src:
                            full_src = src if src.startswith("http") else "https://admin-kfc-web.azurewebsites.net/" + src.lstrip("/")
                            title = alt.strip() if alt and len(alt) > 3 and "KFC" not in alt else f"KFC Promotional Bucket Deal"
                            offers.append({
                                "id": f"kfc-promo-{idx}",
                                "title": title,
                                "description": f"KFC Sri Lanka official promotional banner deal.",
                                "category": "Bucket Deals",
                                "original_price": 2860.0,
                                "discounted_price": 2860.0,
                                "discount_percentage": 0,
                                "image_url": full_src,
                                "deal_type": "Official Banner",
                                "valid_until": "Limited Time",
                                "source_url": self.website_url
                            })
                            idx += 1
            except Exception:
                pass
        return offers
