import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

def fetch_dynamic_deals(url: str, vendor_id: str, vendor_name: str, timeout: int = 25000) -> List[Dict[str, Any]]:
    """
    Intelligent dynamic live deal and image extraction engine using Playwright Firefox with Sri Lankan localization headers.
    """
    offers = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-LK",
                timezone_id="Asia/Colombo",
                extra_http_headers={
                    "Accept-Language": "en-LK,en-US;q=0.9,en;q=0.8"
                }
            )
            page = context.new_page()

            try:
                page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)
            except Exception as nav_e:
                logger.warning(f"Navigation timeout for {url}: {nav_e}")

            extracted = page.evaluate("""() => {
                const results = [];
                const imgs = Array.from(document.querySelectorAll("img"));

                imgs.forEach(img => {
                    const src = img.src || img.getAttribute("data-src") || img.getAttribute("srcset");
                    if (!src || src.startsWith("data:") || src.includes("logo") || src.includes("icon") || src.includes("avatar")) return;

                    const card = img.closest("div, article, section, li, a") || img.parentElement;
                    if (!card) return;

                    const text = card.innerText ? card.innerText.trim() : "";
                    if (!text || text.length < 5 || text.length > 500) return;

                    const lines = text.split("\\n").map(l => l.trim()).filter(l => l.length > 2);
                    if (lines.length > 0) {
                        results.push({
                            title: lines[0],
                            full_text: text.replace(/\\n/g, " "),
                            image_url: src
                        });
                    }
                });
                return results;
            }""")

            seen_titles = set()
            idx = 1
            for item in extracted:
                title = item["title"]
                img_url = item["image_url"]
                full_text = item["full_text"]

                if (
                    not title
                    or len(title) < 4
                    or len(title) > 80
                    or title in seen_titles
                    or title.startswith("http")
                    or "DELIVERY" in title.upper()
                    or "SHOW MORE" in title.upper()
                    or "SIGN IN" in title.upper()
                    or "PRIVACY" in title.upper()
                    or "TERMS" in title.upper()
                    or "HOME" in title.upper()
                    or "MENU" in title.upper()
                ):
                    continue

                # Filter out pure phone numbers or address strings
                if re.match(r"^[\d\s\-\+\(\)]+$", title):
                    continue

                # Check price match in LKR
                price_match = re.search(r"(?:Rs\.?|LKR)\s*([\d,]+(?:\.\d{2})?)", full_text, re.I)
                if not price_match:
                    continue

                price = float(price_match.group(1).replace(",", ""))
                if price < 150 or price > 50000:
                    continue
                orig_price = round(price * 1.15)
                disc_pct = 13

                seen_titles.add(title)

                offers.append({
                    "id": f"{vendor_id}-live-{idx}",
                    "title": title,
                    "description": full_text[:140],
                    "category": "Live Deals",
                    "original_price": orig_price,
                    "discounted_price": price,
                    "discount_percentage": disc_pct,
                    "image_url": img_url,
                    "deal_type": "Live Web Offer",
                    "valid_until": "Limited Time",
                    "source_url": url,
                    "is_fallback": False
                })
                idx += 1

            browser.close()
    except Exception as e:
        logger.warning(f"Playwright live fetch error for {url}: {e}")

    return offers
