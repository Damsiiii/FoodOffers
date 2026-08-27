import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class BreadTalkScraper(BaseScraper):
    vendor_id = "breadtalk"
    vendor_name = "BreadTalk Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=100&h=100&fit=crop"
    website_url = "https://breadtalk.lk"
    categories = ["Pastries & Bread", "Cakes & Desserts", "Flosss Buns"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        return fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
