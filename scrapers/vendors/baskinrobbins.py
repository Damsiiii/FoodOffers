import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class BaskinRobbinsScraper(BaseScraper):
    vendor_id = "baskinrobbins"
    vendor_name = "Baskin-Robbins Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=100&h=100&fit=crop"
    website_url = "https://baskinrobbins.lk"
    categories = ["Ice Cream & Desserts", "Ice Cream Packs", "Sundaes"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
