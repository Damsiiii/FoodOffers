import logging
from typing import List, Dict, Any, Optional
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

def fetch_dynamic_deals(url: str, timeout: int = 15000) -> List[Dict[str, Any]]:
    """
    Launches headless Playwright browser to fetch dynamic rendered DOM and image URLs.
    """
    deals = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, timeout=timeout, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

            extracted = page.evaluate("""() => {
                const items = [];
                const imgElements = document.querySelectorAll('img');
                imgElements.forEach(img => {
                    const src = img.src || img.getAttribute('data-src') || img.getAttribute('srcset');
                    if (!src || src.startsWith('data:') || src.includes('logo') || src.includes('icon')) return;

                    const parent = img.closest('div, article, section, li, a') || img.parentElement;
                    if (!parent) return;

                    const text = parent.innerText ? parent.innerText.trim() : '';
                    if (!text || text.length < 5) return;

                    items.push({
                        title: text.split('\\n')[0].trim(),
                        full_text: text.replace(/\\n/g, ' '),
                        image_url: src
                    });
                });
                return items;
            }""")

            seen_titles = set()
            for item in extracted:
                title = item['title']
                if title and title not in seen_titles and len(title) > 3:
                    seen_titles.add(title)
                    deals.append(item)

            browser.close()
    except Exception as e:
        logger.warning(f"Playwright dynamic fetch failed for {url}: {e}")

    return deals
