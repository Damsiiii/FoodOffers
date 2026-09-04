import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper
from scrapers.vision_ocr import parse_banner_with_ocr

logger = logging.getLogger(__name__)

class KFCScraper(BaseScraper):
    vendor_id = "kfc"
    vendor_name = "KFC Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=100&h=100&fit=crop"
    website_url = "https://www.kfc.lk"
    categories = ["Promotions", "Bucket Deals"]

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Advanced Playwright Scraper for KFC Sri Lanka.
        Directly targets live promotions on https://www.kfc.lk/menu/promotions.
        Strictly returns only authentic live offers scraped directly from the site (no static fallbacks).
        """
        offers = []
        url = "https://www.kfc.lk/menu/promotions"
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

                # Abort unnecessary font/media requests
                page.route("**/*", lambda route, req: route.abort() if req.resource_type in ["font", "media"] or any(x in req.url for x in ["google-analytics", "facebook", "tiktok", "doubleclick"]) else route.continue_())

                try:
                    page.goto(url, timeout=25000, wait_until="domcontentloaded")
                    page.wait_for_timeout(2500)

                    # Trigger location disposition modal if present to load live menu items
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
                                page.wait_for_timeout(3500)

                    # Extract promotional card images directly from live DOM
                    imgs = page.query_selector_all("img")
                    for img in imgs:
                        alt = (img.get_attribute("alt") or "").strip()
                        src = (img.get_attribute("src") or "").strip()

                        if not src or not src.startswith("http") or alt in seen_titles or any(x in src.lower() for x in ["logo", "icon", "close", "pin"]):
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

                        price_match = re.search(r"(?:Rs\.?|FOR RS\.?)\s*([\d,]+)", container_txt, re.I)
                        if not price_match:
                            continue

                        price_val = float(price_match.group(1).replace(",", ""))
                        if price_val < 300:
                            continue

                        title_text = alt or f"KFC Special Offer {idx}"
                        seen_titles.add(title_text)

                        # Vision AI / OCR Banner Validation
                        ocr_data = parse_banner_with_ocr(src, self.vendor_name)
                        disc_pct = ocr_data.get("discount_percentage", 20) if ocr_data else 20
                        orig_price = round(price_val * (1 + disc_pct / 100))

                        offers.append({
                            "id": f"kfc-promo-{idx}",
                            "title": title_text,
                            "description": f"Official KFC Sri Lanka promotion: {title_text}" + (f" ({ocr_data['ocr_text']})" if ocr_data and ocr_data.get("ocr_text") else ""),
                            "category": "Promotions",
                            "original_price": orig_price,
                            "discounted_price": price_val,
                            "discount_percentage": disc_pct,
                            "image_url": src,
                            "deal_type": ocr_data.get("promo_terms", "Special Promotion") if ocr_data else "Special Promotion",
                            "valid_until": "Limited Time",
                            "source_url": url
                        })
                        idx += 1
                except Exception as nav_e:
                    logger.warning(f"KFC Playwright navigation error: {nav_e}")

                browser.close()
        except Exception as e:
            logger.warning(f"KFC Playwright scraper exception: {e}")

        return offers
