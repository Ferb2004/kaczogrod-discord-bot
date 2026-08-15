import traceback

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import delete_from_guild_config, get_guild_config, update_guild_config
from utils.embeds import config_embed, error_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


class OnJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = self.__class__.__name__

        self.group = OnJoinKomendy(self)
        self.bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.group.name)

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "Nie masz uprawnień do użycia tej komendy.", ephemeral=True
            )
            return

        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        cfg = get_guild_config(member.guild.id)
        role_id = cfg.get("onjoin_role_id")
        role = discord.utils.get(member.guild.roles, id=role_id)
        if role is None:
            logger.error(f"Nie znaleziono roli o ID {role_id}")
            return

        try:
            await member.add_roles(role, reason="Automatyczna rola po dołączeniu")
        except discord.Forbidden as e:
            logger.error(e)
        except discord.HTTPException as e:
            logger.error(e)
        except Exception:
            logger.exception("Nieoczekiwany błąd.")


@app_commands.guild_only()
class OnJoinKomendy(app_commands.Group):
    def __init__(self, cog: OnJoin):
        self.cog = cog
        super().__init__(
            name="onjoin",
            description="Komendy do zarządzania rolą po dołączeniu na serwer.",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not isinstance(interaction.user, discord.Member)
            or not interaction.user.guild_permissions.administrator
        ):
            raise app_commands.MissingPermissions(["administrator"])
        return True

    @app_commands.command(name="dodaj", description="Komenda do dodania roli.")
    @app_commands.describe(
        rola="Rola, którą będę mieli użytkownicy po dołączeniu na serwer."
    )
    async def add(self, interaction: discord.Interaction, rola: discord.Role):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            update_guild_config(
                interaction.guild.id,
                {"onjoin_role_id": rola.id},
            )
            await interaction.followup.send(
                embed=config_embed(
                    "Rola, którą użytkownicy będą mieli po dołączeniu na serwer została ustawiona na:",
                    value=rola.mention,
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="usun", description="Komenda do usunięcia roli.")
    async def remove(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            delete_from_guild_config(
                interaction.guild.id,
                {"onjoin_role_id": None},
            )
            await interaction.followup.send("Rola została usunięta", ephemeral=True)
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(OnJoin(bot))
