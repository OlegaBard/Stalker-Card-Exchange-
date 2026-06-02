from __future__ import annotations

import discord
from discord import ui

from bot.cards import get_card
from bot.embeds import card_art_embed, card_detail_embed, error_embed
from bot.views.constants import COLLECTION


class CardPickerView(ui.View):
    """Меню вибору картки — показує арт у Discord."""

    PAGE_SIZE = 25

    def __init__(
        self,
        bot: discord.Client,
        user_id: int,
        *,
        card_ids: list[int] | None = None,
        page: int = 0,
        show_qty: bool = False,
    ) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.show_qty = show_qty
        all_ids = card_ids if card_ids is not None else list(range(1, 49))
        self.card_ids = sorted(all_ids)
        self.page = page
        start = page * self.PAGE_SIZE
        chunk = self.card_ids[start : start + self.PAGE_SIZE]
        if not chunk and page > 0:
            chunk = self.card_ids[: self.PAGE_SIZE]
            self.page = 0

        options = []
        for cid in chunk:
            card = get_card(cid)
            if not card:
                continue
            desc = card.category[:100]
            options.append(
                discord.SelectOption(
                    label=f"{card.code} {card.name}"[:100],
                    value=str(cid),
                    description=desc,
                )
            )
        if options:
            select = ui.Select(
                placeholder="🖼 Обери номер картки…",
                options=options,
                custom_id=f"{COLLECTION}:pick:{page}:{hash(tuple(self.card_ids)) % 10_000}",
            )
            select.callback = self._on_pick
            self.add_item(select)

        total_pages = max(1, (len(self.card_ids) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
        if self.page + 1 < total_pages:
            nxt = ui.Button(label="→ Арт", style=discord.ButtonStyle.secondary)

            async def next_p(inter: discord.Interaction) -> None:
                await inter.response.edit_message(
                    view=CardPickerView(
                        bot,
                        user_id,
                        card_ids=self.card_ids,
                        page=self.page + 1,
                        show_qty=self.show_qty,
                    ),
                )

            nxt.callback = next_p
            self.add_item(nxt)
        if self.page > 0:
            prv = ui.Button(label="← Арт", style=discord.ButtonStyle.secondary)

            async def prev_p(inter: discord.Interaction) -> None:
                await inter.response.edit_message(
                    view=CardPickerView(
                        bot,
                        user_id,
                        card_ids=self.card_ids,
                        page=self.page - 1,
                        show_qty=self.show_qty,
                    ),
                )

            prv.callback = prev_p
            self.add_item(prv)

    async def _on_pick(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твій перегляд."), ephemeral=True
            )
            return
        select = [c for c in self.children if isinstance(c, ui.Select)][0]
        cid = int(select.values[0])
        card = get_card(cid)
        if not card:
            await interaction.response.send_message(
                embed=error_embed("Картку не знайдено."), ephemeral=True
            )
            return
        extra = ""
        if self.show_qty:
            qty = await self.bot.db.get_quantities(self.user_id)  # type: ignore[attr-defined]
            extra = f"\n\n**У схроні:** {qty.get(cid, 0)} шт."
            await interaction.response.send_message(
                embed=card_detail_embed(card, qty.get(cid, 0)),
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                embed=card_art_embed(card, extra=extra),
                ephemeral=True,
            )
