import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class DinemoreScraper(BaseScraper):
    vendor_id = "dinemore"
    vendor_name = "Dinemore Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=100&h=100&fit=crop"
    website_url = "https://dinemore.lk"
    categories = ["Subs & Grills", "Family Platter", "Fried Rice"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        return fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
