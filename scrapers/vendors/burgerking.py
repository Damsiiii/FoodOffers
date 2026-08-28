import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class BurgerKingScraper(BaseScraper):
    vendor_id = "burgerking"
    vendor_name = "Burger King Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=100&h=100&fit=crop"
    website_url = "https://burgerking.lk"
    categories = ["Burgers", "Family Combos", "King Savers"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
