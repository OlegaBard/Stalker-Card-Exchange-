from __future__ import annotations

import os

DEFAULT_CARD_IMAGE_BASE = "https://s2-atb-checklist.web.app/cards"
DEFAULT_CARD_IMAGE_VERSION = "2"


def card_image_url(card_id: int, *, base_url: str | None = None, version: str | None = None) -> str:
    """Публічні арти колекції АТБ (card-{id}.webp, без ведучого нуля)."""
    base = (base_url or os.getenv("CARD_IMAGE_BASE_URL") or DEFAULT_CARD_IMAGE_BASE).rstrip("/")
    ver = version or os.getenv("CARD_IMAGE_VERSION") or DEFAULT_CARD_IMAGE_VERSION
    return f"{base}/card-{card_id}.webp?v={ver}"
