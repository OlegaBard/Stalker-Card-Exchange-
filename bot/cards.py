from __future__ import annotations

from dataclasses import dataclass

from bot.config import TOTAL_CARDS


@dataclass(frozen=True, slots=True)
class Card:
    id: int
    name: str

    @property
    def code(self) -> str:
        return f"#{self.id:02d}"

    def label(self, owned: bool = False, qty: int = 0) -> str:
        mark = "✅" if owned else "❌"
        suffix = f" x{qty}" if qty > 1 else (" x1" if qty == 1 and owned else "")
        return f"{self.code} {self.name} {mark}{suffix}"


# 48 карток колекції S.T.A.L.K.E.R. 2 (тематика Зони)
CARDS: tuple[Card, ...] = tuple(
    Card(i, name)
    for i, name in enumerate(
        [
            "Скіф",
            "Ріхтер",
            "Коршунов",
            "Болт",
            "Стрілок",
            "Дегтярьов",
            "Хімера",
            "Компас",
            "Сич",
            "Привид",
            "Калина",
            "Сич-2",
            "Аномалія",
            "Виверт",
            "Кровосос",
            "Контролер",
            "Полтергейст",
            "Снорк",
            "Кабан",
            "Псевдособака",
            "Бюрер",
            "Зомбі",
            "Долг",
            "Свобода",
            "Варта",
            "Науковці",
            "Бандити",
            "Чорнобилець",
            "Моноліт",
            "Чисте Небо",
            "Артефакт «Кров каменю»",
            "Артефакт «Медуза»",
            "Артефакт «Батарейка»",
            "Артефакт «Граві»",
            "Викид",
            "КПК",
            "Схрон",
            "Болота",
            "Прип'ять",
            "ЧАЕС",
            "Викид-2",
            "Сталкер-ветеран",
            "Суперечка",
            "Сигнал",
            "Суперзброя",
            "Легенда Зони",
            "Вогнище",
            "Емісар",
        ],
        start=1,
    )
)

assert len(CARDS) == TOTAL_CARDS

CARD_BY_ID: dict[int, Card] = {c.id: c for c in CARDS}


def get_card(card_id: int) -> Card | None:
    return CARD_BY_ID.get(card_id)
