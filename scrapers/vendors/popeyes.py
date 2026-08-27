import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class PopeyesScraper(BaseScraper):
    vendor_id = "popeyes"
    vendor_name = "Popeyes Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=100&h=100&fit=crop"
    website_url = "https://popeyes.com.lk"
    categories = ["Sandwiches & Burgers", "Chicken Buckets", "Tenders"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        return fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
