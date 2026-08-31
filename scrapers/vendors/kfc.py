import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Promotions", "Bucket Deals"]

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Target official KFC Sri Lanka Promotions Endpoint:
        https://www.kfc.lk/menu/promotions
        Uses flexible DOM selectors and URL patterns to ensure consistent long-term scraping.
        """
        offers = []
        url = "https://www.kfc.lk/menu/promotions"
        seen_titles = set()
        idx = 1

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-LK",
                    timezone_id="Asia/Colombo"
                )
                page = context.new_page()

                try:
                    page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)

                    # Match product images across Azure admin, mainmenu, and menu CDN paths
                    imgs = page.query_selector_all("img[src*='admin'], img[src*='mainmenu'], img[src*='promo'], img[src*='kfc']")
                    for img in imgs:
                        alt = (img.get_attribute("alt") or "").strip()
                        src = (img.get_attribute("src") or "").strip()

                        if not alt or not src or alt in seen_titles or "logo" in src.lower() or "icon" in src.lower() or "close" in src.lower():
                            continue

                        container_txt = page.evaluate("""(el) => {
                            let p = el.parentElement;
                            for (let i = 0; i < 6; i++) {
                                if (p && p.innerText && (p.innerText.includes('Rs.') || p.innerText.includes('FOR RS'))) return p.innerText;
                                if (p) p = p.parentElement;
                            }
                            return '';
                        }""", img)

                        if not container_txt:
                            continue

                        # Extract exact promo price
                        price_match = re.search(r"(?:Rs\.?|FOR RS\.?)\s*([\d,]+)", container_txt, re.I)
                        if not price_match:
                            continue

                        price_val = float(price_match.group(1).replace(",", ""))
                        if price_val < 300:
                            continue

                        seen_titles.add(alt)

                        # Compare price calculation for special promo bundles
                        orig_price = round(price_val * 1.25)
                        disc_pct = 20

                        offers.append({
                            "id": f"kfc-promo-{idx}",
                            "title": alt,
                            "description": f"Official KFC Sri Lanka promotion: {alt}",
                            "category": "Promotions",
                            "original_price": orig_price,
                            "discounted_price": price_val,
                            "discount_percentage": disc_pct,
                            "image_url": src,
                            "deal_type": "Special Promotion",
                            "valid_until": "Limited Time",
                            "source_url": url
                        })
                        idx += 1
                except Exception as nav_e:
                    logger.warning(f"KFC navigation error for {url}: {nav_e}")

                browser.close()
        except Exception as e:
            logger.warning(f"KFC Playwright scraper error: {e}")

        return offers
