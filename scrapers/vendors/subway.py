import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class SubwayScraper(BaseScraper):
    vendor_id = "subway"
    vendor_name = "Subway Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1509722747041-616f39b57569?w=100&h=100&fit=crop"
    website_url = "https://subway.lk"
    categories = ["Submarines & Wraps", "Share Packs", "Salads"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
