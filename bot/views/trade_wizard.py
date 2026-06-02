from __future__ import annotations

import time
from datetime import datetime, timezone

import discord
from discord import ui

from bot.cards import get_card
from bot.embeds import (
    card_art_embed,
    error_embed,
    market_trade_embed,
    success_embed,
    trade_offer_embed,
    trade_preview_embed,
)
from bot.views.constants import TRADE
from bot.views.market import build_market_view


class TradeWizardView(ui.View):
    def __init__(self, bot: discord.Client, user_id: int) -> None:
        super().__init__(timeout=600)
        self.bot = bot
        self.user_id = user_id
        self.give_id: int | None = None
        self.want_id: int | None = None

    async def send_step(self, interaction: discord.Interaction) -> None:
        db = self.bot.db  # type: ignore[attr-defined]
        dups = await db.get_duplicates(self.user_id)
        lines = []
        for cid, count in dups:
            card = get_card(cid)
            if card:
                lines.append(f"{card.code} {card.name} x{count}")
        text = "**Твої дублікати:**\n" + ("\n".join(lines) if lines else "—")
        text += "\n\n**Крок 1:** обери картку, яку **віддаєш**."
        self.clear_items()
        self.add_item(self._give_select(dups))
        await interaction.followup.send(text, view=self, ephemeral=True)

    def _give_select(self, dups: list[tuple[int, int]]) -> ui.Select:
        options = []
        for cid, count in dups[:25]:
            card = get_card(cid)
            if card:
                options.append(
                    discord.SelectOption(
                        label=f"{card.code} {card.name} x{count}"[:100],
                        value=str(cid),
                        description="Віддаю",
                    )
                )
        select = ui.Select(
            placeholder="Віддаю…",
            options=options,
            custom_id=f"{TRADE}:give",
        )

        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    embed=error_embed("Не твій обмін."), ephemeral=True
                )
                return
            self.give_id = int(select.values[0])
            db = self.bot.db  # type: ignore[attr-defined]
            missing = await db.get_missing_ids(self.user_id)
            if not missing:
                await interaction.response.send_message(
                    embed=error_embed("Немає відсутніх карток."),
                    ephemeral=True,
                )
                return
            self.clear_items()
            self.add_item(self._want_select(missing))
            give = get_card(self.give_id)
            await interaction.response.edit_message(
                content="**Крок 2:** обери картку, яку **хочеш отримати**.",
                embed=card_art_embed(give, extra="\n📤 **Віддаєш цю картку**"),
                view=self,
            )

        select.callback = callback
        return select

    def _want_select(self, missing: list[int]) -> ui.Select:
        options = []
        for cid in missing[:25]:
            card = get_card(cid)
            if card:
                options.append(
                    discord.SelectOption(
                        label=f"{card.code} {card.name}"[:100],
                        value=str(cid),
                        description="Хочу",
                    )
                )
        select = ui.Select(
            placeholder="Хочу отримати…",
            options=options,
            custom_id=f"{TRADE}:want",
        )

        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message(
                    embed=error_embed("Не твій обмін."), ephemeral=True
                )
                return
            self.want_id = int(select.values[0])
            give = get_card(self.give_id)
            want = get_card(self.want_id)
            self.clear_items()
            confirm = ui.Button(
                label="✅ Створити пропозицію",
                style=discord.ButtonStyle.success,
                custom_id=f"{TRADE}:confirm",
            )

            async def confirm_cb(inter: discord.Interaction) -> None:
                await self._confirm_trade(inter)

            confirm.callback = confirm_cb
            cancel = ui.Button(
                label="Скасувати",
                style=discord.ButtonStyle.secondary,
            )

            async def cancel_cb(inter: discord.Interaction) -> None:
                await inter.response.edit_message(
                    content="Обмін скасовано.",
                    view=None,
                )

            cancel.callback = cancel_cb
            self.add_item(confirm)
            self.add_item(cancel)
            await interaction.response.edit_message(
                content="Після підтвердження бот створить оголошення на ринку.",
                embed=trade_preview_embed(give, want),
                view=self,
            )

        select.callback = callback
        return select

    async def _confirm_trade(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Не твій обмін."), ephemeral=True
            )
            return
        if self.give_id is None or self.want_id is None:
            await interaction.response.send_message(
                embed=error_embed("Обери обидві картки."), ephemeral=True
            )
            return

        db = self.bot.db  # type: ignore[attr-defined]
        settings = self.bot.settings  # type: ignore[attr-defined]

        if not await db.has_card(self.user_id, self.give_id, 2):
            await interaction.response.send_message(
                embed=error_embed("Потрібен дубль (мінімум 2 однакові картки)."),
                ephemeral=True,
            )
            return

        open_count = await db.count_open_trades(self.user_id)
        if open_count >= 5:
            await interaction.response.send_message(
                embed=error_embed("Максимум 5 активних оголошень."),
                ephemeral=True,
            )
            return

        channel_id = settings.channel_trade_market
        if not channel_id:
            await interaction.response.send_message(
                embed=error_embed(
                    "Канал ринку не налаштовано (CHANNEL_CARD_TRADE_MARKET)."
                ),
                ephemeral=True,
            )
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                embed=error_embed("Канал ринку недоступний."),
                ephemeral=True,
            )
            return

        give = get_card(self.give_id)
        want = get_card(self.want_id)
        if not give or not want:
            await interaction.response.send_message(
                embed=error_embed("Невідома картка."), ephemeral=True
            )
            return

        trade_id = await db.create_trade(
            self.user_id, self.give_id, self.want_id
        )
        expires = datetime.fromtimestamp(
            time.time() + 24 * 3600, tz=timezone.utc
        ).strftime("%d.%m.%Y %H:%M UTC")
        member = interaction.user
        name = member.display_name

        market_embed = market_trade_embed(name, give, want, "24 години")
        view = build_market_view(self.bot, trade_id)
        self.bot.add_view(view)  # persistent
        msg = await channel.send(embed=market_embed, view=view)
        await db.update_trade_message(trade_id, msg.id, channel.id)

        preview = trade_offer_embed(name, give, want, is_new=True)
        await interaction.response.edit_message(
            content=None,
            embed=preview,
            view=None,
        )
        await interaction.followup.send(
            embed=success_embed(
                f"Оголошення опубліковано в {channel.mention}.\n"
                f"⏳ Актуально до: {expires}"
            ),
            ephemeral=True,
        )

        collections_ch = settings.channel_collections
        if collections_ch:
            ch = self.bot.get_channel(collections_ch)
            if isinstance(ch, discord.TextChannel):
                await ch.send(
                    embed=trade_offer_embed(name, give, want, is_new=True),
                    view=view,
                )
