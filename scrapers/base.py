import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

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

    def get_offers(self, force_fallback: bool = False) -> Dict[str, Any]:
        """
        Get live offers for this vendor.
        Executes live dynamic web scraping.
        """
        try:
            live_offers = self.scrape_live()
            if live_offers:
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
            logger.error(f"Live scraping failed for {self.vendor_name} ({self.vendor_id}): {e}")

        return {
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "vendor_logo": self.vendor_logo,
            "website_url": self.website_url,
            "status": "live",
            "count": 0,
            "offers": []
        }
