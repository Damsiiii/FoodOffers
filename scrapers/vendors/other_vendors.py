import requests
from scrapers.base import BaseScraper

class PizzaHutScraper(BaseScraper):
    vendor_id = "pizzahut"
    vendor_name = "Pizza Hut Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.pizzahut.lk"
    categories = ["Pizza Deals", "Family Combos", "Solo Meals", "Sides", "Desserts"]

    def scrape_live(self):
        return []

class DominosScraper(BaseScraper):
    vendor_id = "dominos"
    vendor_name = "Domino's Pizza Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.dominos.lk"
    categories = ["Value Combos", "Pizza Deals", "Sides", "Desserts"]

    def scrape_live(self):
        return []

class TacoBellScraper(BaseScraper):
    vendor_id = "tacobell"
    vendor_name = "Taco Bell Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=100&h=100&fit=crop"
    website_url = "https://www.tacobell.lk"
    categories = ["Tacos & Burritos", "Combos", "Loaded Nachos"]

    def scrape_live(self):
        return []

class BurgerKingScraper(BaseScraper):
    vendor_id = "burgerking"
    vendor_name = "Burger King Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=100&h=100&fit=crop"
    website_url = "https://burgerking.lk"
    categories = ["Burgers", "Family Combos", "King Savers"]

    def scrape_live(self):
        return []

class PopeyesScraper(BaseScraper):
    vendor_id = "popeyes"
    vendor_name = "Popeyes Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=100&h=100&fit=crop"
    website_url = "https://popeyes.lk"
    categories = ["Sandwiches & Burgers", "Chicken Buckets", "Tenders"]

    def scrape_live(self):
        return []

class FullerBurgersScraper(BaseScraper):
    vendor_id = "fullerburgers"
    vendor_name = "Fuller Burgers"
    vendor_logo = "https://images.unsplash.com/photo-1586190848861-99aa4a171e90?w=100&h=100&fit=crop"
    website_url = "https://fullerburgers.com"
    categories = ["Artisanal Burgers", "Smash Burgers", "Fries & Sides"]

    def scrape_live(self):
        return []

class CrepeRunnerScraper(BaseScraper):
    vendor_id = "creperunner"
    vendor_name = "Crepe Runner"
    vendor_logo = "https://images.unsplash.com/photo-1519676867240-f03562e64548?w=100&h=100&fit=crop"
    website_url = "https://creperunner.lk"
    categories = ["Sweet Crepes", "Savory Crepes", "Beverages"]

    def scrape_live(self):
        return []

class SubwayScraper(BaseScraper):
    vendor_id = "subway"
    vendor_name = "Subway Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1509722747041-616f39b57569?w=100&h=100&fit=crop"
    website_url = "https://subway.lk"
    categories = ["Submarines & Wraps", "Share Packs", "Salads"]

    def scrape_live(self):
        return []

class DinemoreScraper(BaseScraper):
    vendor_id = "dinemore"
    vendor_name = "Dinemore Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=100&h=100&fit=crop"
    website_url = "https://dinemore.lk"
    categories = ["Subs & Grills", "Family Platter", "Fried Rice"]

    def scrape_live(self):
        return []

class PereraAndSonsScraper(BaseScraper):
    vendor_id = "pereraandsons"
    vendor_name = "Perera & Sons (P&S)"
    vendor_logo = "https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=100&h=100&fit=crop"
    website_url = "https://pereraandsons.com"
    categories = ["Short Eats & Bakery", "Rice & Lamprais", "Sweets"]

    def scrape_live(self):
        return []

class ChineseDragonScraper(BaseScraper):
    vendor_id = "chinesedragon"
    vendor_name = "Chinese Dragon Cafe"
    vendor_logo = "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=100&h=100&fit=crop"
    website_url = "https://chinesedragoncafe.com"
    categories = ["Chinese Family Meals", "Express Lunch", "Seafood Special"]

    def scrape_live(self):
        return []

class BaskinRobbinsScraper(BaseScraper):
    vendor_id = "baskinrobbins"
    vendor_name = "Baskin-Robbins Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=100&h=100&fit=crop"
    website_url = "https://baskinrobbins.lk"
    categories = ["Ice Cream & Desserts", "Ice Cream Packs", "Sundaes"]

    def scrape_live(self):
        return []

class BreadTalkScraper(BaseScraper):
    vendor_id = "breadtalk"
    vendor_name = "BreadTalk Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1509440159596-0249088772ff?w=100&h=100&fit=crop"
    website_url = "https://breadtalk.lk"
    categories = ["Pastries & Bread", "Cakes & Desserts", "Flosss Buns"]

    def scrape_live(self):
        return []
