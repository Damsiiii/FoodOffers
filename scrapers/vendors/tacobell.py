import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class TacoBellScraper(BaseScraper):
    vendor_id = "tacobell"
    vendor_name = "Taco Bell Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=100&h=100&fit=crop"
    website_url = "https://www.tacobell.lk"
    categories = ["Tacos & Burritos", "Combos", "Loaded Nachos"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
