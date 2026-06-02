from __future__ import annotations

import discord
from discord import ui

from bot.cards import get_card
from bot.embeds import card_detail_embed, error_embed
from bot.views.constants import SEARCH


class SearchCardView(ui.View):
    PAGE_SIZE = 25

    def __init__(self, bot: discord.Client, user_id: int, page: int) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id
        self.page = page
        start = page * self.PAGE_SIZE + 1
        end = min(start + self.PAGE_SIZE - 1, 48)
        options = []
        for cid in range(start, end + 1):
            card = get_card(cid)
            if card:
                options.append(
                    discord.SelectOption(
                        label=f"{card.code} {card.name}"[:100],
                        value=str(cid),
                    )
                )
        select = ui.Select(
            placeholder="🔍 Обери картку…",
            options=options,
            custom_id=f"{SEARCH}:pick:{page}",
        )

        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != user_id:
                await interaction.response.send_message(
                    embed=error_embed("Чужий пошук."), ephemeral=True
                )
                return
            cid = int(select.values[0])
            qty = await bot.db.get_quantities(user_id)  # type: ignore[attr-defined]
            card = get_card(cid)
            await interaction.response.send_message(
                embed=card_detail_embed(card, qty.get(cid, 0)),
                ephemeral=True,
            )

        select.callback = callback
        self.add_item(select)
        if end < 48:
            nxt = ui.Button(label="→", style=discord.ButtonStyle.secondary)

            async def next_p(inter: discord.Interaction) -> None:
                await inter.response.edit_message(
                    view=SearchCardView(bot, user_id, page + 1),
                )

            nxt.callback = next_p
            self.add_item(nxt)
        if page > 0:
            prv = ui.Button(label="←", style=discord.ButtonStyle.secondary)

            async def prev_p(inter: discord.Interaction) -> None:
                await inter.response.edit_message(
                    view=SearchCardView(bot, user_id, page - 1),
                )

            prv.callback = prev_p
            self.add_item(prv)
