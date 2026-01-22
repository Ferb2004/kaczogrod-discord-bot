import discord
from discord.ext import commands
from discord import app_commands

from logger import logger

import random

class Moneta(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{__name__} działa.")


    @app_commands.command(name="moneta", description="Rzut monetą.")
    async def moneta(self, interaction: discord.Interaction):
        opcje = ['Orzeł', 'Reszka']
        rzut = random.choice(opcje)
        await interaction.response.send_message(f"{rzut}")



async def setup(bot):
    await bot.add_cog(Moneta(bot))