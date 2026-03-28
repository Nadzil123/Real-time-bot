from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_webhook_url: str
    discord_channel_id: int
    search_url: str
    wiki_base_url: str
    post_keyword: str
    poll_minutes: int
    user_agent: str


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        discord_webhook_url=_require("DISCORD_WEBHOOK_URL"),
        discord_channel_id=int(os.getenv("DISCORD_CHANNEL_ID", "0")),
        search_url=_require("SEARCH_URL"),
        wiki_base_url=_require("WIKI_BASE_URL"),
        post_keyword=os.getenv("POST_KEYWORD", "Gag Value List").strip().lower(),
        poll_minutes=max(1, int(os.getenv("POLL_MINUTES", "30"))),
        user_agent=os.getenv(
            "USER_AGENT", "Mozilla/5.0 (compatible; GrowAGardenPriceBot/1.0)"
        ),
    )
