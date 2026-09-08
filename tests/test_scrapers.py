"""
Tests for the KFC and Pizza Hut scrapers.

Tests cover:
- Correct deal extraction from HTML / API data
- Normal menu items are not treated as deals
- Duplicate deal removal
- Deterministic output (same source -> same output)
- Malformed / empty response handling
- Failed scrape does not overwrite valid cached data
- Validation logic (0 deals, deal drop, duplicate detection)
"""
import json
import os
import sys
import re
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from html import unescape

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scrapers.vendors.kfc import KFCScraper
from scrapers.vendors.pizzahut import PizzaHutScraper
from scrapers.vendors.popeyes import PopeyesScraper
from scrapers.base import BaseScraper


# ---------------------------------------------------------------------------
# Fixtures & Helpers
# ---------------------------------------------------------------------------

SAMPLE_KFC_PROMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head><link rel="canonical" href="https://kfc.lk/menu/promotions/promtn--others" /></head>
<body>
<div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
    <div class="itemBorder"><div class="box">
        <div class="row">
            <div class="col-md-12 col-sm-5 col-xs-5 itemImageContainer">
                <div class="itemImage">
                    <center>
                        <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/8pchcbucket.jpg" alt="8PC H&amp;C BUCKET FOR RS.2990" class="data-gtag-item-image" />
                    </center>
                </div>
            </div>
            <div class="col-md-12 col-sm-7 col-xs-7 itemDetailContainer">
                <div class="row"><div class="col-md-12">
                    <h3 class="menu-item-name hidden-lg hidden-md" title="8PC H&amp;C BUCKET FOR RS.2990" data-toggle="tooltip">8PC H&amp;C BUCKET FOR RS....</h3>
                    <h3 class="menu-item-name hidden-sm hidden-xs" title="8PC H&amp;C BUCKET FOR RS.2990" data-toggle="tooltip">8PC H&amp;C BUCKET FOR RS.2990 </h3>
                    <p class="hidden-xs hidden-sm menu-item-desc text-left" title="8PC H&amp;C BUCKET FOR RS.2990">8PC H&amp;C BUCKET FOR RS.2990</p>
                </div></div>
                <div class="menu-price-container-parent"><div class="row"><div>
                    <div class="submenus-1"><div class="col-md-12 col-sm-12 col-xs-12 menu-price-container">
                        <span class="price">+  Rs. 2,990</span>
                    <div class="btn btn-danger btn-add-quick btn-add-to-cart-quick" data-price="2990.0000" data-main-menu="1540" data-main-menu-name="8PC H&amp;C BUCKET" data-sub-menu="" data-sub-menu-name="">
                    </div></div></div>
                </div></div></div>
            </div>
        </div>
    </div></div>
</div>

<div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
    <div class="itemBorder"><div class="box">
        <div class="row">
            <div class="col-md-12 col-sm-5 col-xs-5 itemImageContainer">
                <div class="itemImage">
                    <center>
                        <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/buyzinger.jpg" alt="BUY 2 ZINGER BURGER &amp; GET 1 FREE" />
                    </center>
                </div>
            </div>
            <div class="col-md-12 col-sm-7 col-xs-7 itemDetailContainer">
                <div class="row"><div class="col-md-12">
                    <h3 class="menu-item-name hidden-sm hidden-xs" title="BUY 2 ZINGER BURGER &amp; GET 1 FREE" data-toggle="tooltip">BUY 2 ZINGER BURGER &amp; GET 1 FREE </h3>
                    <p class="hidden-xs hidden-sm menu-item-desc text-left" title="BUY 2 ZINGER BURGER &amp; GET 1 FREE">BUY 2 ZINGER BURGER &amp; GET 1 FREE</p>
                </div></div>
                <div class="menu-price-container-parent"><div class="row"><div>
                    <div class="submenus-1"><div class="col-md-12 menu-price-container">
                        <span class="price">Rs. 3,180</span>
                    <div class="btn" data-price="3180.0000" data-main-menu-name="BUY 2 ZINGER" data-sub-menu-name="">
                    </div></div></div>
                </div></div></div>
            </div>
        </div>
    </div></div>
</div>
</body></html>
"""

SAMPLE_KFC_MEALS_HTML = """
<!DOCTYPE html>
<html><head><link rel="canonical" href="https://kfc.lk/menu/meals-and-beverages/combos" /></head>
<body>
<div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
    <div class="itemBorder"><div class="box"><div class="row">
        <div class="col-md-12 itemImageContainer"><div class="itemImage"><center>
            <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/zingercombo.jpg" alt="Zinger Burger Combo + 400ML PEPSI" />
        </center></div></div>
        <div class="col-md-12 itemDetailContainer">
            <div class="row"><div class="col-md-12">
                <h3 class="menu-item-name hidden-sm hidden-xs" title="Zinger Burger Combo + 400ML PEPSI">Zinger Burger Combo + 400ML PEPSI </h3>
                <p class="hidden-xs hidden-sm menu-item-desc text-left" title="Zinger Burger Combo + 400ML PEPSI">Zinger Burger Combo</p>
            </div></div>
            <div class="menu-price-container-parent"><div class="row"><div>
                <div class="submenus-1"><div class="col-md-12 menu-price-container">
                    <span class="price">Rs. 2,530</span>
                <div class="btn" data-price="2530.0000" data-main-menu-name="Zinger Burger Combo"></div>
                </div></div>
            </div></div></div>
        </div>
    </div></div></div>
</div>
</body></html>
"""

# Regular chicken items - NOT promotions
SAMPLE_KFC_REGULAR_MENU_HTML = """
<!DOCTYPE html>
<html><head><link rel="canonical" href="https://kfc.lk/menu/mains/hot-and-crispy-chicken" /></head>
<body>
<div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
    <div class="itemBorder"><div class="box"><div class="row">
        <div class="col-md-12 itemImageContainer"><div class="itemImage"><center>
            <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/1pcchoice.jpg" alt="1 Pc Choice (HC)" />
        </center></div></div>
        <div class="col-md-12 itemDetailContainer">
            <div class="row"><div class="col-md-12">
                <h3 class="menu-item-name hidden-sm hidden-xs" title="1 Pc Choice (HC)">1 Pc Choice (HC) </h3>
            </div></div>
            <div class="menu-price-container-parent"><div class="row"><div>
                <div class="submenus-1"><div class="col-md-12 menu-price-container">
                    <span class="price">Rs. 990</span>
                </div></div>
            </div></div></div>
        </div>
    </div></div></div>
</div>
<div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
    <div class="itemBorder"><div class="box"><div class="row">
        <div class="col-md-12 itemImageContainer"><div class="itemImage"><center>
            <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/quarter2pc.jpg" alt="Quarter/2Pc (HC)" />
        </center></div></div>
        <div class="col-md-12 itemDetailContainer">
            <div class="row"><div class="col-md-12">
                <h3 class="menu-item-name hidden-sm hidden-xs" title="Quarter/2Pc (HC)">Quarter/2Pc (HC) </h3>
            </div></div>
            <div class="menu-price-container-parent"><div class="row"><div>
                <div class="submenus-1"><div class="col-md-12 menu-price-container">
                    <span class="price">Rs. 1,540</span>
                </div></div>
            </div></div></div>
        </div>
    </div></div></div>
</div>
</body></html>
"""

SAMPLE_PIZZAHUT_PROMO_RESPONSE = [
    {
        "Code": "B091",
        "WebCategoryCode": "9MD",
        "WebName": "Offer 1 - Weekend Vibes",
        "IsCustomizable": False,
        "Description": "Weekend special",
        "DescriptionShort": "...",
        "Url": "weekend-vibes-offer",
        "Price": "0.00",
        "CategoryCode": "9MD",
        "ClassificationId": 31,
        "ClassificationName": "Weekend Vibes",
        "ImageURL": "/images/mainmenu/test1.jpg",
        "FullImageUrl": "https://adminsc.pizzahut.lk//images/mainmenu/test1.jpg",
    },
    {
        "Code": "B124",
        "WebCategoryCode": "9MD",
        "WebName": "Cyber Saving Offer 1",
        "IsCustomizable": False,
        "Description": "",
        "DescriptionShort": "...",
        "Url": "cyber-savings-1",
        "Price": "4900.00",
        "CategoryCode": "9MD",
        "ClassificationId": 30,
        "ClassificationName": "Cyber Savings",
        "ImageURL": "/images/mainmenu/test2.jpg",
        "FullImageUrl": "https://adminsc.pizzahut.lk//images/mainmenu/test2.jpg",
    },
    {
        "Code": "J956",
        "WebCategoryCode": "9MD",
        "WebName": "Grand Dipper Fix Special Offer",
        "IsCustomizable": False,
        "Description": "",
        "DescriptionShort": "...",
        "Url": "grand-dipper-fix",
        "Price": "0.00",
        "CategoryCode": "9MD",
        "ClassificationId": 29,
        "ClassificationName": "Grand Dipper Deals",
        "ImageURL": "/images/mainmenu/test3.jpg",
        "FullImageUrl": "https://adminsc.pizzahut.lk//images/mainmenu/test3.jpg",
    },
]

SAMPLE_PIZZAHUT_BANNER_RESPONSE = {
    "HttpCode": None,
    "DateTime": "2026-09-06T08:00:00Z",
    "Message": None,
    "Data": {
        "DisplayOnDesktop": True,
        "Tiltle": "Summer Special",
        "Id": 23,
        "Description": "Limited time offer",
        "ImageURL": "/images/sliderimages/banner1.jpg",
        "FullImageUrl": "https://adminsc.pizzahut.lk//images/sliderimages/banner1.jpg",
        "Url": "https://www.pizzahut.lk/menu/promo",
        "IsActive": True,
    }
}


# ---------------------------------------------------------------------------
# KFC Scraper Tests
# ---------------------------------------------------------------------------

class TestKFCExtraction:
    """Test KFC HTML item extraction logic."""

    def test_extracts_promo_items_from_html(self):
        """Promotional items are correctly extracted from the promotions page HTML."""
        scraper = KFCScraper()
        items = scraper._extract_items_from_html(SAMPLE_KFC_PROMO_HTML, "/menu/promotions")

        assert len(items) == 2
        assert items[0]["title"] == "8PC H&C BUCKET FOR RS.2990"
        assert items[0]["price"] == 2990.0
        assert "admin-kfc-web.azurewebsites.net" in items[0]["image_url"]

        assert items[1]["title"] == "BUY 2 ZINGER BURGER & GET 1 FREE"
        assert items[1]["price"] == 3180.0

    def test_extracts_combo_deals_from_meals_page(self):
        """Combo meals are correctly extracted from the meals page."""
        scraper = KFCScraper()
        items = scraper._extract_items_from_html(SAMPLE_KFC_MEALS_HTML, "/menu/meals-and-beverages")

        assert len(items) == 1
        assert items[0]["title"] == "Zinger Burger Combo + 400ML PEPSI"
        assert items[0]["price"] == 2530.0

    def test_extracts_regular_menu_items(self):
        """Regular menu items are extracted from the mains page."""
        scraper = KFCScraper()
        items = scraper._extract_items_from_html(SAMPLE_KFC_REGULAR_MENU_HTML, "/menu/mains")

        assert len(items) == 2
        assert items[0]["title"] == "1 Pc Choice (HC)"
        assert items[1]["title"] == "Quarter/2Pc (HC)"

    def test_empty_html_returns_no_items(self):
        """Empty or minimal HTML returns no items."""
        scraper = KFCScraper()
        assert scraper._extract_items_from_html("", "/menu/promotions") == []
        assert scraper._extract_items_from_html("<html></html>", "/menu/promotions") == []

    def test_malformed_html_handled_safely(self):
        """Malformed HTML does not raise exceptions."""
        scraper = KFCScraper()
        malformed = '<div class="itemContainer"><img src="no-host.jpg" alt="bad"></div>'
        items = scraper._extract_items_from_html(malformed, "/menu/promotions")
        # Should not crash, and the item without the KFC image host gets filtered
        assert len(items) == 0


class TestKFCChallengePageDetection:
    """Test bot-challenge / Cloudflare detection — the root cause of today's failure."""

    def test_normal_html_is_not_challenge(self):
        """Real KFC HTML is not flagged as a challenge page."""
        scraper = KFCScraper()
        assert scraper._is_challenge_page(SAMPLE_KFC_PROMO_HTML) is False

    def test_cloudflare_challenge_detected(self):
        """HTML containing Cloudflare challenge markers is detected."""
        scraper = KFCScraper()
        cf_html = '<html><head></head><body>__CF$cv$params={r:\'abc\'}</body></html>'
        assert scraper._is_challenge_page(cf_html) is True

    def test_challenge_platform_url_detected(self):
        scraper = KFCScraper()
        cf_html = '<html><body><script src="/cdn-cgi/challenge-platform/scripts/jsd/main.js"></script></body></html>'
        assert scraper._is_challenge_page(cf_html) is True

    def test_enable_cookies_message_detected(self):
        scraper = KFCScraper()
        cf_html = '<html><body><p>Please enable cookies to continue.</p></body></html>'
        assert scraper._is_challenge_page(cf_html) is True

    def test_empty_html_is_not_challenge(self):
        """Empty string is not treated as a challenge page."""
        scraper = KFCScraper()
        assert scraper._is_challenge_page("") is False
        assert scraper._is_challenge_page(None) is False

    def test_challenge_page_returns_no_items(self):
        """When extraction is called with challenge HTML, it returns empty and logs an error."""
        scraper = KFCScraper()
        cf_html = '<html><body>__CF$cv$params={}</body></html>'
        items = scraper._extract_items_from_html(cf_html, "/menu/promotions")
        assert items == []

    def test_challenge_page_triggers_cache_fallback(self):
        """A Cloudflare-blocked scrape returns cached data, not an empty list."""
        scraper = KFCScraper()
        cached_deals = [
            {"id": "kfc-1", "title": "Cached Deal 1"},
            {"id": "kfc-2", "title": "Cached Deal 2"},
        ]
        cf_html = '<html><body>__CF$cv$params={}</body></html>'

        with patch.object(scraper, '_get_session'), \
             patch.object(scraper, '_fetch_page', return_value=cf_html), \
             patch.object(scraper, '_load_cache', return_value=cached_deals), \
             patch.object(scraper, '_save_cache') as mock_save:
            result = scraper.scrape_live()

        # Should return cached deals, not the empty challenge result
        assert len(result) == 2
        assert result[0]["title"] == "Cached Deal 1"
        # Should NOT have overwritten the cache
        mock_save.assert_not_called()


class TestKFCImageHostMatching:
    """Test the robust image-host matching that replaced exact-string comparison."""

    def test_primary_host_accepted(self):
        scraper = KFCScraper()
        url = "https://admin-kfc-web.azurewebsites.net/images/mainmenu/item.jpg"
        assert scraper._is_kfc_product_image(url) is True

    def test_fallback_kfc_lk_with_mainmenu_accepted(self):
        """If KFC migrates images to kfc.lk domain, mainmenu paths are still accepted."""
        scraper = KFCScraper()
        url = "https://kfc.lk/images/mainmenu/item.jpg"
        assert scraper._is_kfc_product_image(url) is True

    def test_icon_without_mainmenu_rejected(self):
        """Generic icons or logos without 'mainmenu' in the path are rejected."""
        scraper = KFCScraper()
        url = "https://kfc.lk/images/icons/pin.png"
        assert scraper._is_kfc_product_image(url) is False

    def test_unrelated_host_rejected(self):
        scraper = KFCScraper()
        assert scraper._is_kfc_product_image("https://example.com/image.jpg") is False

    def test_empty_url_rejected(self):
        scraper = KFCScraper()
        assert scraper._is_kfc_product_image("") is False
        assert scraper._is_kfc_product_image(None) is False


class TestKFCDealFiltering:
    """Test that normal menu items are correctly filtered out."""

    def test_promo_page_items_are_always_deals(self):
        """Items from /menu/promotions are always classified as deals."""
        scraper = KFCScraper()
        item = {"title": "Some Item", "source_page": "/menu/promotions"}
        assert scraper._is_promotional_deal(item) is True

    def test_regular_chicken_not_a_deal(self):
        """Regular chicken items from the mains page are not deals."""
        scraper = KFCScraper()
        item = {"title": "1 Pc Choice (HC)", "source_page": "/menu/mains"}
        assert scraper._is_promotional_deal(item) is False

    def test_combo_with_drink_is_a_deal(self):
        """Combo items with drinks from the meals page are deals."""
        scraper = KFCScraper()
        item = {"title": "Zinger Burger Combo + 400ML PEPSI", "source_page": "/menu/meals-and-beverages"}
        assert scraper._is_promotional_deal(item) is True

    def test_for_rs_price_is_a_deal(self):
        """Items with 'FOR RS.' in the title indicate a special price deal."""
        scraper = KFCScraper()
        item = {"title": "8PC H&C BUCKET FOR RS.2990", "source_page": "/menu/any"}
        assert scraper._is_promotional_deal(item) is True

    def test_plain_rice_not_a_deal(self):
        """A regular rice item from a non-promo page isn't a deal."""
        scraper = KFCScraper()
        item = {"title": "Chicken Rice", "source_page": "/menu/mains"}
        assert scraper._is_promotional_deal(item) is False


class TestKFCDeduplication:
    """Test duplicate deal removal."""

    def test_duplicate_titles_removed(self):
        """Items with the same title (case-insensitive) are deduplicated."""
        scraper = KFCScraper()

        # Create HTML with duplicate items
        dupe_html = SAMPLE_KFC_PROMO_HTML + """
        <div class="col-lg-3 col-md-4 col-sm-6 col-xs-12 itemContainer">
            <div class="itemBorder"><div class="box"><div class="row">
                <div class="col-md-12 itemImageContainer"><div class="itemImage"><center>
                    <img src="https://admin-kfc-web.azurewebsites.net/images/mainmenu/dup.jpg" alt="8PC H&amp;C BUCKET FOR RS.2990" />
                </center></div></div>
                <div class="col-md-12 itemDetailContainer">
                    <div class="row"><div class="col-md-12">
                        <h3 class="menu-item-name hidden-sm hidden-xs" title="8PC H&amp;C BUCKET FOR RS.2990">8PC H&amp;C BUCKET FOR RS.2990 </h3>
                    </div></div>
                    <div class="menu-price-container-parent"><div class="row"><div>
                        <div class="submenus-1"><div class="col-md-12 menu-price-container">
                            <span class="price">Rs. 2,990</span>
                        </div></div>
                    </div></div></div>
                </div>
            </div></div></div>
        </div>
        """

        items = scraper._extract_items_from_html(dupe_html, "/menu/promotions")
        # Should have 3 items from HTML (2 + 1 duplicate)
        assert len(items) == 3

        # But scrape_live should deduplicate
        with patch.object(scraper, '_get_session') as mock_session, \
             patch.object(scraper, '_fetch_page') as mock_fetch, \
             patch.object(scraper, '_load_cache', return_value=[]), \
             patch.object(scraper, '_save_cache'):
            mock_fetch.return_value = dupe_html
            # Only mock one page
            with patch('scrapers.vendors.kfc.KFC_PROMO_PAGES', ['/menu/promotions']), \
                 patch('scrapers.vendors.kfc.KFC_DEAL_PAGES', []):
                offers = scraper.scrape_live()

        titles = [o["title"] for o in offers]
        assert len(titles) == len(set(t.lower().strip() for t in titles)), "Duplicate titles found in output"


class TestKFCDeterminism:
    """Test that the same input produces the same output."""

    def test_same_html_produces_same_output(self):
        """Running extraction twice on the same HTML produces identical results."""
        scraper = KFCScraper()
        items1 = scraper._extract_items_from_html(SAMPLE_KFC_PROMO_HTML, "/menu/promotions")
        items2 = scraper._extract_items_from_html(SAMPLE_KFC_PROMO_HTML, "/menu/promotions")
        assert items1 == items2

    def test_stable_ids_are_deterministic(self):
        """IDs generated from the same input are always the same."""
        scraper = KFCScraper()
        id1 = scraper._generate_stable_id("Test Deal", "/menu/promotions")
        id2 = scraper._generate_stable_id("Test Deal", "/menu/promotions")
        assert id1 == id2
        assert id1.startswith("kfc-")


class TestKFCValidation:
    """Test the scrape validation logic."""

    def test_zero_deals_fails_validation(self):
        """An empty deal list fails validation."""
        scraper = KFCScraper()
        assert scraper._validate_deals([], []) is False

    def test_deal_drop_passes_validation(self):
        """Valid deal count reductions (e.g. expired promos) pass validation without being rejected."""
        scraper = KFCScraper()
        cached = [{"title": f"Deal {i}"} for i in range(10)]
        new = [{"title": "Deal 1"}]
        assert scraper._validate_deals(new, cached) is True

    def test_normal_count_passes_validation(self):
        """A reasonable deal count passes validation."""
        scraper = KFCScraper()
        deals = [{"title": f"Deal {i}"} for i in range(5)]
        cached = [{"title": f"Deal {i}"} for i in range(6)]
        assert scraper._validate_deals(deals, cached) is True

    def test_first_run_no_cache_passes(self):
        """When there's no cache, even a small count passes validation."""
        scraper = KFCScraper()
        deals = [{"title": "Deal 1"}]
        assert scraper._validate_deals(deals, []) is True

    def test_mostly_duplicate_titles_fails(self):
        """If most titles are duplicates, validation fails."""
        scraper = KFCScraper()
        deals = [{"title": "Same Deal"} for _ in range(10)]
        assert scraper._validate_deals(deals, []) is False

    def test_failed_scrape_preserves_cache(self):
        """A failed scrape should return the cached data, not overwrite it."""
        scraper = KFCScraper()
        cached_deals = [
            {"id": "kfc-1", "title": "Cached Deal 1"},
            {"id": "kfc-2", "title": "Cached Deal 2"},
        ]

        with patch.object(scraper, '_get_session'), \
             patch.object(scraper, '_fetch_page', return_value=None), \
             patch.object(scraper, '_load_cache', return_value=cached_deals), \
             patch.object(scraper, '_save_cache') as mock_save:
            result = scraper.scrape_live()

        # Should return cached deals
        assert len(result) == 2
        assert result[0]["title"] == "Cached Deal 1"
        # Should NOT have overwritten the cache
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# Pizza Hut Scraper Tests
# ---------------------------------------------------------------------------

class TestPizzaHutExtraction:
    """Test Pizza Hut API item parsing."""

    def test_parses_promo_items_from_api(self):
        """Promo items are correctly parsed from the API response."""
        scraper = PizzaHutScraper()
        offers = scraper._parse_promo_items(SAMPLE_PIZZAHUT_PROMO_RESPONSE)

        assert len(offers) == 3

        # Check the Weekend Vibes item
        vibes = next(o for o in offers if "Weekend Vibes" in o["title"])
        assert vibes["id"] == "pizzahut-b091"
        assert vibes["category"] == "Meal Deals"
        assert "adminsc.pizzahut.lk" in vibes["image_url"]

        # Check the Cyber Savings item with price
        cyber = next(o for o in offers if "Cyber" in o["title"])
        assert cyber["id"] == "pizzahut-b124"
        assert cyber["category"] == "Cyber Savings"
        assert cyber["discounted_price"] == 4900.0

        # Check Grand Dipper
        dipper = next(o for o in offers if "Grand Dipper" in o["title"])
        assert dipper["id"] == "pizzahut-j956"
        assert dipper["category"] == "Grand Dipper Deals"

    def test_empty_api_response(self):
        """Empty API response returns no items."""
        scraper = PizzaHutScraper()
        assert scraper._parse_promo_items([]) == []

    def test_malformed_api_items_handled(self):
        """Malformed items in the API response are skipped safely."""
        scraper = PizzaHutScraper()
        bad_data = [
            {},  # Empty dict
            {"Code": "X1"},  # No WebName
            None,  # Not a dict
            "garbage",  # Not a dict
            {"Code": "X2", "WebName": "Valid Item", "ClassificationName": "Test",
             "FullImageUrl": "https://adminsc.pizzahut.lk/img.jpg", "Url": "test"},
        ]
        offers = scraper._parse_promo_items(bad_data)
        assert len(offers) == 1
        assert offers[0]["title"] == "Valid Item"

    def test_duplicate_codes_removed(self):
        """Items with the same code are deduplicated."""
        scraper = PizzaHutScraper()
        dupes = [
            {"Code": "B091", "WebName": "Offer 1", "ClassificationName": "Test",
             "FullImageUrl": "https://adminsc.pizzahut.lk/img.jpg"},
            {"Code": "B091", "WebName": "Offer 1 Duplicate", "ClassificationName": "Test",
             "FullImageUrl": "https://adminsc.pizzahut.lk/img2.jpg"},
        ]
        offers = scraper._parse_promo_items(dupes)
        assert len(offers) == 1


class TestPizzaHutBanner:
    """Test banner parsing."""

    def test_parses_banner_correctly(self):
        """A valid banner is parsed with correct fields."""
        scraper = PizzaHutScraper()
        banner = scraper._parse_banner(SAMPLE_PIZZAHUT_BANNER_RESPONSE["Data"])

        assert banner is not None
        assert banner["title"] == "Summer Special"
        assert "adminsc.pizzahut.lk" in banner["image_url"]
        assert banner["category"] == "Cyber Savings"

    def test_banner_with_generic_title_gets_fallback(self):
        """A banner with only 'New' as title gets a fallback title."""
        scraper = PizzaHutScraper()
        data = {
            "Tiltle": "New",
            "Description": "New",
            "FullImageUrl": "https://adminsc.pizzahut.lk/img.jpg",
        }
        banner = scraper._parse_banner(data)
        assert banner is not None
        assert banner["title"] == "Pizza Hut Featured Promotion"

    def test_banner_with_no_image_returns_none(self):
        """A banner without an image URL is skipped."""
        scraper = PizzaHutScraper()
        data = {"Tiltle": "Test", "FullImageUrl": ""}
        assert scraper._parse_banner(data) is None

    def test_banner_with_azure_url_cleaned(self):
        """Banner URLs pointing to Azure get replaced with the main website."""
        scraper = PizzaHutScraper()
        data = {
            "Tiltle": "Test Banner",
            "FullImageUrl": "https://adminsc.pizzahut.lk/img.jpg",
            "Url": "https://ph-asp2-prd-website-pizzahut-lk.azurewebsites.net/",
        }
        banner = scraper._parse_banner(data)
        assert "azurewebsites.net" not in banner["source_url"]
        assert banner["source_url"] == "https://www.pizzahut.lk"


class TestPizzaHutImageNormalization:
    """Test image URL normalization."""

    def test_relative_url_normalized(self):
        """Relative image URLs are converted to absolute."""
        scraper = PizzaHutScraper()
        url = scraper._normalize_image_url("/images/mainmenu/test.jpg")
        assert url.startswith("https://adminsc.pizzahut.lk")
        assert url.endswith("test.jpg")

    def test_double_slash_fixed(self):
        """Double slashes in the URL path are fixed."""
        scraper = PizzaHutScraper()
        url = scraper._normalize_image_url("https://adminsc.pizzahut.lk//images/test.jpg")
        assert "//" not in url.split("://")[1]

    def test_empty_url_returns_empty(self):
        """Empty or None URLs return empty string."""
        scraper = PizzaHutScraper()
        assert scraper._normalize_image_url("") == ""
        assert scraper._normalize_image_url(None) == ""


class TestPizzaHutDeterminism:
    """Test deterministic output."""

    def test_same_api_response_same_output(self):
        """Parsing the same API data twice produces identical results."""
        scraper = PizzaHutScraper()
        offers1 = scraper._parse_promo_items(SAMPLE_PIZZAHUT_PROMO_RESPONSE)
        offers2 = scraper._parse_promo_items(SAMPLE_PIZZAHUT_PROMO_RESPONSE)
        assert offers1 == offers2

    def test_stable_ids_are_deterministic(self):
        """IDs generated from the same code are always the same."""
        scraper = PizzaHutScraper()
        id1 = scraper._generate_stable_id("B091", "Offer 1")
        id2 = scraper._generate_stable_id("B091", "Offer 1")
        assert id1 == id2
        assert id1 == "pizzahut-b091"


class TestPizzaHutValidation:
    """Test scrape validation logic."""

    def test_zero_deals_fails_validation(self):
        """An empty deal list fails validation."""
        scraper = PizzaHutScraper()
        assert scraper._validate_deals([], []) is False

    def test_deal_drop_fails_validation(self):
        """A large drop in deal count fails validation."""
        scraper = PizzaHutScraper()
        cached = [{"title": f"Deal {i}"} for i in range(20)]
        new = [{"title": "Deal 1"}]
        assert scraper._validate_deals(new, cached) is False

    def test_normal_count_passes(self):
        """A reasonable deal count passes validation."""
        scraper = PizzaHutScraper()
        deals = [{"title": f"Deal {i}"} for i in range(10)]
        cached = [{"title": f"Deal {i}"} for i in range(12)]
        assert scraper._validate_deals(deals, cached) is True

    def test_failed_scrape_preserves_cache(self):
        """A failed scrape should return cached data instead of overwriting."""
        scraper = PizzaHutScraper()
        cached_deals = [
            {"id": "ph-1", "title": "Cached PH Deal 1"},
            {"id": "ph-2", "title": "Cached PH Deal 2"},
        ]

        with patch.object(scraper, '_get_token', return_value=None), \
             patch.object(scraper, '_load_cache', return_value=cached_deals), \
             patch.object(scraper, '_save_cache') as mock_save:
            result = scraper.scrape_live()

        assert len(result) == 2
        assert result[0]["title"] == "Cached PH Deal 1"
        mock_save.assert_not_called()


# ---------------------------------------------------------------------------
# BaseScraper Integration Tests
# ---------------------------------------------------------------------------

class TestBaseScraperNormalization:
    """Test BaseScraper price normalization and offer processing."""

    def test_deal_with_only_discounted_price_accepted(self):
        """Deals with only a discounted price (no original) are accepted."""
        class TestScraper(BaseScraper):
            vendor_id = "test"
            vendor_name = "Test"

            def scrape_live(self):
                return [
                    {"title": "KFC Combo", "discounted_price": 2530},
                ]

        result = TestScraper().get_offers()
        assert result["count"] == 1
        assert result["offers"][0]["discounted_price"] == 2530

    def test_deal_with_no_price_accepted(self):
        """Promotional deals without any price are accepted."""
        class TestScraper(BaseScraper):
            vendor_id = "test"
            vendor_name = "Test"

            def scrape_live(self):
                return [
                    {"title": "Banner Promo", "deal_type": "Featured"},
                ]

        result = TestScraper().get_offers()
        assert result["count"] == 1

    def test_deal_with_valid_discount_accepted(self):
        """Deals with original > discounted price are accepted with correct discount."""
        class TestScraper(BaseScraper):
            vendor_id = "test"
            vendor_name = "Test"

            def scrape_live(self):
                return [
                    {"title": "Discounted Item", "discounted_price": 1000, "original_price": 2000},
                ]

        result = TestScraper().get_offers()
        assert result["count"] == 1
        assert result["offers"][0]["discount_percentage"] == 50

    def test_deal_with_invalid_compare_price_filtered(self):
        """Items where original_price < discounted_price (with no discount %) are filtered."""
        class TestScraper(BaseScraper):
            vendor_id = "test"
            vendor_name = "Test"

            def scrape_live(self):
                return [
                    {"title": "Bad Compare", "discounted_price": 1500, "original_price": 1200},
                ]

        result = TestScraper().get_offers()
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# Existing Tests (preserved from original)
# ---------------------------------------------------------------------------

from scrapers.manager import ScraperManager

EXPECTED_VENDORS = [
    "kfc", "pizzahut", "dominos", "tacobell", "burgerking", "popeyes",
    "fullerburgers", "creperunner", "subway", "dinemore",
    "chinesedragon", "breadtalk", "ubereats", "pickme"
]


def test_scraper_manager_registered_vendors():
    manager = ScraperManager()
    vendors = manager.get_registered_vendors()
    vendor_ids = [v["id"] for v in vendors]
    for expected in EXPECTED_VENDORS:
        assert expected in vendor_ids, f"Vendor {expected} not registered in manager"


def test_base_scraper_normalization():
    class DummyScraper(BaseScraper):
        vendor_id = "dummy"
        vendor_name = "Dummy Vendor"

        def scrape_live(self):
            return [
                # Item without compare price (should now be accepted with only disc price)
                {"title": "Item A", "discounted_price": 1000},
                # Item with genuine discount (2000 down to 1000)
                {"title": "Item B", "discounted_price": 1000, "original_price": 2000},
                # Item with compare price less than discounted price (should be filtered out)
                {"title": "Item C", "discounted_price": 1500, "original_price": 1200},
            ]

    scraper = DummyScraper()
    result = scraper.get_offers()
    offers = result["offers"]

    # Item A (disc price only) and Item B (genuine discount) should be kept
    # Item C (invalid compare) should be filtered
    assert len(offers) == 2
    titles = [o["title"] for o in offers]
    assert "Item A" in titles
    assert "Item B" in titles
    assert "Item C" not in titles

    item_b = next(o for o in offers if o["title"] == "Item B")
    assert item_b["discounted_price"] == 1000
    assert item_b["original_price"] == 2000
    assert item_b["discount_percentage"] == 50


# ---------------------------------------------------------------------------
# Popeyes Scraper Tests
# ---------------------------------------------------------------------------

SAMPLE_POPEYES_HTML = """
<!DOCTYPE html>
<html>
<head><title>Popeyes Sri Lanka</title></head>
<body>
    <img id="logo" src="https://popeyes.com.lk/uploads/Header_80x130_01_d89e84a414.png" />
    <img id="header-banner" src="https://popeyes.com.lk/uploads/Header_Banner_1436x517_01_0414329313.png" />
    <span id="premium-selection-title-area"><h5><strong>Signature Products</strong></h5></span>
    <span id="premium-selection-area" class="row align-items-center">
        <div class="col">
            <img id="premium_selection_img" data-src="https://popeyes.com.lk/uploads/PLK_Sandwich_BOGO_KV_b481298226.jpg" class="lazy" />
        </div>
        <div class="col">
            <img id="premium_selection_img" data-src="https://popeyes.com.lk/uploads/PLK_Drumstick_Deal_03_377724312a.jpg" class="lazy" />
        </div>
        <div class="col">
            <img id="premium_selection_img" data-src="https://popeyes.com.lk/uploads/PLK_BOGO_KV_e8b41d26f7.jpg" class="lazy" />
        </div>
        <div class="col">
            <img id="premium_selection_img" data-src="https://popeyes.com.lk/uploads/PLK_Big_Box_01_abd7e98543.jpg" class="lazy" />
        </div>
    </span>
    <!-- Mobile duplicate layout that should be deduplicated -->
    <div class="row row-cols-2 row-cols-md-2 g-4">
        <div class="col">
            <img id="premium_selection_img" data-src="https://popeyes.com.lk/uploads/PLK_Sandwich_BOGO_KV_b481298226.jpg" class="lazy" />
        </div>
    </div>
</body>
</html>
"""


class TestPopeyesExtraction:
    """Test Popeyes HTML deal extraction and deduplication."""

    def test_extracts_signature_deals_and_banner(self):
        """Extracts the 4 signature promo posters and header banner from Popeyes HTML."""
        scraper = PopeyesScraper()
        deals = scraper._extract_deals_from_html(SAMPLE_POPEYES_HTML)

        # 1 header banner + 4 signature products = 5 unique deals
        assert len(deals) == 5

        titles = [d["title"] for d in deals]
        assert "Spicy Double Deal - Buy 1 Get 1 FREE" in titles
        assert "Drumstick Deal - Buy 4 Get 4 FREE" in titles
        assert "Why Stop at 1? Make it Double - Buy 1 Get 1 FREE" in titles
        assert "Big Box - 10 Ways to Go Big" in titles
        assert "Popeyes Louisiana Chicken Promotion" in titles

    def test_prices_and_discounts_mapped_correctly(self):
        """Validates pricing, categories, and validity strings on signature deals."""
        scraper = PopeyesScraper()
        deals = scraper._extract_deals_from_html(SAMPLE_POPEYES_HTML)

        tuesday_deal = next(d for d in deals if "Spicy Double Deal" in d["title"])
        assert tuesday_deal["discounted_price"] == 1600.0
        assert tuesday_deal["original_price"] == 3200.0
        assert tuesday_deal["discount_percentage"] == 50
        assert tuesday_deal["category"] == "Sandwiches & Burgers"
        assert tuesday_deal["valid_until"] == "Every Tuesday"

        friday_deal = next(d for d in deals if "Drumstick Deal" in d["title"])
        assert friday_deal["discounted_price"] == 2800.0
        assert friday_deal["original_price"] == 4720.0
        assert friday_deal["discount_percentage"] == 41
        assert friday_deal["category"] == "Chicken Buckets"
        assert friday_deal["valid_until"] == "Every Friday"

        saturday_deal = next(d for d in deals if "Why Stop at 1?" in d["title"])
        assert saturday_deal["discounted_price"] == 1600.0
        assert saturday_deal["valid_until"] == "Every Saturday"

    def test_duplicate_images_deduplicated(self):
        """Duplicate mobile and desktop images in DOM are deduplicated to single offer."""
        scraper = PopeyesScraper()
        deals = scraper._extract_deals_from_html(SAMPLE_POPEYES_HTML)
        image_urls = [d["image_url"] for d in deals]
        assert len(image_urls) == len(set(image_urls))

    def test_empty_or_malformed_html_returns_empty(self):
        """Empty HTML returns empty list without error."""
        scraper = PopeyesScraper()
        assert scraper._extract_deals_from_html("") == []
        assert scraper._extract_deals_from_html("<html><body><p>No images</p></body></html>") == []

    def test_generic_banner_fallback(self):
        """New unrecognized promo banners are parsed cleanly."""
        scraper = PopeyesScraper()
        deal = scraper._parse_generic_banner(
            "https://popeyes.com.lk/uploads/PLK_Wings_Party_Pack_12345678.jpg",
            "Wings Party Pack Promotion"
        )
        assert deal["title"] == "Wings Party Pack Promotion"
        assert deal["category"] == "Tenders"
        assert deal["deal_type"] == "Special Promotion"
        assert deal["id"].startswith("popeyes-")


class TestPopeyesDeterminismAndValidation:
    """Test deterministic IDs and cache fallback."""

    def test_stable_ids_are_deterministic(self):
        scraper = PopeyesScraper()
        id1 = scraper._generate_stable_id("https://popeyes.com.lk/img.jpg", "Spicy Deal")
        id2 = scraper._generate_stable_id("https://popeyes.com.lk/img.jpg", "Spicy Deal")
        assert id1 == id2
        assert id1.startswith("popeyes-")

    def test_validation_passes_on_valid_deals(self):
        scraper = PopeyesScraper()
        deals = [{"title": "Deal 1"}, {"title": "Deal 2"}]
        assert scraper._validate_deals(deals, []) is True

    def test_validation_fails_on_zero_deals(self):
        scraper = PopeyesScraper()
        assert scraper._validate_deals([], []) is False

    def test_failed_scrape_preserves_cache(self):
        scraper = PopeyesScraper()
        cached = [{"id": "popeyes-1", "title": "Cached Popeyes Deal"}]

        with patch("requests.get", side_effect=Exception("Connection refused")), \
             patch.object(scraper, "_load_cache", return_value=cached), \
             patch.object(scraper, "_save_cache") as mock_save:
            deals = scraper.scrape_live()

        assert len(deals) == 1
        assert deals[0]["title"] == "Cached Popeyes Deal"
        mock_save.assert_not_called()

