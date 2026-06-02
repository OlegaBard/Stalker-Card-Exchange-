from __future__ import annotations

import time

import discord
from discord import ui

from bot.cards import get_card
from bot.embeds import error_embed, success_embed
from bot.views.constants import MARKET


def build_market_view(bot: discord.Client, trade_id: int) -> MarketTradeView:
    """View з унікальними custom_id для persistent-кнопок."""
    view = MarketTradeView(bot)
    view.trade_id = trade_id

    accept = ui.Button(
        label="Прийняти",
        style=discord.ButtonStyle.success,
        custom_id=f"{MARKET}:accept:{trade_id}",
    )
    accept.callback = lambda i: _handle_accept(i, bot, trade_id)
    view.add_item(accept)

    profile = ui.Button(
        label="Профіль",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{MARKET}:profile:{trade_id}",
    )
    profile.callback = lambda i: _handle_profile(i, bot, trade_id)
    view.add_item(profile)

    report = ui.Button(
        label="Скарга",
        style=discord.ButtonStyle.danger,
        custom_id=f"{MARKET}:report:{trade_id}",
    )
    report.callback = lambda i: _handle_report(i, bot, trade_id)
    view.add_item(report)

    return view


class MarketTradeView(ui.View):
    """Базовий persistent view; кнопки додаються через build_market_view."""

    def __init__(self, bot: discord.Client) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.trade_id: int = 0


async def _handle_accept(
    interaction: discord.Interaction, bot: discord.Client, trade_id: int
) -> None:
    await interaction.response.defer(ephemeral=True)
    db = bot.db  # type: ignore[attr-defined]
    trade = await db.get_trade(trade_id)
    if not trade or trade["status"] != "open":
        await interaction.followup.send(
            embed=error_embed("Оголошення недоступне або вже закрито."),
            ephemeral=True,
        )
        return
    if time.time() > trade["expires_at"]:
        await db.close_trade(trade_id, "expired")
        await interaction.followup.send(
            embed=error_embed("Термін оголошення минув."),
            ephemeral=True,
        )
        return

    offerer_id = int(trade["offerer_id"])
    acceptor_id = interaction.user.id
    if acceptor_id == offerer_id:
        await interaction.followup.send(
            embed=error_embed("Не можна прийняти власне оголошення."),
            ephemeral=True,
        )
        return

    give_id = int(trade["give_card_id"])
    want_id = int(trade["want_card_id"])

    await db.ensure_user(acceptor_id, str(interaction.user))

    if not await db.has_card(offerer_id, give_id, 1):
        await interaction.followup.send(
            embed=error_embed("У продавця більше немає цієї картки."),
            ephemeral=True,
        )
        return
    if not await db.has_card(acceptor_id, want_id, 1):
        want_card = get_card(want_id)
        await interaction.followup.send(
            embed=error_embed(
                f"Тобі потрібна картка {want_card.code} {want_card.name} для обміну."
            ),
            ephemeral=True,
        )
        return

    try:
        await db.execute_swap(offerer_id, acceptor_id, give_id, want_id)
    except ValueError:
        await interaction.followup.send(
            embed=error_embed("Обмін не вдався — перевір кількість карток."),
            ephemeral=True,
        )
        return

    await db.close_trade(trade_id, "completed")
    give = get_card(give_id)
    want = get_card(want_id)
    from bot.embeds import trade_preview_embed

    done = trade_preview_embed(give, want)
    done.title = "✅ Обмін завершено"
    done.description = (
        f"📥 **Отримав:** {give.code} {give.name}\n"
        f"📤 **Віддав:** {want.code} {want.name}"
    )
    await interaction.followup.send(embed=done, ephemeral=True)

    if interaction.message and interaction.message.embeds:
        closed = interaction.message.embeds[0].copy()
        closed.title = "✅ УГОДУ УКЛАДЕНО"
        closed.color = discord.Color.dark_green()
        await interaction.message.edit(embed=closed, view=None)

    offerer = bot.get_user(offerer_id)
    if offerer:
        try:
            await offerer.send(
                embed=success_embed(
                    f"{interaction.user.display_name} прийняв твій обмін:\n"
                    f"{give.code} ↔ {want.code}"
                )
            )
        except discord.HTTPException:
            pass


async def _handle_profile(
    interaction: discord.Interaction, bot: discord.Client, trade_id: int
) -> None:
    db = bot.db  # type: ignore[attr-defined]
    trade = await db.get_trade(trade_id)
    if not trade:
        await interaction.response.send_message(
            embed=error_embed("Оголошення не знайдено."), ephemeral=True
        )
        return
    user = bot.get_user(int(trade["offerer_id"]))
    if user:
        await interaction.response.send_message(
            f"👤 Trader: {user.mention}",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            embed=error_embed("Гравця не знайдено."),
            ephemeral=True,
        )


async def _handle_report(
    interaction: discord.Interaction, bot: discord.Client, trade_id: int
) -> None:
    await interaction.response.send_message(
        embed=success_embed(
            "Скаргу зафіксовано. Модератори переглянуть оголошення.\n"
            f"ID угоди: `{trade_id}`"
        ),
        ephemeral=True,
    )
