import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from scrapers.manager import ScraperManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("update_offers")

def main():
    root_dir = Path(__file__).parent.parent
    output_dir = root_dir / "src" / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "offers.json"

    logger.info("Initializing ScraperManager...")
    manager = ScraperManager()

    logger.info("Fetching vendor offers...")
    payload = manager.fetch_all_offers()
    payload["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully wrote {payload['total_offers']} offers across {payload['total_vendors']} vendors to {output_file}")

if __name__ == "__main__":
    main()
