import warnings
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class CrepeRunnerScraper(BaseScraper):
    vendor_id = "creperunner"
    vendor_name = "Crepe Runner"
    vendor_logo = "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=100&h=100&fit=crop"
    website_url = "https://creperunner.lk"
    categories = ["Sweet Crepes", "Savory Crepes", "Beverages"]

    def scrape_live(self):
        from scrapers.browser import intercept_api_deals
        return intercept_api_deals(self.website_url, self.vendor_id, self.vendor_name)
