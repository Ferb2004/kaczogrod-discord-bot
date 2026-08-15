import calendar
import logging
from datetime import UTC, datetime

import discord
from discord.ext import commands
from discord.utils import format_dt

logger = logging.getLogger(__name__)


class ReloadView(discord.ui.View):
    def __init__(self, cog: str):
        super().__init__()
        self.cog = cog

    @discord.ui.button(label="Spróbuj ponownie", emoji="🔄")
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        loading_embed = discord.Embed(
            description="⏳ Przeładowywanie...", colour=discord.Color.yellow()
        )
        await interaction.response.edit_message(embed=loading_embed, view=None)

        try:
            if not isinstance(interaction.client, commands.Bot):
                return
            await interaction.client.reload_extension(f"cogs.{self.cog}")
            logger.info(f"Przeładowano cogs.{self.cog}")
            await interaction.edit_original_response(
                embed=reload_succesful_embed(self.cog), view=None
            )
        except Exception as e:
            logger.exception(f"Błąd przy przeładowywaniu coga {self.cog}.")
            embed, view = reload_failed_embed(self.cog, e)
            await interaction.edit_original_response(embed=embed, view=view)


def error_embed(e: Exception) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=f"```\n{e}\n```",
        colour=discord.Color.red(),
        timestamp=datetime.now(UTC),
    )
    embed.set_author(name="❌ Wystąpił problem")

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Zgłoś błąd",
            url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new?template=b%C5%82%C4%85d.md",
        )
    )

    return embed, view


def custom_error_embed(tekst: str) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=tekst, colour=discord.Color.red(), timestamp=datetime.now(UTC)
    )
    embed.set_author(name="❌ Wystąpił problem")

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Zgłoś błąd",
            url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new?template=b%C5%82%C4%85d.md",
        )
    )

    return embed, view


def reload_failed_embed(
    cog: str, e: Exception
) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description=f"```\n{e}\n```",
        colour=discord.Color.red(),
        timestamp=datetime.now(UTC),
    )
    embed.set_author(name="❌ Błąd przy przeładowywaniu coga.")

    return embed, ReloadView(cog)


def reload_succesful_embed(cog: str) -> discord.Embed:
    embed = discord.Embed(
        description=f"```\n{cog}\n```",
        colour=discord.Color.green(),
        timestamp=datetime.now(UTC),
    )

    embed.set_author(name="✅ Przeładowano!")

    return embed


def config_embed(what_changed: str, value) -> discord.Embed:
    embed = discord.Embed(colour=discord.Color.green(), timestamp=datetime.now(UTC))
    embed.add_field(name=what_changed, value=value, inline=True)

    embed.set_author(name="✅ Config zaktualizowany")

    return embed


def ping_embed(ping: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"{ping} ms", color=discord.Color.green(), timestamp=datetime.now(UTC)
    )
    embed.set_author(name="Ping")

    return embed


def minecraftserverinfo_success_embed(
    ip, port, players, motd, version, has_icon: bool = True
) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(colour=discord.Colour.green())
    embed.set_author(
        name="Informacje o serwerze Minecraft",
        icon_url="https://cdn.jsdelivr.net/gh/selfhst/icons/png/minecraft-creeper.png",
    )

    embed.add_field(name="IP", value=ip, inline=False)
    embed.add_field(name="Port", value=port, inline=False)
    embed.add_field(name="Gracze", value=players, inline=False)
    embed.add_field(name="MOTD", value=motd, inline=False)
    embed.add_field(name="Wersja", value=version, inline=False)

    if has_icon:
        embed.set_thumbnail(url="attachment://favicon.png")

    embed.set_footer(
        text="Dane dostarczane przez MCStatus.io",
        icon_url="https://mcstatus.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Ficon.71e79e6a.png&w=32&q=75",
    )

    view = discord.ui.View()

    return embed, view


def minecraftserverinfo_failed_embed() -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        description="Nie udało się pobrać danych na temat serwera.",
        colour=discord.Colour.red(),
        timestamp=datetime.now(UTC),
    )
    embed.set_author(
        name="❌ Wystąpił błąd.",
        icon_url="https://cdn.jsdelivr.net/gh/selfhst/icons/png/minecraft-creeper.png",
    )
    embed.set_footer(
        text="Dane dostarczane przez MCStatus.io",
        icon_url="https://mcstatus.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Ficon.71e79e6a.png&w=32&q=75",
    )

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            label="Status usług MCStatus.io", url="https://status.mcstatus.io/"
        )
    )

    return embed, view


def github_embed(
    name, description, language, stars, latest_version, published_at, issues, last_push
) -> tuple[discord.Embed, discord.ui.View]:
    embed = discord.Embed(
        colour=0xFFFFFF,
        title=name,
        description=description,
        timestamp=datetime.now(UTC),
    )
    embed.set_author(
        name="Github",
        url="https://github.com/Ferb2004/kaczogrod-discord-bot",
        icon_url="https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png",
    )

    embed.add_field(name="Język", value=language, inline=False)
    embed.add_field(name="Gwiazdki", value=stars, inline=False)
    embed.add_field(
        name="Ostatnie wydanie",
        value=f"**{latest_version}** wydane {format_dt(published_at, style='f')} {format_dt(published_at, style='R')}",
        inline=False,
    )
    embed.add_field(name="Otwarte issues", value=issues, inline=False)
    embed.add_field(
        name="Ostatni commit", value=format_dt(last_push, style="R"), inline=False
    )

    view = discord.ui.View()

    view.add_item(
        discord.ui.Button(
            label="GitHub", url="https://github.com/Ferb2004/kaczogrod-discord-bot"
        )
    )

    view.add_item(
        discord.ui.Button(
            label="Zgłoś błąd/zaproponuj funkcję",
            url="https://github.com/Ferb2004/kaczogrod-discord-bot/issues/new/choose",
        )
    )

    view.add_item(
        discord.ui.Button(
            label="Lista Zmian",
            url="https://github.com/Ferb2004/kaczogrod-discord-bot/releases",
        )
    )
    return embed, view


def rss_embed(
    feed_title,
    feed_link,
    feed_icon,
    article_link,
    article_title,
    article_image_url,
    description,
    author,
    published_at,
) -> tuple[discord.Embed, discord.ui.View]:

    embed = discord.Embed(
        colour=0xFF8801,
        timestamp=datetime.now(UTC),
        title=article_title,
        description=description,
    )
    embed.set_author(
        name=feed_title,
        url=feed_link,
        icon_url=feed_icon,
    )

    embed.set_image(url=article_image_url)
    embed.add_field(name="Autor", value=author, inline=False)

    if published_at is not None:
        timestamp = calendar.timegm(published_at)
        embed.add_field(
            name="Data publikacji",
            value=format_dt(datetime.fromtimestamp(timestamp, tz=UTC), style="f"),
            inline=False,
        )

    embed.set_footer(
        text="RSS/Atom",
        icon_url="https://cdn.iconscout.com/icon/free/png-512/free-rss-logo-icon-svg-download-png-2284902.png?f=webp&w=256",
    )

    view = discord.ui.View()

    view.add_item(discord.ui.Button(label="Zobacz stronę główną", url=feed_link))

    view.add_item(discord.ui.Button(label="Czytaj artykuł", url=article_link))

    return embed, view
