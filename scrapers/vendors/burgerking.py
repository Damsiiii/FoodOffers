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

class BurgerKingScraper(BaseScraper):
    vendor_id = "burgerking"
    vendor_name = "Burger King Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=100&h=100&fit=crop"
    website_url = "https://burgerking.lk"
    categories = ["Burgers", "Family Combos", "King Savers"]

    def scrape_live(self):
        offers = []
        try:
            from scrapers.browser import intercept_api_deals
            offers = intercept_api_deals("https://burgerking.lk", self.vendor_id, self.vendor_name)
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
                        if "uploads" in src and ("Header_Banner" in src or "Saver" in src) and not "LOGO" in src:
                            full_src = src if src.startswith("http") else "https://burgerking.lk/" + src.lstrip("/")
                            title = alt.strip() if alt and len(alt) > 3 else "Burger King Promotional Deal"
                            offers.append({
                                "id": f"bk-promo-{idx}",
                                "title": title,
                                "description": "Burger King Sri Lanka special promotional offer.",
                                "category": "King Savers",
                                "image_url": full_src,
                                "deal_type": "Official Banner",
                                "valid_until": "Limited Time",
                                "source_url": self.website_url,
                                "location": "colombo"
                            })
                            idx += 1
            except Exception:
                pass
        return offers
