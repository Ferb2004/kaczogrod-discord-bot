import os

import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import reload_failed_embed, reload_succesful_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    def get_all_cogs(self, folder="cogs") -> list[str]:
        """
        Rekurencyjnie przeszukuje folder i zwraca listę ścieżek do cogów w formacie: admin.moderation
        """
        cog_paths = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    full_path = os.path.join(root, file)
                    module_path = full_path.replace("/", ".").replace("\\", ".")[
                        :-3
                    ]  # zamiana ścieżki na moduł
                    module_path = module_path.removeprefix(
                        "cogs."
                    )  # usuwamy "cogs." z początku
                    cog_paths.append(module_path)
        return cog_paths

    # ─────────────────────────────────────────
    # Autocomplete do dynamicznych nazw cogów, z podfolderami
    # ─────────────────────────────────────────
    async def cog_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        all_cogs = self.get_all_cogs()
        filtered = [
            app_commands.Choice(name=cog, value=cog)
            for cog in all_cogs
            if current.lower() in cog.lower()
        ]
        return filtered[:25]

    # ─────────────────────────────────────────
    # Komenda
    # ─────────────────────────────────────────
    @app_commands.command(name="reload", description="Odświeża coga.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(cog="Nazwa coga do przeładowania (np. admin.moderation)")
    @app_commands.autocomplete(cog=cog_autocomplete)
    async def reload(self, interaction: discord.Interaction, cog: str):
        await interaction.response.defer(ephemeral=True)
        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await interaction.followup.send(
                embed=reload_succesful_embed(cog), ephemeral=True
            )
            logger.info(f"Przeładowano cogs.{cog}")
        except commands.ExtensionNotFound:
            await interaction.response.send_message(
                f"❌ Nie znaleziono coga `cogs.{cog}`", ephemeral=True
            )
            logger.warning(f"Nie znaleziono coga cogs.{cog}")
        except Exception as e:
            embed, view = reload_failed_embed(cog, e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            logger.exception(f"Błąd przy przeładowywaniu coga {cog}.")


async def setup(bot):
    await bot.add_cog(Reload(bot))
