import logging
import json
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

PROMO_KEYWORDS = [
    "promo", "deal", "combo", "special", "save", "offer",
    "discount", "off", "free", "bogo", "bucket", "saver", "value"
]

def intercept_api_deals(url: str, vendor_id: str, vendor_name: str, timeout: int = 25000) -> List[Dict[str, Any]]:
    """
    Network XHR / Internal API Interception Engine.
    Intercepts JSON responses sent by vendor web applications (React, Angular, Vue, Next.js)
    and extracts deal items directly from internal API payloads.
    """
    offers = []
    intercepted_json_payloads = []

    def handle_response(response):
        try:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                # Filter out analytics, tracking, or telemetry endpoints
                url_lower = response.url.lower()
                if any(x in url_lower for x in ["google", "analytics", "facebook", "sentry", "clarity", "hotjar", "gtm"]):
                    return
                try:
                    payload = response.json()
                    if payload:
                        intercepted_json_payloads.append((response.url, payload))
                except Exception:
                    pass
        except Exception:
            pass

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
            page.on("response", handle_response)

            try:
                page.goto(url, timeout=timeout, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)
            except Exception as nav_e:
                logger.warning(f"Navigation timeout for {url}: {nav_e}")

            browser.close()
    except Exception as e:
        logger.warning(f"Playwright XHR Interception error for {url}: {e}")

    # Parse intercepted JSON payloads for deal objects
    seen_titles = set()
    idx = 1

    def recursive_extract_deals(data):
        nonlocal idx
        if isinstance(data, dict):
            # Check if this dict looks like a product/deal item
            title = data.get("name") or data.get("title") or data.get("productName") or data.get("itemName")
            price = data.get("price") or data.get("discountedPrice") or data.get("offerPrice") or data.get("sellingPrice")
            compare_price = data.get("compareAtPrice") or data.get("originalPrice") or data.get("oldPrice") or data.get("listPrice")
            img = data.get("image") or data.get("imageUrl") or data.get("img") or data.get("thumbnail") or data.get("picture")

            if isinstance(img, list) and len(img) > 0:
                img = img[0]
            if isinstance(img, dict):
                img = img.get("src") or img.get("url")

            if title and isinstance(title, str) and price is not None:
                try:
                    price_val = float(price)
                    if price_val > 100:
                        comp_val = float(compare_price) if compare_price is not None else price_val
                        disc_pct = 0
                        if comp_val > price_val:
                            disc_pct = int(round((comp_val - price_val) / comp_val * 100))

                        title_clean = title.strip()
                        title_lower = title_clean.lower()
                        is_promo = any(kw in title_lower for kw in PROMO_KEYWORDS) or disc_pct > 0

                        if is_promo and title_clean not in seen_titles and len(title_clean) > 3:
                            seen_titles.add(title_clean)
                            img_str = str(img) if img else "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500&fit=crop"
                            offers.append({
                                "id": f"{vendor_id}-api-{idx}",
                                "title": title_clean,
                                "description": f"{vendor_name} promotional deal: {title_clean}",
                                "category": "API Deals",
                                "original_price": comp_val,
                                "discounted_price": price_val,
                                "discount_percentage": disc_pct,
                                "image_url": img_str,
                                "deal_type": "Internal API Deal",
                                "valid_until": "Limited Time",
                                "source_url": url,
                                "is_fallback": False
                            })
                            idx += 1
                except (ValueError, TypeError):
                    pass

            for v in data.values():
                recursive_extract_deals(v)
        elif isinstance(data, list):
            for item in data:
                recursive_extract_deals(item)

    for resp_url, payload in intercepted_json_payloads:
        recursive_extract_deals(payload)

    return offers
