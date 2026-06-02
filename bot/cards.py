from __future__ import annotations

from dataclasses import dataclass

from bot.card_images import card_image_url
from bot.config import TOTAL_CARDS

# Категорії колекції S.T.A.L.K.E.R. 2 × АТБ (офіційна нумерація на картках)
CATEGORY_EVENT = "Подія"
CATEGORY_CHARACTER = "Персонаж"
CATEGORY_FACTION = "Фракція"
CATEGORY_RESEARCH = "Дослідження"
CATEGORY_XLAB = "Х-Лабораторія"
CATEGORY_ARTIFACT = "Артефакт"

CATEGORIES: tuple[str, ...] = (
    CATEGORY_EVENT,
    CATEGORY_CHARACTER,
    CATEGORY_FACTION,
    CATEGORY_RESEARCH,
    CATEGORY_XLAB,
    CATEGORY_ARTIFACT,
)


@dataclass(frozen=True, slots=True)
class Card:
    id: int
    name: str
    category: str

    @property
    def code(self) -> str:
        return f"#{self.id:02d}"

    @property
    def image_url(self) -> str:
        return card_image_url(self.id)

    def label(self, owned: bool = False, qty: int = 0) -> str:
        mark = "✅" if owned else "❌"
        suffix = f" x{qty}" if qty > 1 else (" x1" if qty == 1 and owned else "")
        return f"{self.code} {self.name} {mark}{suffix}"


# Джерело: колекція АТБ × S.T.A.L.K.E.R. 2 (s2-atb-checklist.web.app / альманах)
_CARD_DATA: tuple[tuple[int, str, str], ...] = (
    (1, "Перші Експерименти", CATEGORY_EVENT),
    (2, "Аномальна Зона", CATEGORY_EVENT),
    (3, "Загони Евакуації", CATEGORY_EVENT),
    (4, "Рейд Стрільця", CATEGORY_EVENT),
    (5, "Війна Угруповань", CATEGORY_EVENT),
    (6, "Випалювач Мізків", CATEGORY_EVENT),
    (7, "С-Свідомість", CATEGORY_EVENT),
    (8, "Операція Фарватер", CATEGORY_EVENT),
    (9, "Скіф", CATEGORY_CHARACTER),
    (10, "Ріхтер", CATEGORY_CHARACTER),
    (11, "Коршунов", CATEGORY_CHARACTER),
    (12, "Далін", CATEGORY_CHARACTER),
    (13, "Шрам", CATEGORY_CHARACTER),
    (14, "Бродяга", CATEGORY_CHARACTER),
    (15, "Фауст", CATEGORY_CHARACTER),
    (16, "Стрілець", CATEGORY_CHARACTER),
    (17, "Доктор", CATEGORY_CHARACTER),
    (18, "Дегтярьов", CATEGORY_CHARACTER),
    (19, "Агата", CATEGORY_CHARACTER),
    (20, "Сидорович", CATEGORY_CHARACTER),
    (21, "Мавка", CATEGORY_CHARACTER),
    (22, "Воронін", CATEGORY_CHARACTER),
    (23, "Зулус", CATEGORY_CHARACTER),
    (24, "Миклуха", CATEGORY_CHARACTER),
    (25, "Варта", CATEGORY_FACTION),
    (26, "Іскра", CATEGORY_FACTION),
    (27, "Моноліт", CATEGORY_FACTION),
    (28, "НДІЧАЗ", CATEGORY_FACTION),
    (29, "Долг", CATEGORY_FACTION),
    (30, "Воля", CATEGORY_FACTION),
    (31, "Бандити", CATEGORY_FACTION),
    (32, "Полудень", CATEGORY_FACTION),
    (33, "Бункер", CATEGORY_RESEARCH),
    (34, "Х-18", CATEGORY_XLAB),
    (35, "Х-16", CATEGORY_XLAB),
    (36, "Х-3", CATEGORY_XLAB),
    (37, "Х-11", CATEGORY_XLAB),
    (38, "Х-17", CATEGORY_XLAB),
    (39, "Х-5", CATEGORY_XLAB),
    (40, "Дуга", CATEGORY_RESEARCH),
    (41, "Таченко", CATEGORY_CHARACTER),
    (42, "Х-7", CATEGORY_XLAB),
    (43, "Фундамент", CATEGORY_XLAB),
    (44, "Х-19", CATEGORY_XLAB),
    (45, "Альфа", CATEGORY_ARTIFACT),
    (46, "Грозова Ягода", CATEGORY_ARTIFACT),
    (47, "Компас", CATEGORY_ARTIFACT),
    (48, "Дивна Квітка", CATEGORY_ARTIFACT),
)

CARDS: tuple[Card, ...] = tuple(
    Card(card_id, name, category) for card_id, name, category in _CARD_DATA
)

assert len(CARDS) == TOTAL_CARDS

CARD_BY_ID: dict[int, Card] = {c.id: c for c in CARDS}

CARDS_BY_CATEGORY: dict[str, tuple[Card, ...]] = {}
for _cat in CATEGORIES:
    CARDS_BY_CATEGORY[_cat] = tuple(c for c in CARDS if c.category == _cat)


def get_card(card_id: int) -> Card | None:
    return CARD_BY_ID.get(card_id)
