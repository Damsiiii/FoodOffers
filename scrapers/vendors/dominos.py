import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class DominosScraper(BaseScraper):
    vendor_id = "dominos"
    vendor_name = "Domino's Pizza Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.dominos.lk"
    categories = ["Value Combos", "Pizza Deals", "Sides", "Desserts"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
