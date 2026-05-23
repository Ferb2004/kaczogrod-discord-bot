import discord
from datetime import datetime

from logger import logger, get_logger


logger = get_logger(__name__)

class ReloadView(discord.ui.View):
    def __init__(self, cog: str):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="Spróbuj ponownie", emoji="🔄")
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Edytuj obecną wiadomość na "ładowanie"
        loading_embed = discord.Embed(
            description="⏳ Przeładowywanie...",
            colour=discord.Color.yellow()
        )
        await interaction.response.edit_message(embed=loading_embed, view=None)

        try:
            await interaction.client.reload_extension(f"cogs.{self.cog}")
            logger.success(f"Przeładowano cogs.{self.cog}")
            await interaction.edit_original_response(
                embed=reload_succesful_embed(self.cog),
                view=None
            )
        except Exception as e:
            logger.error(f"Błąd przy przeładowywaniu coga {self.cog}.", exc_info=True)
            embed, view = reload_failed_embed(self.cog, e)
            await interaction.edit_original_response(embed=embed, view=view)

def error_embed(e: Exception) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=f"```\n{e}\n```",
        colour=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_author(name="❌ Wystąpił problem")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Zgłoś błąd",
        url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new?template=b%C5%82%C4%85d.md"
    ))

    return embed, view


def custom_error_embed(tekst: str) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=tekst,
        colour=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_author(name="❌ Wystąpił problem")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Zgłoś błąd",
        url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new?template=b%C5%82%C4%85d.md"
    ))

    return embed, view


def reload_failed_embed(cog: str, e: Exception) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=f"```\n{e}\n```",
        colour=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.set_author(name="❌ Błąd przy przeładowywaniu coga.")

    return embed, ReloadView(cog)

def reload_succesful_embed(cog: str) -> tuple[discord.Embed]:
    embed = discord.Embed(description=f"```\n{cog}\n```",
                          colour=discord.Color.green(),
                          timestamp=datetime.now())

    embed.set_author(name="✅ Przeładowano!")

    return embed


def config_embed(what_changed: str, value) -> tuple[discord.Embed]:
    embed = discord.Embed(colour=discord.Color.green(),
                          timestamp=datetime.now())
    embed.add_field(name=what_changed,
                    value=value,
                    inline=True)

    embed.set_author(name="✅ Config zaktualizowany")

    return embed

def ping_embed(ping: str) -> tuple[discord.Embed]:
    embed = discord.Embed(
        title=f"{ping} ms",
        color=discord.Color.green(),
        timestamp=datetime.now()
    )
    embed.set_author(name="Ping")

def minecraftserverinfo_success_embed(ip,port,players,motd,version) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        colour=discord.Colour.green(),
    )
    embed.set_author(name=f"Informacje o serwerze Minecraft",
                     icon_url="https://cdn.jsdelivr.net/gh/selfhst/icons/png/minecraft-creeper.png")

    embed.add_field(name="IP",
                    value=ip,
                    inline=False)
    embed.add_field(name="Port",
                    value=port,
                    inline=False)
    embed.add_field(name="Gracze",
                    value=players,
                    inline=False)
    embed.add_field(name="MOTD",
                    value=motd,
                    inline=False)
    embed.add_field(name="Wersja",
                    value=version,
                    inline=False)

    embed.set_thumbnail(url="attachment://favicon.png")

    embed.set_footer(text="Dane dostarczane przez MCStatus.io",
                     icon_url="https://mcstatus.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Ficon.71e79e6a.png&w=32&q=75")

    view = discord.ui.View()

    buttonMCStatus = discord.ui.Button(label="Strona MCStatus.io",
                                       url="https://mcstatus.io/")
    return embed, view

def minecraftserverinfo_failed_embed() -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(description=f"Nie udało się pobrać danych na temat serwera.",
        colour=discord.Colour.red(),
        timestamp=datetime.now()
    )
    embed.set_author(name=f"❌ Wystąpił błąd.",
                     icon_url="https://cdn.jsdelivr.net/gh/selfhst/icons/png/minecraft-creeper.png")
    embed.set_footer(text="Dane dostarczane przez MCStatus.io",
                     icon_url="https://mcstatus.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Ficon.71e79e6a.png&w=32&q=75")

    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Status usług MCStatus.io",
                                       url="https://status.mcstatus.io/"))

    return embed, view

def github_embed() -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        colour=0xffffff
    )
    embed.set_author(name="Github",
                     url="https://github.com/Ferb2004/kaczogrod-discord-bot",
                     icon_url="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png")

    view = discord.ui.View()
    #buttonGithub
    view.add_item(discord.ui.Button(label="Github",
                                     url="https://github.com/Ferb2004/kaczogrod-discord-bot"))
    #buttonIssues
    view.add_item(discord.ui.Button(label="Zgłoś błąd/zaproponuj funkcję",
                                     url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new/choose"))
    #buttonReleases
    view.add_item(discord.ui.Button(label="Lista Zmian",
                                       url="https://github.com/Ferb2004/kaczogrod-discord-bot/releases"))
    return embed, view