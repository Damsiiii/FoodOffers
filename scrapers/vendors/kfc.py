import re
import requests
import warnings
from bs4 import BeautifulSoup
from scrapers.base import BaseScraper

warnings.filterwarnings("ignore")

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Bucket Deals", "Combos", "Rice Meals", "Burgers", "Snacks"]

    def scrape_live(self):
        from scrapers.browser import fetch_dynamic_deals
        offers = fetch_dynamic_deals(self.website_url, self.vendor_id, self.vendor_name)
        return offers
