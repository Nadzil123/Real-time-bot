from __future__ import annotations

from math import ceil

import requests

from scraper import PetRecord, ScrapeResult


EMBED_COLOR = 0x58A55C
ITEMS_PER_EMBED = 15


def build_embed_payloads(result: ScrapeResult) -> list[dict]:
    total_pages = max(1, ceil(len(result.records) / ITEMS_PER_EMBED))
    payloads: list[dict] = []

    for page_index, chunk in enumerate(chunk_records(result.records, ITEMS_PER_EMBED), start=1):
        title_suffix = f" ({page_index}/{total_pages})" if total_pages > 1 else ""
        embeds = [
            {
                "title": f"Grow a Garden Token Values{title_suffix}",
                "description": (
                    f"**Post:** {result.article_title}\n"
                    f"**Tanggal:** {result.article_date or 'tidak ditemukan'}\n"
                    f"**Sumber:** {result.article_url}"
                ),
                "color": EMBED_COLOR,
                "fields": [build_record_field(index, record) for index, record in chunk],
                "footer": {"text": f"{len(result.records)} pets parsed"},
            }
        ]
        payloads.append({"embeds": embeds})

    return payloads


def build_record_field(index: int, record: PetRecord) -> dict:
    rarity = record.rarity.title() if record.rarity else "Unknown"
    return {
        "name": f"{index}. {record.name}",
        "value": f"Rarity: **{rarity}**\nToken: **{record.token_price}**",
        "inline": True,
    }


def chunk_records(records: list[PetRecord], size: int) -> list[list[tuple[int, PetRecord]]]:
    indexed_records = list(enumerate(records, start=1))
    return [indexed_records[i : i + size] for i in range(0, len(indexed_records), size)]


def send_webhook(webhook_url: str, result: ScrapeResult) -> None:
    for payload in build_embed_payloads(result):
        response = requests.post(webhook_url, json=payload, timeout=30)
        response.raise_for_status()
