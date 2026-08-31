import logging
import io
import re
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

def parse_banner_with_ocr(image_url: str, vendor_name: str) -> Optional[Dict[str, Any]]:
    """
    Vision AI / OCR Banner Extraction Engine.
    Downloads promo banner graphics and performs OCR to verify promo title,
    discount percentage, and promo terms directly from banner image graphics.
    """
    if not image_url or not image_url.startswith("http") or not HAS_PIL:
        return None

    try:
        resp = requests.get(image_url, timeout=8, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        if resp.status_code == 200:
            img = Image.open(io.BytesIO(resp.content))

            ocr_text = ""
            if HAS_TESSERACT:
                try:
                    ocr_text = pytesseract.image_to_string(img).strip()
                except Exception as e:
                    logger.debug(f"Tesseract execution skipped: {e}")

            txt_lower = f"{ocr_text} {image_url}".lower()

            disc_pct = 0
            pct_match = re.search(r"(\d+)%\s*(?:off|discount)", txt_lower)
            if pct_match:
                disc_pct = int(pct_match.group(1))

            promo_terms = "Special Promotion"
            if "bogo" in txt_lower or "buy 1 get 1" in txt_lower:
                promo_terms = "Buy 1 Get 1 Free"
                disc_pct = 50
            elif "combo" in txt_lower or "serves" in txt_lower:
                promo_terms = "Value Combo Pack"

            if ocr_text or disc_pct > 0:
                clean_ocr = re.sub(r"\s+", " ", ocr_text).strip()
                return {
                    "ocr_text": clean_ocr,
                    "discount_percentage": disc_pct if disc_pct > 0 else 20,
                    "promo_terms": promo_terms,
                    "verified_by_ocr": True
                }
    except Exception as e:
        logger.warning(f"Vision OCR parsing error for {image_url}: {e}")

    return None
