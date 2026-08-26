import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
FALLBACK_FILE = DATA_DIR / "fallback_dataset.json"

class BaseScraper:
    """Base class for all vendor food scrapers."""

    vendor_id: str = "base"
    vendor_name: str = "Base Vendor"
    vendor_logo: str = ""
    website_url: str = ""
    categories: List[str] = []

    def scrape_live(self) -> List[Dict[str, Any]]:
        """Scrape live offers from vendor website. Override in subclasses."""
        raise NotImplementedError("scrape_live must be implemented by subclass")

    def load_fallback_dataset(self) -> Dict[str, Any]:
        """Load full fallback dataset JSON file."""
        if not FALLBACK_FILE.exists():
            logger.warning(f"Fallback dataset file not found at {FALLBACK_FILE}")
            return {}
        try:
            with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read fallback dataset: {e}")
            return {}

    def get_fallback_offers(self) -> List[Dict[str, Any]]:
        """Retrieve fallback offers for this specific vendor."""
        data = self.load_fallback_dataset()
        vendor_data = data.get(self.vendor_id, {})
        offers = vendor_data.get("offers", [])

        for offer in offers:
            offer["is_fallback"] = True
            if "vendor_id" not in offer:
                offer["vendor_id"] = self.vendor_id
            if "vendor_name" not in offer:
                offer["vendor_name"] = self.vendor_name
        return offers

    def get_offers(self, force_fallback: bool = False) -> Dict[str, Any]:
        """
        Get offers for this vendor.
        Tries live scraping first unless force_fallback is True.
        Falls back to local offline dataset if live scraping fails or returns no results.
        """
        if not force_fallback:
            try:
                live_offers = self.scrape_live()
                if live_offers and len(live_offers) > 0:
                    for offer in live_offers:
                        offer["is_fallback"] = False
                        if "vendor_id" not in offer:
                            offer["vendor_id"] = self.vendor_id
                        if "vendor_name" not in offer:
                            offer["vendor_name"] = self.vendor_name
                    return {
                        "vendor_id": self.vendor_id,
                        "vendor_name": self.vendor_name,
                        "vendor_logo": self.vendor_logo,
                        "website_url": self.website_url,
                        "status": "live",
                        "count": len(live_offers),
                        "offers": live_offers
                    }
            except Exception as e:
                logger.warning(f"Live scraping failed for {self.vendor_name} ({self.vendor_id}): {e}. Using fallback.")

        fallback_offers = self.get_fallback_offers()
        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "vendor_logo": self.vendor_logo,
            "website_url": self.website_url,
            "status": "fallback",
            "count": len(fallback_offers),
            "offers": fallback_offers
        }
