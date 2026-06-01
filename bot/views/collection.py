from __future__ import annotations

import discord
from discord import ui

from bot.cards import CARD_BY_ID, get_card
from bot.embeds import card_list_embed, collection_summary_embed, error_embed, format_card_line
from bot.views.constants import COLLECTION


class CollectionView(ui.View):
    def __init__(self, bot: discord.Client, user_id: int) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id

    async def _qty(self) -> dict[int, int]:
        return await self.bot.db.get_quantities(self.user_id)  # type: ignore[attr-defined]

    @ui.button(label="📘 Показати зібрані", style=discord.ButtonStyle.primary)
    async def show_owned(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твоя колекція."), ephemeral=True
            )
            return
        qty = await self._qty()
        lines = [
            format_card_line(cid, qty[cid])
            for cid in range(1, 49)
            if qty.get(cid, 0) > 0
        ]
        await interaction.response.send_message(
            embed=card_list_embed(
                "📘 Зібрані картки",
                lines,
                empty="Схрон порожній. Додай картки з гри.",
            ),
            ephemeral=True,
        )

    @ui.button(label="📕 Показати відсутні", style=discord.ButtonStyle.secondary)
    async def show_missing(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твоя колекція."), ephemeral=True
            )
            return
        qty = await self._qty()
        lines = [
            f"{get_card(cid).code} {get_card(cid).name} ❌"
            for cid in range(1, 49)
            if qty.get(cid, 0) == 0 and get_card(cid)
        ]
        await interaction.response.send_message(
            embed=card_list_embed(
                "📕 Відсутні картки",
                lines,
                empty="🎉 Усі картки зібрані!",
            ),
            ephemeral=True,
        )

    @ui.button(label="📦 Показати дублі", style=discord.ButtonStyle.success)
    async def show_dups(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твоя колекція."), ephemeral=True
            )
            return
        dups = await self.bot.db.get_duplicates(self.user_id)  # type: ignore[attr-defined]
        lines = []
        for cid, count in dups:
            card = get_card(cid)
            if card:
                lines.append(f"{card.code} {card.name} x{count}")
        await interaction.response.send_message(
            embed=card_list_embed(
                "📦 Дублікати",
                lines,
                empty="Дублів немає.",
            ),
            ephemeral=True,
        )

    @ui.button(label="📥 Оновити схрон (+1)", style=discord.ButtonStyle.primary, row=1)
    async def add_card(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твоя колекція."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Обери картку, яку знайшов у Зоні:",
            view=StashCardSelect(self.bot, self.user_id, page=0, mode="add"),
            ephemeral=True,
        )

    @ui.button(label="📤 Забрати з схрону (-1)", style=discord.ButtonStyle.danger, row=1)
    async def remove_card(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твоя колекція."), ephemeral=True
            )
            return
        await interaction.response.send_message(
            "Обери картку для зменшення кількості:",
            view=StashCardSelect(self.bot, self.user_id, page=0, mode="remove"),
            ephemeral=True,
        )


class StashCardSelect(ui.View):
    PAGE_SIZE = 25

    def __init__(
        self,
        bot: discord.Client,
        user_id: int,
        page: int,
        mode: str,
    ) -> None:
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id
        self.page = page
        self.mode = mode
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
            placeholder="Картка…",
            options=options,
            custom_id=f"{COLLECTION}:stash:{mode}:{page}",
        )

        async def callback(interaction: discord.Interaction) -> None:
            if interaction.user.id != user_id:
                await interaction.response.send_message(
                    embed=error_embed("Чужий схрон."), ephemeral=True
                )
                return
            cid = int(select.values[0])
            db = self.bot.db  # type: ignore[attr-defined]
            if mode == "add":
                await db.add_card(user_id, cid, 1)
            else:
                await db.add_card(user_id, cid, -1)
            card = get_card(cid)
            await interaction.response.edit_message(
                content=f"✅ {card.code} {card.name} оновлено в схроні.",
                view=None,
            )

        select.callback = callback
        self.add_item(select)
        if end < 48:
            next_btn = ui.Button(
                label="Наступна сторінка →",
                style=discord.ButtonStyle.secondary,
            )

            async def next_page(
                inter: discord.Interaction, btn: ui.Button
            ) -> None:
                await inter.response.edit_message(
                    view=StashCardSelect(bot, user_id, page + 1, mode),
                )

            next_btn.callback = next_page
            self.add_item(next_btn)
        if page > 0:
            prev_btn = ui.Button(
                label="← Попередня",
                style=discord.ButtonStyle.secondary,
            )

            async def prev_page(
                inter: discord.Interaction, btn: ui.Button
            ) -> None:
                await inter.response.edit_message(
                    view=StashCardSelect(bot, user_id, page - 1, mode),
                )

            prev_btn.callback = prev_page
            self.add_item(prev_btn)


async def open_collection(interaction: discord.Interaction, bot: discord.Client) -> None:
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)
    db = bot.db  # type: ignore[attr-defined]
    await db.ensure_user(interaction.user.id, str(interaction.user))
    collected, duplicates, missing = await db.get_collection_stats(
        interaction.user.id
    )
    await interaction.followup.send(
        embed=collection_summary_embed(collected, duplicates, missing),
        view=CollectionView(bot, interaction.user.id),
        ephemeral=True,
    )
