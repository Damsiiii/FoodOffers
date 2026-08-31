import logging
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from scrapers.vendors.kfc import KFCScraper
from scrapers.vendors.pizzahut import PizzaHutScraper
from scrapers.vendors.dominos import DominosScraper
from scrapers.vendors.tacobell import TacoBellScraper
from scrapers.vendors.burgerking import BurgerKingScraper
from scrapers.vendors.popeyes import PopeyesScraper
from scrapers.vendors.fullerburgers import FullerBurgersScraper
from scrapers.vendors.creperunner import CrepeRunnerScraper
from scrapers.vendors.subway import SubwayScraper
from scrapers.vendors.dinemore import DinemoreScraper
from scrapers.vendors.chinesedragon import ChineseDragonScraper
from scrapers.vendors.breadtalk import BreadTalkScraper
from scrapers.vendors.ubereats import UberEatsScraper
from scrapers.vendors.pickme import PickMeScraper

logger = logging.getLogger(__name__)

class ScraperManager:
    """Manages all vendor food scrapers and aggregates offer data."""

    def __init__(self):
        self.scrapers: Dict[str, BaseScraper] = {
            "kfc": KFCScraper(),
            "pizzahut": PizzaHutScraper(),
            "dominos": DominosScraper(),
            "tacobell": TacoBellScraper(),
            "burgerking": BurgerKingScraper(),
            "popeyes": PopeyesScraper(),
            "fullerburgers": FullerBurgersScraper(),
            "creperunner": CrepeRunnerScraper(),
            "subway": SubwayScraper(),
            "dinemore": DinemoreScraper(),
            "chinesedragon": ChineseDragonScraper(),
            "breadtalk": BreadTalkScraper(),
            "ubereats": UberEatsScraper(),
            "pickme": PickMeScraper(),
        }

    def get_registered_vendors(self) -> List[Dict[str, str]]:
        """Return list of vendor metadata."""
        return [
            {
                "id": scraper.vendor_id,
                "name": scraper.vendor_name,
                "logo": scraper.vendor_logo,
                "website": scraper.website_url,
            }
            for scraper in self.scrapers.values()
        ]

    def fetch_all_offers(self) -> Dict[str, Any]:
        """Fetch offers across all vendors."""
        results = []
        all_offers = []
        live_count = 0

        for vendor_id, scraper in self.scrapers.items():
            try:
                data = scraper.get_offers()
                results.append(data)
                offers = data.get("offers", [])
                all_offers.extend(offers)
                live_count += 1
            except Exception as e:
                logger.error(f"Error fetching offers for {vendor_id}: {e}")

        return {
            "total_vendors": len(self.scrapers),
            "live_vendors": live_count,
            "fallback_vendors": 0,
            "total_offers": len(all_offers),
            "vendors": results,
            "all_offers": all_offers,
        }
