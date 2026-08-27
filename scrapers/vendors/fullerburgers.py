import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class FullerBurgersScraper(BaseScraper):
    vendor_id = "fullerburgers"
    vendor_name = "Fuller Burgers"
    vendor_logo = "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=100&h=100&fit=crop"
    website_url = "https://fullerburgers.com"
    categories = ["Artisanal Burgers", "Smash Burgers", "Fries & Sides"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        return fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
