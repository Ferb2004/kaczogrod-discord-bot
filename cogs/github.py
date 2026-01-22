import discord
from discord.ext import commands
from discord import app_commands

from logger import logger


class Github(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{__name__} działa.")

    @app_commands.command(name="kod", description="Wysyła link do kodu źródłowego.")
    async def github(self, interaction: discord.Interaction):
        embed = discord.Embed(
            colour=0xffffff
        )
        embed.set_author(name="Github",
                         url="https://github.com/Ferb2004/kaczogrod-discord-bot",
                         icon_url="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png")

        view = discord.ui.View()

        buttonGithub = discord.ui.Button(label="Github",
                                   url="https://github.com/Ferb2004/kaczogrod-discord-bot")
        view.add_item(buttonGithub)

        buttonIssues = discord.ui.Button(label="Zgłoś błąd/zaproponuj funkcję",
                                    url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new/choose")
        view.add_item(buttonIssues)

        buttonReleases = discord.ui.Button(label="Lista Zmian",
                                    url="https://github.com/Ferb2004/kaczogrod-discord-bot/releases")
        view.add_item(buttonReleases)

        await interaction.response.send_message(embed= embed, view= view)



async def setup(bot):
    await bot.add_cog(Github(bot))