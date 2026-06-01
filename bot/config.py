from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TOTAL_CARDS = 48
TRADE_EXPIRE_HOURS = 24


@dataclass(frozen=True)
class Colors:
    background: int = 0x1A1F16
    swamp_green: int = 0x4A5D23
    radiation_yellow: int = 0xC4A000
    metal_gray: int = 0x6B7280
    danger_red: int = 0xDC2626
    success: int = 0x3D5A2E


COLORS = Colors()


@dataclass(frozen=True)
class Settings:
    token: str
    guild_id: int | None
    channel_news: int | None
    channel_trade_market: int | None
    channel_collections: int | None
    channel_completed: int | None
    channel_rules: int | None
    admin_role_id: int | None
    database_path: Path


def _int_or_none(value: str | None) -> int | None:
    if not value or not value.strip():
        return None
    return int(value.strip())


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")

    db = os.getenv("DATABASE_PATH", "data/stalker_cards.db").strip()
    return Settings(
        token=token,
        guild_id=_int_or_none(os.getenv("GUILD_ID")),
        channel_news=_int_or_none(os.getenv("CHANNEL_CARD_NEWS")),
        channel_trade_market=_int_or_none(os.getenv("CHANNEL_CARD_TRADE_MARKET")),
        channel_collections=_int_or_none(os.getenv("CHANNEL_CARD_COLLECTIONS")),
        channel_completed=_int_or_none(os.getenv("CHANNEL_CARD_COMPLETED")),
        channel_rules=_int_or_none(os.getenv("CHANNEL_CARD_RULES")),
        admin_role_id=_int_or_none(os.getenv("ADMIN_ROLE_ID")),
        database_path=Path(db),
    )
