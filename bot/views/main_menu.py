from __future__ import annotations

import discord
from discord import ui

from bot.embeds import (
    error_embed,
    main_menu_embed,
    rules_embed,
    success_embed,
)
from bot.views.collection import CollectionView, open_collection
from bot.views.constants import MAIN_MENU
from bot.views.market_browser import open_market_browser
from bot.views.progress import open_progress
from bot.views.search import SearchCardView
from bot.views.trade_wizard import TradeWizardView


class MainMenuView(ui.View):
    """Persistent головне меню."""

    def __init__(self, bot: discord.Client) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    async def _defer_ephemeral(self, interaction: discord.Interaction) -> None:
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    @ui.button(
        label="📦 Моя колекція",
        style=discord.ButtonStyle.primary,
        custom_id=f"{MAIN_MENU}:collection",
        row=0,
    )
    async def collection(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await open_collection(interaction, self.bot)

    @ui.button(
        label="🔁 Обміняти дублікати",
        style=discord.ButtonStyle.success,
        custom_id=f"{MAIN_MENU}:trade",
        row=0,
    )
    async def trade(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await self._defer_ephemeral(interaction)
        db = self.bot.db  # type: ignore[attr-defined]
        await db.ensure_user(interaction.user.id, str(interaction.user))
        dups = await db.get_duplicates(interaction.user.id)
        if not dups:
            await interaction.followup.send(
                embed=error_embed("У тебе немає дублів для обміну."),
                ephemeral=True,
            )
            return
        missing = await db.get_missing_ids(interaction.user.id)
        if not missing:
            await interaction.followup.send(
                embed=error_embed("Колекція повна — немає карток, які шукати."),
                ephemeral=True,
            )
            return
        view = TradeWizardView(self.bot, interaction.user.id)
        await view.send_step(interaction)

    @ui.button(
        label="🧾 Ринок обміну",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{MAIN_MENU}:market",
        row=1,
    )
    async def market(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await open_market_browser(interaction, self.bot)

    @ui.button(
        label="🔍 Знайти картку",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{MAIN_MENU}:search",
        row=1,
    )
    async def search(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await self._defer_ephemeral(interaction)
        db = self.bot.db  # type: ignore[attr-defined]
        await db.ensure_user(interaction.user.id, str(interaction.user))
        view = SearchCardView(self.bot, interaction.user.id, page=0)
        await interaction.followup.send(
            embed=success_embed("Обери картку зі списку:"),
            view=view,
            ephemeral=True,
        )

    @ui.button(
        label="🏆 Прогрес до суперпушки",
        style=discord.ButtonStyle.primary,
        custom_id=f"{MAIN_MENU}:progress",
        row=2,
    )
    async def progress(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await open_progress(interaction, self.bot)

    @ui.button(
        label="❓ Правила",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{MAIN_MENU}:rules",
        row=2,
    )
    async def rules(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await interaction.response.send_message(
            embed=rules_embed(), ephemeral=True
        )

    @ui.button(
        label="☢️ Головне меню",
        style=discord.ButtonStyle.secondary,
        custom_id=f"{MAIN_MENU}:home",
        row=3,
    )
    async def home(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await interaction.response.send_message(
            embed=main_menu_embed(),
            view=MainMenuView(self.bot),
            ephemeral=True,
        )
