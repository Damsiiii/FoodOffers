import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class PereraAndSonsScraper(BaseScraper):
    vendor_id = "pereraandsons"
    vendor_name = "Perera & Sons (P&S)"
    vendor_logo = "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=100&h=100&fit=crop"
    website_url = "https://pns.lk"
    categories = ["Short Eats & Bakery", "Rice & Lamprais", "Sweets"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        return fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
