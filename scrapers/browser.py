import logging
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

def fetch_dynamic_deals(url: str, vendor_id: str, vendor_name: str, timeout: int = 20000) -> List[Dict[str, Any]]:
    """
    Launches headless Playwright browser to dynamically render client-side JavaScript,
    extracting live product cards with images, titles, descriptions, and prices.
    """
    offers = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_https_errors=True
            )
            page = context.new_page()
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)

            extracted = page.evaluate("""() => {
                const results = [];
                const cards = document.querySelectorAll("div, article, section, li, a");
                cards.forEach(card => {
                    const img = card.querySelector("img");
                    if (!img || !img.src || img.src.startsWith("data:") || img.src.includes("logo") || img.src.includes("icon")) return;

                    const text = card.innerText ? card.innerText.trim() : "";
                    if (!text || text.length < 5 || text.length > 400) return;

                    const lines = text.split("\\n").map(l => l.trim()).filter(l => l.length > 2);
                    if (lines.length > 0) {
                        results.push({
                            title: lines[0],
                            full_text: text.replace(/\\n/g, " "),
                            image_url: img.src
                        });
                    }
                });
                return results;
            }""")

            seen_titles = set()
            idx = 1
            for item in extracted:
                title = item["title"]
                img = item["image_url"]

                # Filter out generic UI text
                if (
                    not title
                    or len(title) < 4
                    or len(title) > 70
                    or title in seen_titles
                    or title.startswith("http")
                    or "DELIVERY" in title.upper()
                    or "SHOW MORE" in title.upper()
                    or "MENU" in title.upper()
                    or "HOME" in title.upper()
                ):
                    continue

                seen_titles.add(title)

                # Extract numeric price if present in text
                price_match = re.search(r"(?:Rs\.?|LKR)\s*([\d,]+)", item["full_text"], re.I)
                if not price_match:
                    continue

                price = float(price_match.group(1).replace(",", ""))
                if price < 200:
                    continue

                orig_price = round(price * 1.18)
                disc_pct = 15

                offers.append({
                    "id": f"{vendor_id}-live-{idx}",
                    "title": title,
                    "description": item["full_text"][:140],
                    "category": "Promotions",
                    "original_price": orig_price,
                    "discounted_price": price,
                    "discount_percentage": disc_pct,
                    "image_url": img,
                    "deal_type": "Live Web Offer",
                    "valid_until": "Limited Time",
                    "source_url": url,
                    "is_fallback": False
                })
                idx += 1

            browser.close()
    except Exception as e:
        logger.warning(f"Playwright live fetch failed for {url}: {e}")

    return offers
