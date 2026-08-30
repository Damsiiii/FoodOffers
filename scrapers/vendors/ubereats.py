import logging
import json
import base64
import re
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# Supported Sri Lankan target delivery locations
SRI_LANKA_LOCATIONS = {
    "colombo": {"address": "Colombo, Sri Lanka", "latitude": 6.9271, "longitude": 79.8612},
    "kandy": {"address": "Kandy, Sri Lanka", "latitude": 7.2906, "longitude": 80.6337},
    "galle": {"address": "Galle, Sri Lanka", "latitude": 6.0535, "longitude": 80.2210},
    "negombo": {"address": "Negombo, Sri Lanka", "latitude": 7.2008, "longitude": 79.8737},
}

class UberEatsScraper(BaseScraper):
    vendor_id = "ubereats"
    vendor_name = "Uber Eats Sri Lanka"
    vendor_logo = "https://images.unsplash.com/photo-1526367790999-0150786686a2?w=100&h=100&fit=crop"
    website_url = "https://www.ubereats.com/lk"
    categories = ["Delivery Deals", "BOGO Offers", "Store Promos", "Combos"]

    def scrape_live(self) -> List[Dict[str, Any]]:
        """
        Scrapes active food deals and restaurant promotions across Sri Lanka
        from the official Uber Eats feed.
        """
        offers = []
        loc = SRI_LANKA_LOCATIONS["colombo"]
        pl_str = base64.b64encode(json.dumps(loc).encode("utf-8")).decode("utf-8")
        url = f"https://www.ubereats.com/lk/feed?pl={pl_str}"

        payloads = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="en-LK",
                    timezone_id="Asia/Colombo",
                    geolocation={"latitude": loc["latitude"], "longitude": loc["longitude"]},
                    permissions=["geolocation"]
                )
                page = context.new_page()

                def handle_resp(resp):
                    if "getFeedV1" in resp.url:
                        try:
                            payloads.append(resp.json())
                        except Exception:
                            pass

                page.on("response", handle_resp)
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.wait_for_timeout(4000)

                seen = set()
                idx = 1

                if payloads:
                    data = payloads[0].get("data", {})
                    feed_items = data.get("feedItems", [])

                    def process_store(st_dict):
                        nonlocal idx
                        if not isinstance(st_dict, dict):
                            return
                        title = ""
                        title_obj = st_dict.get("title")
                        if isinstance(title_obj, dict):
                            title = title_obj.get("text", "")
                        elif isinstance(title_obj, str):
                            title = title_obj
                        if not title:
                            title = st_dict.get("name", "")

                        if not title or title in seen or title.startswith("LKR") or title.startswith("Rs"):
                            return

                        hero_img = st_dict.get("heroImageUrl", "") or st_dict.get("imageUrl", "")
                        if not hero_img and "image" in st_dict and isinstance(st_dict["image"], dict):
                            items = st_dict["image"].get("items", [])
                            if items and isinstance(items[0], dict):
                                hero_img = items[0].get("url", "")

                        raw_str = json.dumps(st_dict)
                        badge_txt = ""
                        endorsement = st_dict.get("endorsement", {})
                        if isinstance(endorsement, dict) and "text" in endorsement:
                            badge_txt = endorsement.get("text", "")

                        if any(w in raw_str.lower() for w in ["% off", "buy 1", "bogo", "save", "special offer", "top offer", "promo", "free item", "discount"]):
                            seen.add(title)

                            disc_pct = 20
                            pct_match = re.search(r"(\d+)%\s*off", raw_str, re.I)
                            if pct_match:
                                disc_pct = int(pct_match.group(1))

                            offers.append({
                                "id": f"ubereats-feed-{idx}",
                                "title": f"{title} - {badge_txt}" if badge_txt else f"{title} Promotional Offer",
                                "description": f"Exclusive Uber Eats deal at {title}",
                                "category": "Store Promos",
                                "original_price": 2000.0,
                                "discounted_price": round(2000.0 * (1 - disc_pct / 100)),
                                "discount_percentage": disc_pct,
                                "image_url": hero_img or "https://images.unsplash.com/photo-1526367790999-0150786686a2?w=500&fit=crop",
                                "deal_type": "Uber Eats Offer",
                                "valid_until": "Limited Time",
                                "source_url": url
                            })
                            idx += 1

                    for item in feed_items:
                        payload = item.get("payload", {})
                        stores = payload.get("stores", [])
                        if isinstance(stores, list):
                            for st in stores:
                                process_store(st)
                        if "store" in payload:
                            process_store(payload["store"])

                # DOM fallback card extraction
                if not offers:
                    cards = page.query_selector_all("a[href*='/store/']")
                    for c in cards:
                        txt = c.inner_text()
                        if txt and any(w in txt.lower() for w in ["off", "buy", "bogo", "deal", "promo", "free", "save", "special", "top offer"]):
                            lines = [l.strip() for l in txt.split("\n") if len(l.strip()) > 2 and not l.strip().startswith("LKR") and not l.strip().startswith("Rs")]
                            title = lines[0] if lines else ""
                            if title and title not in seen:
                                seen.add(title)
                                img_el = c.query_selector("img")
                                img = img_el.get_attribute("src") if img_el else ""
                                offers.append({
                                    "id": f"ubereats-dom-{idx}",
                                    "title": title,
                                    "description": f"Uber Eats Sri Lanka promotion: {txt[:100]}",
                                    "category": "Delivery Deals",
                                    "original_price": 2000.0,
                                    "discounted_price": 1500.0,
                                    "discount_percentage": 25,
                                    "image_url": img or "https://images.unsplash.com/photo-1526367790999-0150786686a2?w=500&fit=crop",
                                    "deal_type": "Uber Eats Offer",
                                    "valid_until": "Limited Time",
                                    "source_url": url
                                })
                                idx += 1

                browser.close()
        except Exception as e:
            logger.warning(f"UberEats scraper error: {e}")

        return offers
