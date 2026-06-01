from __future__ import annotations

import discord

from bot.embeds import error_embed, success_embed


async def open_market_browser(
    interaction: discord.Interaction, bot: discord.Client
) -> None:
    settings = bot.settings  # type: ignore[attr-defined]
    channel_id = settings.channel_trade_market
    if not channel_id:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                embed=error_embed("Канал ринку не налаштовано."),
                ephemeral=True,
            )
        return
    channel = bot.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        if not interaction.response.is_done():
            await interaction.response.send_message(
                embed=error_embed("Канал ринку недоступний."),
                ephemeral=True,
            )
        return
    text = (
        f"🧾 **Ринок обміну:** {channel.mention}\n\n"
        "Усі активні бартери публікуються там.\n"
        "Натисни **Прийняти** під оголошенням, якщо маєш потрібну картку."
    )
    if not interaction.response.is_done():
        await interaction.response.send_message(
            embed=success_embed(text),
            ephemeral=True,
        )
    else:
        await interaction.followup.send(
            embed=success_embed(text),
            ephemeral=True,
        )
