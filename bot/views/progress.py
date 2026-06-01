from __future__ import annotations

import discord
from discord import ui

from bot.cards import get_card
from bot.config import TOTAL_CARDS
from bot.embeds import (
    error_embed,
    full_collection_embed,
    success_embed,
    super_weapon_progress_embed,
)
from bot.views.constants import PROGRESS


def _status_message(collected: int) -> str:
    if collected == 0:
        return "Новачок у Зоні. Почни полювання."
    if collected < 12:
        return "Сталкер на старті — бігай за артефактами."
    if collected < 24:
        return "Колекція росте. Дублів стає більше."
    if collected < 36:
        return "Досвідчений мисливець карток."
    if collected < TOTAL_CARDS:
        return "Майже легенда, але ще бігай."
    return "Легенда Зони. Комплект зібрано!"


class ProgressView(ui.View):
    def __init__(self, bot: discord.Client, user_id: int) -> None:
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id

    @ui.button(
        label="🎁 Отримати нагороду",
        style=discord.ButtonStyle.success,
        custom_id=f"{PROGRESS}:claim",
    )
    async def claim(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=error_embed("Це не твій прогрес."), ephemeral=True
            )
            return
        db = self.bot.db  # type: ignore[attr-defined]
        settings = self.bot.settings  # type: ignore[attr-defined]
        collected, _, missing = await db.get_collection_stats(self.user_id)
        if missing > 0:
            await interaction.response.send_message(
                embed=error_embed(
                    f"Ще не всі картки ({collected}/{TOTAL_CARDS})."
                ),
                ephemeral=True,
            )
            return
        if await db.is_super_weapon_claimed(self.user_id):
            await interaction.response.send_message(
                embed=error_embed("Нагороду вже отримано."),
                ephemeral=True,
            )
            return

        await db.claim_super_weapon(self.user_id)
        name = interaction.user.display_name
        embed = full_collection_embed(name)

        completed_ch = settings.channel_completed
        if completed_ch:
            ch = self.bot.get_channel(completed_ch)
            if isinstance(ch, discord.TextChannel):
                claim_view = ClaimCelebrationView(self.bot)
                await ch.send(embed=embed, view=claim_view)

        await interaction.response.send_message(
            embed=success_embed(
                "🔥 **SUPER WEAPON TOKEN** видано!\n"
                "Звернися до модераторів сервера для отримання в грі."
            ),
            ephemeral=True,
        )


class ClaimCelebrationView(ui.View):
    def __init__(self, bot: discord.Client) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @ui.button(
        label="🎁 Отримати нагороду",
        style=discord.ButtonStyle.primary,
        custom_id=f"{PROGRESS}:claim_public",
    )
    async def claim_public(
        self, interaction: discord.Interaction, button: ui.Button
    ) -> None:
        await interaction.response.send_message(
            embed=success_embed(
                "Вітаємо! Звернися до адміністрації для SUPER WEAPON TOKEN."
            ),
            ephemeral=True,
        )


async def open_progress(interaction: discord.Interaction, bot: discord.Client) -> None:
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)
    db = bot.db  # type: ignore[attr-defined]
    await db.ensure_user(interaction.user.id, str(interaction.user))
    collected, _, _ = await db.get_collection_stats(interaction.user.id)
    missing_ids = await db.get_missing_ids(interaction.user.id)
    missing_cards = [get_card(i) for i in missing_ids if get_card(i)]
    embed = super_weapon_progress_embed(
        collected,
        missing_cards,  # type: ignore[arg-type]
        _status_message(collected),
    )
    view = ProgressView(bot, interaction.user.id)
    if collected >= TOTAL_CARDS and not await db.is_super_weapon_claimed(
        interaction.user.id
    ):
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        view.children[0].disabled = collected < TOTAL_CARDS  # type: ignore[index]
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
