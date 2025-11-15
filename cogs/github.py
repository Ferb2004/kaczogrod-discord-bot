import discord
from discord.ext import commands
from discord import app_commands


class Github(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} działa.")

    @app_commands.command(name="github", description="Link do Githuba.")
    async def github(self, interaction: discord.Interaction):
        embed = discord.Embed(
            colour=0xffffff
        )
        embed.set_author(name="Github",
                         url="https://github.com/Ferb2004/kaczogrod-discord-bot",
                         icon_url="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png")

        await interaction.response.send_message(embed=embed)



async def setup(bot):
    await bot.add_cog(Github(bot))