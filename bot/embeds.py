from __future__ import annotations

import discord

from bot.cards import Card, get_card
from bot.config import COLORS, TOTAL_CARDS


def _footer() -> str:
    return "☢️ КПК · Зона · Бартер"


def main_menu_embed() -> discord.Embed:
    embed = discord.Embed(
        title="☢️ ОБМІННИК КАРТОК S.T.A.L.K.E.R. 2",
        description=(
            "Ласкаво просимо до **бартерного вузла Зони**.\n"
            "Усі дії — через кнопки та меню нижче.\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "**ГОЛОВНЕ МЕНЮ**\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=COLORS.swamp_green,
    )
    embed.add_field(
        name="📦 Моя колекція",
        value="Перегляд зібраних, відсутніх і дублів",
        inline=False,
    )
    embed.add_field(
        name="🔁 Обміняти дублікати",
        value="Створити пропозицію обміну",
        inline=False,
    )
    embed.add_field(
        name="🧾 Ринок обміну",
        value="Активні оголошення в каналі ринку",
        inline=False,
    )
    embed.add_field(
        name="🔍 Знайти картку",
        value="Пошук за номером або назвою",
        inline=False,
    )
    embed.add_field(
        name="🏆 Прогрес до суперпушки",
        value="Шлях до повної колекції",
        inline=False,
    )
    embed.add_field(
        name="❓ Правила",
        value="Як працює обмін у Зоні",
        inline=False,
    )
    embed.set_footer(text=_footer())
    return embed


def progress_bar(ratio: float, width: int = 10) -> str:
    filled = round(ratio * width)
    filled = max(0, min(width, filled))
    return "▰" * filled + "▱" * (width - filled)


def collection_summary_embed(
    collected: int,
    duplicates: int,
    missing: int,
) -> discord.Embed:
    ratio = collected / TOTAL_CARDS if TOTAL_CARDS else 0
    embed = discord.Embed(
        title="━━━━━━━━━━━━━━━━━━━━━━\nМОЯ КОЛЕКЦІЯ\n━━━━━━━━━━━━━━━━━━━━━━",
        description=(
            f"🟢 **Зібрано:** {collected} / {TOTAL_CARDS}\n"
            f"🟡 **Дублів:** {duplicates}\n"
            f"🔴 **Не вистачає:** {missing}\n\n"
            f"{progress_bar(ratio)} **{int(ratio * 100)}%**"
        ),
        color=COLORS.background,
    )
    embed.set_footer(text=_footer())
    return embed


def card_list_embed(title: str, lines: list[str], *, empty: str) -> discord.Embed:
    body = "\n".join(lines[:48]) if lines else empty
    if len(lines) > 48:
        body += f"\n… та ще {len(lines) - 48}"
    embed = discord.Embed(title=title, description=body, color=COLORS.metal_gray)
    embed.set_footer(text=_footer())
    return embed


def trade_offer_embed(
    trader_name: str,
    give: Card,
    want: Card,
    *,
    is_new: bool = False,
) -> discord.Embed:
    title = "🔁 НОВА ПРОПОЗИЦІЯ ОБМІНУ" if is_new else "🔁 ПРОПОЗИЦІЯ ОБМІНУ"
    embed = discord.Embed(
        title=title,
        description=(
            f"👤 **{trader_name}**\n"
            f"**Віддає:** {give.code} {give.name}\n"
            f"**Хоче:** {want.code} {want.name}"
        ),
        color=COLORS.radiation_yellow,
    )
    embed.set_footer(text=_footer())
    return embed


def market_trade_embed(
    trader_name: str,
    give: Card,
    want: Card,
    expires_text: str,
) -> discord.Embed:
    embed = discord.Embed(
        title="☢️ БАРТЕР У ЗОНІ",
        description=(
            f"👤 **Trader:** {trader_name}\n"
            f"📤 **Віддає:** {give.code} {give.name}\n"
            f"📥 **Шукає:** {want.code} {want.name}\n\n"
            f"⏳ **Актуально до:** {expires_text}"
        ),
        color=COLORS.swamp_green,
    )
    embed.set_footer(text=_footer())
    return embed


def super_weapon_progress_embed(
    collected: int,
    missing_cards: list[Card],
    status: str,
) -> discord.Embed:
    missing_lines = "\n".join(c.code for c in missing_cards[:12]) or "—"
    if len(missing_cards) > 12:
        missing_lines += f"\n… +{len(missing_cards) - 12}"
    embed = discord.Embed(
        title="🏆 ШЛЯХ ДО СУПЕРПУШКИ",
        description=(
            f"**Зібрано карток:** {collected} / {TOTAL_CARDS}\n\n"
            f"**Не вистачає:**\n{missing_lines}\n\n"
            f"**Статус:**\n{status}"
        ),
        color=COLORS.radiation_yellow,
    )
    embed.set_footer(text=_footer())
    return embed


def full_collection_embed(player_name: str) -> discord.Embed:
    embed = discord.Embed(
        title="🔥 КОМПЛЕКТ ЗІБРАНО",
        description=(
            f"**Гравець:** {player_name}\n\n"
            "**Нагорода:**\n`SUPER WEAPON TOKEN`"
        ),
        color=COLORS.radiation_yellow,
    )
    embed.set_footer(text=_footer())
    return embed


def rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="❓ ПРАВИЛА ОБМІННИКА",
        description=(
            "1. **Колекція** — у «Моя колекція» додавай картки з гри (кнопка «Оновити схрон»).\n"
            "2. **Дублі** — картки з кількістю ≥ 2 можна віддавати в обмін.\n"
            "3. **Обмін** — обери що віддаєш і що хочеш; після підтвердження оголошення з’явиться на ринку.\n"
            "4. **Прийняття** — інший гравець натискає «Прийняти»; бот перевіряє наявність карток і переносить їх.\n"
            "5. **Термін** — оголошення діють **24 години**.\n"
            "6. **Суперпушка** — збери всі 48 карток і отримай **SUPER WEAPON TOKEN**.\n"
            "7. **Чесна гра** — не обманюй щодо наявності карток; за скаргами модератори можуть скасувати угоду."
        ),
        color=COLORS.metal_gray,
    )
    embed.set_footer(text=_footer())
    return embed


def error_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="☢️ ПОМИЛКА",
        description=message,
        color=COLORS.danger_red,
    )


def success_embed(message: str) -> discord.Embed:
    return discord.Embed(
        title="☢️ СИГНАЛ ОТРИМАНО",
        description=message,
        color=COLORS.success,
    )


def card_detail_embed(card: Card, qty: int) -> discord.Embed:
    status = "✅ У схроні" if qty > 0 else "❌ Відсутня"
    dup = f"\n🟡 Дублів: {qty - 1}" if qty > 1 else ""
    embed = discord.Embed(
        title=f"🔍 {card.code} {card.name}",
        description=(
            f"**Категорія:** {card.category}\n"
            f"{status}\n**Кількість:** {qty}{dup}"
        ),
        color=COLORS.background if qty else COLORS.danger_red,
    )
    embed.set_footer(text=_footer())
    return embed


def format_card_line(card_id: int, qty: int) -> str:
    card = get_card(card_id)
    if not card:
        return f"#{card_id:02d} ?"
    owned = qty > 0
    return card.label(owned=owned, qty=qty if owned else 0).replace("  ", " ")
