import discord
from discord.ext import commands
from discord import app_commands

from logger import logger, get_logger, log_cog_loaded
from embeds import github_embed

logger = get_logger(__name__)


class Github(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    @app_commands.command(name="kod", description="Wysyła link do kodu źródłowego.")
    async def github(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        embed , view = github_embed()
        await interaction.followup.send(embed= embed, view= view, ephemeral=True)



async def setup(bot):
    await bot.add_cog(Github(bot))