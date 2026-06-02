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
    admin_role_name: str | None
    database_path: Path
    card_image_base_url: str
    card_image_version: str


def _int_or_none(value: str | None) -> int | None:
    """Discord ID каналу/сервера — лише цифри."""
    if not value or not value.strip():
        return None
    raw = value.strip()
    if not raw.isdigit():
        return None
    return int(raw)


def _admin_role_from_env() -> tuple[int | None, str | None]:
    """
    ADMIN_ROLE_ID — цифри (ID ролі).
    ADMIN_ROLE_NAME — назва ролі (наприклад Owner).
    Якщо в ADMIN_ROLE_ID вказано текст — трактуємо як назву (зручно для .env).
    """
    role_id: int | None = None
    role_name: str | None = None

    name_raw = os.getenv("ADMIN_ROLE_NAME", "").strip()
    if name_raw:
        role_name = name_raw

    id_raw = os.getenv("ADMIN_ROLE_ID", "").strip()
    if id_raw:
        if id_raw.isdigit():
            role_id = int(id_raw)
        elif not role_name:
            role_name = id_raw

    return role_id, role_name


def load_settings() -> Settings:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is not set")

    admin_role_id, admin_role_name = _admin_role_from_env()
    db = os.getenv("DATABASE_PATH", "data/stalker_cards.db").strip()
    return Settings(
        token=token,
        guild_id=_int_or_none(os.getenv("GUILD_ID")),
        channel_news=_int_or_none(os.getenv("CHANNEL_CARD_NEWS")),
        channel_trade_market=_int_or_none(os.getenv("CHANNEL_CARD_TRADE_MARKET")),
        channel_collections=_int_or_none(os.getenv("CHANNEL_CARD_COLLECTIONS")),
        channel_completed=_int_or_none(os.getenv("CHANNEL_CARD_COMPLETED")),
        channel_rules=_int_or_none(os.getenv("CHANNEL_CARD_RULES")),
        admin_role_id=admin_role_id,
        admin_role_name=admin_role_name,
        database_path=Path(db),
        card_image_base_url=os.getenv(
            "CARD_IMAGE_BASE_URL", "https://s2-atb-checklist.web.app/cards"
        )
        .strip()
        .rstrip("/"),
        card_image_version=os.getenv("CARD_IMAGE_VERSION", "2").strip(),
    )
