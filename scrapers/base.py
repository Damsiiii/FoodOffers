import json
import logging
from typing import Dict, List, Any
from scrapers.vision_ocr import parse_banner_with_ocr

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for all Sri Lanka food deal scrapers."""

    vendor_id: str = "base"
    vendor_name: str = "Base Vendor"
    vendor_logo: str = ""
    website_url: str = ""
    categories: List[str] = []

    def scrape_live(self) -> List[Dict[str, Any]]:
        """Scrape live offers from vendor website/API. Must be overridden by subclasses."""
        raise NotImplementedError("scrape_live must be implemented by subclass")

    def get_offers(self) -> Dict[str, Any]:
        """
        Get live offers for this vendor.
        Executes live dynamic web / API scraping and processes offer metadata cleanly.
        """
        try:
            live_offers = self.scrape_live()
            if live_offers:
                sanitized_offers = []
                for offer in live_offers:
                    offer["is_fallback"] = False
                    if "vendor_id" not in offer:
                        offer["vendor_id"] = self.vendor_id
                    if "vendor_name" not in offer:
                        offer["vendor_name"] = self.vendor_name

                    # Run Vision OCR / Banner AI validation across every scraper's deal image
                    img_url = offer.get("image_url", "")
                    if img_url and img_url.startswith("http"):
                        ocr_info = parse_banner_with_ocr(img_url, self.vendor_name)
                        if ocr_info:
                            offer["ocr_verified"] = True
                            if ocr_info.get("ocr_text") and ocr_info["ocr_text"] not in offer.get("description", ""):
                                offer["description"] = f"{offer.get('description', '')} ({ocr_info['ocr_text']})".strip()
                            if ocr_info.get("promo_terms") and offer.get("deal_type") in ["Special Promotion", "Live Promotion", "Menu Deal", "Live Offer"]:
                                offer["deal_type"] = ocr_info["promo_terms"]

                    disc_price = float(offer.get("discounted_price", 0)) if offer.get("discounted_price") is not None else 0.0
                    orig_price = float(offer.get("original_price", 0)) if offer.get("original_price") is not None else 0.0

                    # Discount normalization and filtering invalid compare prices
                    if orig_price > disc_price and disc_price > 0:
                        calculated_disc = int(round((orig_price - disc_price) / orig_price * 100))
                        offer["original_price"] = orig_price
                        offer["discounted_price"] = disc_price
                        offer["discount_percentage"] = max(0, calculated_disc)
                        sanitized_offers.append(offer)
                    elif offer.get("discount_percentage", 0) > 0 and disc_price > 0:
                        disc_pct = int(offer["discount_percentage"])
                        if orig_price <= disc_price:
                            orig_price = round(disc_price / (1 - disc_pct / 100))
                        offer["original_price"] = orig_price
                        offer["discounted_price"] = disc_price
                        offer["discount_percentage"] = disc_pct
                        sanitized_offers.append(offer)
                    elif offer.get("discounted_price") is None and offer.get("original_price") is None:
                        # Promotional banner offers without numeric price quotes
                        sanitized_offers.append(offer)

                return {
                    "vendor_id": self.vendor_id,
                    "vendor_name": self.vendor_name,
                    "vendor_logo": self.vendor_logo,
                    "website_url": self.website_url,
                    "status": "live",
                    "count": len(sanitized_offers),
                    "offers": sanitized_offers
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
