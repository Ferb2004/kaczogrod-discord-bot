import discord
from discord.ext import commands
from discord import app_commands

from logger import logger


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{__name__} działa.")

    @app_commands.command(name="ping", description="Pokazuje opóźnienie bota.")
    async def ping(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title=f"{round(self.bot.latency * 1000)} ms",
            color=discord.Color.green()
        )
        embed.set_author(name="Ping")

        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Ping(bot))