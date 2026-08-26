import logging
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from scrapers.vendors.kfc import KFCScraper
from scrapers.vendors.other_vendors import (
    PizzaHutScraper,
    DominosScraper,
    TacoBellScraper,
    BurgerKingScraper,
    PopeyesScraper,
    FullerBurgersScraper,
    CrepeRunnerScraper,
    SubwayScraper,
    DinemoreScraper,
    PereraAndSonsScraper,
    ChineseDragonScraper,
    BaskinRobbinsScraper,
    BreadTalkScraper,
)

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
            "pereraandsons": PereraAndSonsScraper(),
            "chinesedragon": ChineseDragonScraper(),
            "baskinrobbins": BaskinRobbinsScraper(),
            "breadtalk": BreadTalkScraper(),
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

    def fetch_all_offers(self, force_fallback: bool = False) -> Dict[str, Any]:
        """Fetch offers across all vendors."""
        results = []
        all_offers = []
        fallback_count = 0
        live_count = 0

        for vendor_id, scraper in self.scrapers.items():
            try:
                data = scraper.get_offers(force_fallback=force_fallback)
                results.append(data)
                offers = data.get("offers", [])
                all_offers.extend(offers)
                if data.get("status") == "fallback":
                    fallback_count += 1
                else:
                    live_count += 1
            except Exception as e:
                logger.error(f"Error fetching offers for {vendor_id}: {e}")
                fallback_data = scraper.get_offers(force_fallback=True)
                results.append(fallback_data)
                all_offers.extend(fallback_data.get("offers", []))
                fallback_count += 1

        return {
            "total_vendors": len(self.scrapers),
            "live_vendors": live_count,
            "fallback_vendors": fallback_count,
            "total_offers": len(all_offers),
            "vendors": results,
            "all_offers": all_offers,
        }
