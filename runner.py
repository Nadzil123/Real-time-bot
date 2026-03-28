from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path

from notifier import send_webhook
from scraper import PetRecord, scrape_latest_prices
from settings import load_settings


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("grow-a-garden-runner")

DATA_DIR = Path("data")
SNAPSHOT_FILE = DATA_DIR / "latest_snapshot.json"


def run() -> None:
    settings = load_settings()
    while True:
        try:
            logger.info("Starting scrape cycle")
            result = scrape_latest_prices(settings)
            if snapshot_changed(result.records):
                save_snapshot(result.records)
                send_webhook(settings.discord_webhook_url, result)
                logger.info("Posted %s records to Discord", len(result.records))
            else:
                logger.info("No price change detected")
        except Exception:
            logger.exception("Polling failed")

        logger.info("Sleeping for %s minutes", settings.poll_minutes)
        time.sleep(settings.poll_minutes * 60)


def snapshot_changed(records: list[PetRecord]) -> bool:
    previous = load_snapshot()
    current = [asdict(record) for record in records]
    return previous != current


def load_snapshot() -> list[dict]:
    if not SNAPSHOT_FILE.exists():
        return []
    return json.loads(SNAPSHOT_FILE.read_text())


def save_snapshot(records: list[PetRecord]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    SNAPSHOT_FILE.write_text(json.dumps([asdict(record) for record in records], indent=2))
