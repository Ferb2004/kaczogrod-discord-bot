import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import error_embed, ping_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    @app_commands.command(name="ping", description="Pokazuje opóźnienie bota.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            ping = round(self.bot.latency * 1000)  # Mnożywy * 1000, żeby wynik był w ms
            await interaction.followup.send(embed=ping_embed(ping))
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Ping(bot))
