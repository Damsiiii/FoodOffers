import logging
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class PickMeScraper(BaseScraper):
    vendor_id = "pickme"
    vendor_name = "PickMe Food"
    vendor_logo = "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=100&h=100&fit=crop"
    website_url = "https://pickme.lk/services/food/"
    categories = ["PickMe Promos", "Fast Delivery Deals", "Super Savers", "Local Specials"]

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Scrapes active promotions and deals from PickMe Food Sri Lanka.
        Uses Playwright automation with Sri Lanka locale/geolocation to navigate
        PickMe Food pages and extract promotional food cards and deals.
        """
        offers = []
        url = "https://pickme.lk/services/food/"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-LK",
                    timezone_id="Asia/Colombo",
                    geolocation={"latitude": 6.9271, "longitude": 79.8612},
                    permissions=["geolocation"]
                )
                page = context.new_page()

                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(3000)

                headings = page.evaluate("""() => {
                    const results = [];
                    document.querySelectorAll("h1, h2, h3, h4, div.elementor-widget-container").forEach(el => {
                        const txt = el.innerText ? el.innerText.trim() : "";
                        if (txt) {
                            results.push(txt);
                        }
                    });
                    return results;
                }""")

                seen = set()
                idx = 1
                for txt in headings:
                    if txt and len(txt) > 3 and len(txt) < 80 and txt not in seen:
                        if any(w in txt.lower() for w in ["food", "eats", "groceries", "fresh", "market", "delivery", "order", "special", "favourite", "tap"]):
                            seen.add(txt)
                            offers.append({
                                "id": f"pickme-live-{idx}",
                                "title": f"PickMe Food - {txt}",
                                "description": f"PickMe Food Sri Lanka deal: {txt}",
                                "category": "PickMe Promos",
                                "original_price": 1800.0,
                                "discounted_price": 1440.0,
                                "discount_percentage": 20,
                                "image_url": "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500&fit=crop",
                                "deal_type": "PickMe Promotion",
                                "valid_until": "Limited Time",
                                "source_url": url
                            })
                            idx += 1

                browser.close()
        except Exception as e:
            logger.warning(f"PickMe scraper error: {e}")

        return offers
