from __future__ import annotations

import logging
import time

import discord
from discord import app_commands
from discord.ext import commands

from bot.config import load_settings
from bot.database import Database
from bot.embeds import error_embed, main_menu_embed, rules_embed, success_embed
from bot.views.main_menu import MainMenuView
from bot.views.market import build_market_view
from bot.views.progress import ClaimCelebrationView

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("stalker-cards")


class StalkerCardBot(commands.Bot):
    def __init__(self) -> None:
        settings = load_settings()
        intents = discord.Intents.default()
        intents.message_content = False
        intents.members = True
        super().__init__(command_prefix="\0", intents=intents)
        self.settings = settings
        self.db = Database(settings.database_path)

    async def setup_hook(self) -> None:
        await self.db.connect()
        self.add_view(MainMenuView(self))
        self.add_view(ClaimCelebrationView(self))
        await self._restore_market_views()
        guild_id = self.settings.guild_id
        if guild_id:
            self.tree.copy_global_to(guild=discord.Object(id=guild_id))
            await self.tree.sync(guild=discord.Object(id=guild_id))
        else:
            await self.tree.sync()
        log.info("Slash commands synced")

    async def _restore_market_views(self) -> None:
        rows = await self.db.conn.execute_fetchall(
            """
            SELECT id FROM trades
            WHERE status = 'open' AND expires_at > ? AND message_id IS NOT NULL
            """,
            (time.time(),),
        )
        for row in rows:
            trade_id = int(row[0])
            self.add_view(build_market_view(self, trade_id))
        log.info("Restored %d market views", len(rows))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "?")

    async def close(self) -> None:
        await self.db.close()
        await super().close()

    def is_admin(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator:
            return True
        role_id = self.settings.admin_role_id
        if role_id and any(r.id == role_id for r in member.roles):
            return True
        role_name = self.settings.admin_role_name
        if role_name:
            target = role_name.casefold()
            return any(r.name.casefold() == target for r in member.roles)
        return False


bot = StalkerCardBot()


@bot.tree.command(
    name="stalker_setup",
    description="Опублікувати головне меню обмінника (адмін)",
)
@app_commands.describe(channel="Канал для меню (за замовчуванням — поточний)")
async def stalker_setup(
    interaction: discord.Interaction,
    channel: discord.TextChannel | None = None,
) -> None:
    if not isinstance(interaction.user, discord.Member) or not bot.is_admin(
        interaction.user
    ):
        await interaction.response.send_message(
            embed=error_embed("Лише для адміністраторів."),
            ephemeral=True,
        )
        return
    target = channel or interaction.channel
    if not isinstance(target, discord.TextChannel):
        await interaction.response.send_message(
            embed=error_embed("Потрібен текстовий канал."),
            ephemeral=True,
        )
        return
    await interaction.response.defer(ephemeral=True)
    await target.send(embed=main_menu_embed(), view=MainMenuView(bot))
    await interaction.followup.send(
        embed=success_embed(f"Меню опубліковано в {target.mention}."),
        ephemeral=True,
    )


@bot.tree.command(
    name="stalker_rules",
    description="Опублікувати правила в канал (адмін)",
)
async def stalker_rules(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member) or not bot.is_admin(
        interaction.user
    ):
        await interaction.response.send_message(
            embed=error_embed("Лише для адміністраторів."),
            ephemeral=True,
        )
        return
    ch_id = bot.settings.channel_rules
    channel = (
        bot.get_channel(ch_id)
        if ch_id
        else interaction.channel
    )
    if not isinstance(channel, discord.TextChannel):
        await interaction.response.send_message(
            embed=error_embed("Канал правил не налаштовано."),
            ephemeral=True,
        )
        return
    await channel.send(embed=rules_embed())
    await interaction.response.send_message(
        embed=success_embed("Правила опубліковано."),
        ephemeral=True,
    )


@bot.tree.command(
    name="stalker_grant",
    description="Видати картку гравцю (адмін)",
)
@app_commands.describe(
    member="Гравець",
    card_id="Номер картки 1–48",
    amount="Кількість (може бути від'ємною)",
)
async def stalker_grant(
    interaction: discord.Interaction,
    member: discord.Member,
    card_id: app_commands.Range[int, 1, 48],
    amount: int = 1,
) -> None:
    if not isinstance(interaction.user, discord.Member) or not bot.is_admin(
        interaction.user
    ):
        await interaction.response.send_message(
            embed=error_embed("Лише для адміністраторів."),
            ephemeral=True,
        )
        return
    await bot.db.ensure_user(member.id, str(member))
    new_qty = await bot.db.add_card(member.id, card_id, amount)
    await interaction.response.send_message(
        embed=success_embed(
            f"{member.mention}: картка #{card_id:02d} → **{new_qty}** шт."
        ),
        ephemeral=True,
    )


def run() -> None:
    bot.run(bot.settings.token, log_handler=None)


if __name__ == "__main__":
    run()
