import logging
import json
import os
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper
from scrapers.vision_ocr import parse_banner_with_ocr

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "src", "data", "kfc_cache.json")

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Promotions", "Bucket Deals", "Burgers & Combos", "Rice Bowls"]

    def _determine_category(self, title: str, description: str) -> str:
        text = f"{title} {description}".lower()
        if any(k in text for k in ["burger", "combo", "twister", "decker", "wrap", "submarine"]):
            return "Burgers & Combos"
        elif any(k in text for k in ["bucket", "pc", "hot & crispy", "chicken"]):
            return "Bucket Deals"
        elif any(k in text for k in ["rice", "biryani"]):
            return "Rice Bowls"
        return "Promotions"

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Multi-Modal Playwright Scraper for KFC Sri Lanka.
        Targets live promotions & menu items on https://www.kfc.lk across multiple endpoints.
        Includes off-hours session replay cache fallback if the store is closed.
        """
        offers = []
        target_urls = [
            "https://www.kfc.lk/menu/promotions",
            "https://www.kfc.lk/menu/promo",
            "https://www.kfc.lk/menu/mains",
            "https://www.kfc.lk/menu/meals-and-beverages"
        ]
        seen_titles = set()
        idx = 1

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-LK",
                    timezone_id="Asia/Colombo"
                )
                page = context.new_page()

                # Abort unnecessary resources
                page.route("**/*", lambda route, req: route.abort() if req.resource_type in ["font", "media"] or any(x in req.url for x in ["google-analytics", "facebook", "tiktok", "doubleclick"]) else route.continue_())

                try:
                    # Initial location modal pass
                    page.goto("https://www.kfc.lk/menu", timeout=25000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2000)

                    start_btn = page.query_selector('text="Let\'s Start Your Order Now"')
                    if start_btn:
                        start_btn.click()
                        page.wait_for_timeout(1000)

                        pickup_btn = page.query_selector('text="Change order type to pickup"')
                        if pickup_btn:
                            pickup_btn.click()
                            page.wait_for_timeout(1000)

                            page.evaluate("""() => {
                                let s = document.getElementById('outletCombo');
                                if (s) {
                                    s.value = '046'; // Colpetty Outlet
                                    s.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                            }""")
                            page.wait_for_timeout(1000)

                            cont_btn = page.query_selector('text="Continue to menu"')
                            if cont_btn:
                                cont_btn.click()
                                page.wait_for_timeout(2500)

                    for url in target_urls:
                        try:
                            page.goto(url, timeout=20000, wait_until="domcontentloaded")
                            page.wait_for_timeout(2000)

                            cards_data = page.evaluate("""() => {
                                let imgs = Array.from(document.querySelectorAll('img'));
                                let res = [];
                                for (let img of imgs) {
                                    let src = img.src || '';
                                    let alt = img.alt || '';
                                    if (!src || (!src.includes('admin-kfc-web') && !src.includes('mainmenu'))) continue;

                                    let p = img.parentElement;
                                    let fullText = '';
                                    for (let i = 0; i < 6; i++) {
                                        if (p && p.innerText && (p.innerText.includes('Rs') || p.innerText.includes('RS'))) {
                                            fullText = p.innerText;
                                            break;
                                        }
                                        if (p) p = p.parentElement;
                                    }
                                    res.push({ src, alt, fullText });
                                }
                                return res;
                            }""")

                            for c in cards_data:
                                src = c["src"]
                                alt = c["alt"].strip()
                                txt = c["fullText"]
                                if not txt or not src:
                                    continue

                                # Price extraction
                                price_match = re.search(r"(?:Rs\.?|FOR RS\.?)\s*([\d,]+)", txt, re.I)
                                price_val = float(price_match.group(1).replace(",", "")) if price_match else None

                                # Title extraction
                                title_text = alt
                                if not title_text or title_text.lower() in ["logo", "kfc", "banner"]:
                                    lines = [l.strip() for l in txt.split("\n") if l.strip() and not re.search(r"(?:Rs\.?|FOR RS\.?)\s*[\d,]+", l, re.I) and "Add to Bucket" not in l and "Select" not in l]
                                    if lines:
                                        title_text = lines[0]

                                if not title_text or title_text in seen_titles:
                                    continue

                                seen_titles.add(title_text)

                                # Vision AI / OCR Banner Validation
                                ocr_data = parse_banner_with_ocr(src, self.vendor_name)
                                category = self._determine_category(title_text, txt)

                                offer_item = {
                                    "id": f"kfc-promo-{idx}",
                                    "title": title_text,
                                    "description": f"Official KFC Sri Lanka promotion: {title_text}" + (f" ({ocr_data['ocr_text']})" if ocr_data and ocr_data.get("ocr_text") else ""),
                                    "category": category,
                                    "image_url": src,
                                    "deal_type": ocr_data.get("promo_terms", "Special Promotion") if ocr_data else "Special Promotion",
                                    "valid_until": "Limited Time",
                                    "source_url": url,
                                    "location": "colombo"
                                }

                                if price_val and price_val >= 300:
                                    offer_item["discounted_price"] = price_val
                                    if ocr_data and ocr_data.get("discount_percentage", 0) > 0:
                                        disc_pct = int(ocr_data["discount_percentage"])
                                        offer_item["discount_percentage"] = disc_pct
                                        offer_item["original_price"] = round(price_val / (1 - disc_pct / 100))

                                offers.append(offer_item)
                                idx += 1
                        except Exception as page_e:
                            logger.warning(f"Error scraping KFC page {url}: {page_e}")

                except Exception as nav_e:
                    logger.warning(f"KFC Playwright navigation error: {nav_e}")

                browser.close()
        except Exception as e:
            logger.warning(f"KFC Playwright scraper exception: {e}")

        # Update cache on success or fallback to cache on off-hours empty response
        if offers:
            try:
                os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(offers, f, indent=2)
                logger.info(f"Successfully cached {len(offers)} KFC offers to {CACHE_FILE}")
            except Exception as cache_e:
                logger.warning(f"Could not write KFC cache: {cache_e}")
        elif os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "r", encoding="utf-8") as f:
                    offers = json.load(f)
                logger.info(f"Loaded {len(offers)} cached KFC offers during off-hours / empty live response")
            except Exception as read_e:
                logger.warning(f"Could not read KFC cache: {read_e}")

        return offers
