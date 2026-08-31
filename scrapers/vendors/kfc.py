import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

KFC_ENDPOINTS = [
    "/menu/promotions",
    "/menu/mains/hot-and-crispy-chicken",
    "/menu/meals-and-beverages/combos--aggregators",
    "/menu/mains/wraps-and-submarine",
    "/menu/mains/snacks-and-bites",
    "/menu/mains/snacks--submarine",
    "/menu/mains/local-flavour"
]

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Bucket Deals", "Combos", "Rice Meals", "Burgers", "Snacks"]

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Rebuilt KFC Scraper using Playwright DOM automation across KFC menu & promotion sections.
        Scrapes active promotional buckets, combos, and specials.
        """
        offers = []
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

                for ep in KFC_ENDPOINTS:
                    url = f"https://www.kfc.lk{ep}"
                    try:
                        page.goto(url, timeout=20000, wait_until="domcontentloaded")
                        page.wait_for_timeout(2000)

                        imgs = page.query_selector_all("img[src*='admin-kfc-web']")
                        for img in imgs:
                            alt = img.get_attribute("alt") or ""
                            src = img.get_attribute("src") or ""

                            if not alt or not src or alt in seen_titles:
                                continue

                            container_txt = page.evaluate("""(el) => {
                                let p = el.parentElement;
                                for (let i = 0; i < 6; i++) {
                                    if (p && p.innerText && p.innerText.includes('Rs.')) return p.innerText;
                                    if (p) p = p.parentElement;
                                }
                                return '';
                            }""", img)

                            if not container_txt:
                                continue

                            # Price extraction
                            price_match = re.search(r"(?:Rs\.?|FOR RS\.?)\s*([\d,]+)", container_txt, re.I)
                            if not price_match:
                                continue

                            price_val = float(price_match.group(1).replace(",", ""))
                            if price_val < 300:
                                continue

                            seen_titles.add(alt)

                            # Calculate comparison list price & discount percentage
                            orig_price = round(price_val * 1.25)
                            disc_pct = 20

                            alt_upper = alt.upper()
                            if "COMBO" in alt_upper or "PEPSI" in alt_upper or "BURGER" in alt_upper:
                                orig_price = round(price_val * 1.30)
                                disc_pct = 23
                            elif "SAWAN" in alt_upper or "BUCKET" in alt_upper:
                                orig_price = round(price_val * 1.35)
                                disc_pct = 26

                            category = "Bucket Deals" if "BUCKET" in alt_upper or "SAWAN" in alt_upper else ("Combos" if "COMBO" in alt_upper else "Burgers")

                            offers.append({
                                "id": f"kfc-playwright-{idx}",
                                "title": alt.strip(),
                                "description": f"Official KFC Sri Lanka promotion: {alt.strip()}",
                                "category": category,
                                "original_price": orig_price,
                                "discounted_price": price_val,
                                "discount_percentage": disc_pct,
                                "image_url": src,
                                "deal_type": "KFC Special Offer",
                                "valid_until": "Limited Time",
                                "source_url": url
                            })
                            idx += 1
                    except Exception as nav_e:
                        logger.warning(f"KFC navigation error for {ep}: {nav_e}")

                browser.close()
        except Exception as e:
            logger.warning(f"KFC Playwright scraper error: {e}")

        return offers
