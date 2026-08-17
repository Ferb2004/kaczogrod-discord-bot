import re
import traceback
from urllib.parse import urlparse

import aiohttp
import discord
import feedparser
from discord import app_commands
from discord.ext import commands, tasks

from utils.config import (
    add_rss_feed,
    get_guild_config,
    remove_rss_feed,
    update_rss_feed_state,
)
from utils.embeds import error_embed, rss_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


async def fetch_feed(url, session, etag=None, modified=None):
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    if modified:
        headers["If-Modified-Since"] = modified

    try:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            if resp.status == 304:
                return None, etag, modified  # nic nowego

            raw = await resp.read()
            feed = feedparser.parse(raw)

            new_etag = resp.headers.get("ETag")
            new_modified = resp.headers.get("Last-Modified")

            return feed, new_etag, new_modified
    except Exception:
        logger.exception("Nieoczekiwany błąd.")
        return None, etag, modified


def get_favicon_url(site_url, size=64):
    domain = urlparse(site_url).netloc
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"


async def get_og_image(article_url, session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with session.get(
            article_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            html = await resp.text()
        match = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html)
        return match.group(1) if match else None
    except Exception:
        logger.exception("Nieznany")
        return None


def clean_html(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def truncate(text: str, max_length: int = 206, hard_limit: int = 1024) -> str:
    if not text:
        return "Brak opisu"
    if len(text) <= max_length:
        return text

    sentence_ends = [m.end() - 1 for m in re.finditer(r"[.!?]\s", text)]
    if not sentence_ends:
        return text[: max_length - 3] + "..."

    prev_end = max((e for e in sentence_ends if e <= max_length), default=None)
    next_end = min((e for e in sentence_ends if e > max_length), default=None)

    if prev_end is None:
        chosen = next_end
    elif next_end is None:
        chosen = prev_end
    else:
        chosen = (
            next_end if (next_end - max_length) < (max_length - prev_end) else prev_end
        )

    if chosen is None or chosen > hard_limit:
        return text[: hard_limit - 3] + "..."
    return text[: chosen + 1]


def get_entry_id(entry):
    return entry.get("id") or entry.get("link")


async def send_entry(channel, feed, entry, session):
    og_image = await get_og_image(entry.link, session)

    embed, view = rss_embed(
        feed_title=feed.feed.get("title", "Brak nazwy"),
        feed_icon=get_favicon_url(feed.feed.link),
        feed_link=feed.feed.link,
        article_title=entry.get("title", "Brak tytułu"),
        article_link=entry.link,
        article_image_url=og_image,
        description=truncate(clean_html(entry.get("summary", ""))),
        author=entry.get("author", "Nieznany"),
        published_at=entry.get("published_parsed", None),
    )
    await channel.send(embed=embed, view=view)


class RSS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = self.__class__.__name__

        self.group = RSSKomendy(self)
        self.bot.tree.add_command(self.group)

        self.rss_feeds_parse.start()

    async def cog_unload(self):
        self.rss_feeds_parse.cancel()
        self.bot.tree.remove_command(self.group.name)

    @tasks.loop(minutes=5)
    async def rss_feeds_parse(self):
        try:
            async with aiohttp.ClientSession() as session:
                for guild in self.bot.guilds:
                    cfg = get_guild_config(guild.id)
                    feeds = cfg.get("rss")
                    if not feeds:
                        continue

                    for feed_data in feeds:
                        feed_url = feed_data.get("feed_url")
                        channel_id = feed_data.get("channel_id")

                        channel = guild.get_channel(channel_id) if channel_id else None
                        if not channel:
                            logger.error(
                                f"Nie znaleziono kanału dla feeda {feed_url} (guild {guild.id})"
                            )
                            remove_rss_feed(guild.id, feed_url, channel_id)
                            continue

                        feed, new_etag, new_modified = await fetch_feed(
                            feed_url,
                            session,
                            etag=feed_data.get("etag"),
                            modified=feed_data.get("modified"),
                        )

                        # zawsze aktualizuj etag/modified, nawet jeśli 304
                        update_rss_feed_state(
                            guild.id, feed_url, etag=new_etag, modified=new_modified
                        )

                        if feed is None:
                            continue  # 304 (nic nowego) albo błąd pobierania

                        if not feed.entries:
                            continue

                        last_id = feed_data.get("last_entry_id")

                        if last_id is None:
                            # pierwszy raz sprawdzamy ten feed - nie spamuj historią
                            newest_id = get_entry_id(feed.entries[0])
                            update_rss_feed_state(
                                guild.id, feed_url, last_entry_id=newest_id
                            )
                            continue

                        new_entries = []
                        for entry in feed.entries:
                            if get_entry_id(entry) == last_id:
                                break
                            new_entries.append(entry)

                        if not new_entries:
                            continue

                        for entry in reversed(new_entries):
                            await send_entry(channel, feed, entry, session)

                        newest_id = get_entry_id(new_entries[0])
                        update_rss_feed_state(
                            guild.id, feed_url, last_entry_id=newest_id
                        )

        except Exception:
            logger.exception("Nieoczekiwany błąd.")

    @rss_feeds_parse.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

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


@app_commands.guild_only()
class RSSKomendy(app_commands.Group):
    def __init__(self, cog: RSS):
        self.cog = cog
        super().__init__(
            name="rss",
            description="Komendy do zarządzania kanałami RSS/Atom.",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not isinstance(interaction.user, discord.Member)
            or not interaction.user.guild_permissions.administrator
        ):
            raise app_commands.MissingPermissions(["administrator"])
        return True

    async def rss_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []

        guild = interaction.guild
        if guild is None:
            return []

        cfg = get_guild_config(guild.id)
        feeds = cfg.get("rss")
        if not feeds:
            return []

        for feed_data in feeds:
            feed_url = feed_data.get("feed_url")
            channel_id = feed_data.get("channel_id")
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            feed = feedparser.parse(feed_url)
            name = f"{feed.feed.title} / #{channel.name}"
            if current.lower() in name.lower():  # filtrowanie po wpisanym tekście
                choices.append(
                    app_commands.Choice(name=name, value=f"{feed_url}|{channel_id}")
                )

        return choices[:25]

    @app_commands.describe(
        link="Link RSS/Atom feeda.",
        kanal="Kanał na, którym będą wysyłane artykuły z feeda.",
    )
    @app_commands.command(name="dodaj", description="Dodaje kanał RSS/Atom.")
    async def rss_add(
        self, interaction: discord.Interaction, link: str, kanal: discord.TextChannel
    ):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            feed = feedparser.parse(link)

            if not feed.entries or not feed.version:
                await interaction.followup.send(
                    "❌ Podany link nie wygląda na prawidłowy feed RSS/Atom.",
                    ephemeral=True,
                )
                return

            cfg = get_guild_config(interaction.guild.id)
            feeds = cfg.get("rss", [])

            already_exists = any(
                f.get("feed_url") == link and f.get("channel_id") == kanal.id
                for f in feeds
            )
            if already_exists:
                await interaction.followup.send(
                    f"Feed: {feed.feed.title} jest już wysyłany na kanał {kanal.mention}",
                    ephemeral=True,
                )
                return

            add_rss_feed(interaction.guild.id, link, kanal.id)
            await interaction.followup.send(
                f"Feed: {feed.feed.title} będzie wysyłany na kanał {kanal.mention}",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="usun", description="Usuwa kanał RSS/Atom.")
    @app_commands.autocomplete(feed=rss_autocomplete)
    @app_commands.describe(feed="Feed, który będzie usunięty.")
    async def rss_remove(self, interaction: discord.Interaction, feed: str):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            feed_url, channel_id_str = feed.split("|")
            channel_id = int(channel_id_str)
            parsed_feed = feedparser.parse(feed_url)

            remove_rss_feed(interaction.guild.id, feed_url, channel_id)
            await interaction.followup.send(
                f"Feed: {parsed_feed.feed.title} nie będzie już wysyłany.",
                ephemeral=True,
            )

        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(RSS(bot))
