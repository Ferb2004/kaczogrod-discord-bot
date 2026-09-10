import asyncio
import os
import traceback
from urllib.parse import parse_qs, urlparse

import discord
import spotipy
import yt_dlp
from discord import app_commands
from discord.ext import commands
from spotify_scraper import SpotifyClient
from spotipy.oauth2 import SpotifyClientCredentials
from ytmusicapi import YTMusic

from utils.embeds import error_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)

yt_music = YTMusic()
# TODO szukanie przez ytmusic
# TODO dodać embedy i przyciski
# TODO dodać pauzowanie kolejki kiedy bot zostaje sam i wychodzi dopiero po pewnym czasie
# TODO poprawić to jak bot zachowuje się, kiedy dana piosenka z linku nie jest dostepna w kraju
spotify = spotipy.Spotify(
    language="pl",
    auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    ),
)


ytdl_format_options = {
    "format": "bestaudio/best",
    "noplaylist": False,
    "quiet": True,
    "default_search": "auto",
    "extract_flat": False,
    "source_address": "0.0.0.0",
    "cachedir": False,
}
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)  # type: ignore[arg-type]

flat_ytdl_options = {
    "extract_flat": True,
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "default_search": "auto",
}
flat_ytdl = yt_dlp.YoutubeDL(flat_ytdl_options)  # type: ignore[arg-type]


ffmpeg_options = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -bufsize 512k",
}


def is_playlist_link(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False

    if "list" in parse_qs(parsed.query):
        return True

    return "/sets/" in parsed.path

    return False


def is_spotify_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    return parsed.netloc in ("open.spotify.com", "spotify.com", "www.spotify.com")


async def resolve_spotify(url: str) -> list[str]:
    loop = asyncio.get_event_loop()

    if "/track/" in url:
        track = await loop.run_in_executor(None, lambda: spotify.track(url))
        if track is None:
            raise ValueError("Nie udało się pobrać danych utworu ze Spotify.")
        return [f"{track['artists'][0]['name']} - {track['name']}"]

    if "/album/" in url:
        album = await loop.run_in_executor(None, lambda: spotify.album_tracks(url))
        if album is None:
            raise ValueError("Nie udało się pobrać albumu ze Spotify.")
        return [
            f"{item['artists'][0]['name']} - {item['name']}" for item in album["items"]
        ]

    if "/playlist/" in url:
        return await _resolve_spotify_playlist(url)

    return []


async def _resolve_spotify_playlist(url: str) -> list[str]:
    queries = []

    with SpotifyClient() as client:
        playlist = client.get_playlist(url)
        for track in playlist.tracks:
            if track is None:
                continue  # utwór usunięty/niedostępny regionalnie - Spotify zwraca None
            queries.append(f"{track.track.artists[0].name} - {track.track.name}")

        # def _fetch_next(current):
        #    return spotify.next(current)

        # if results["next"]:
        #    results = await loop.run_in_executor(None, _fetch_next, results)
        # else:
        #    results = None

    return queries


def find_song_video_id(query: str) -> str | None:
    results = yt_music.search(query, filter="songs", limit=1)
    if not results:
        return None
    return results[0]["videoId"]


async def resolve_items(search: str) -> list[str]:
    """Zwraca listę linków/zapytań do dodania do kolejki."""
    if is_spotify_url(search):
        return await resolve_spotify(search)

    if not is_playlist_link(search):
        return [search]

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: flat_ytdl.extract_info(search, download=False)
    )

    entries = data.get("entries", [])
    urls = []
    for entry in entries:
        if entry is None:
            continue
        url = entry.get("url") or entry.get("webpage_url")
        if url:
            urls.append(url)
    return urls


class GuildMusicState:
    """Stan odtwarzacza per serwer."""

    def __init__(self):
        self.queue: list[str] = []
        self.voice_client: discord.VoiceClient | None = None
        self.channel: discord.abc.Messageable | None = None
        self.lock = asyncio.Lock()
        self.current_title: str | None = None


class Muzyka(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.states: dict[int, GuildMusicState] = {}

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        _before: discord.VoiceState,
        _after: discord.VoiceState,
    ):
        if member.bot:
            return

        voice_client = member.guild.voice_client
        if (
            not isinstance(voice_client, discord.VoiceClient)
            or not voice_client.is_connected()
        ):
            return

        channel = voice_client.channel
        human_members = [m for m in channel.members if not m.bot]

        if len(human_members) == 0:
            state = self.get_state(member.guild.id)
            state.queue.clear()
            await voice_client.disconnect(force=False)

    @app_commands.guild_only()
    @app_commands.command(name="play", description="Puszcza muzykę.")
    @app_commands.describe(muzyka="Link lub wyszukanie.")
    async def play(self, interaction: discord.Interaction, muzyka: str):
        if (
            not isinstance(interaction.user, discord.Member)
            or interaction.user.voice is None
        ):
            await interaction.response.send_message(
                "Musisz być na kanale głosowym, żeby użyć tej komendy.", ephemeral=True
            )
            return

        channel = interaction.user.voice.channel
        if channel is None:
            await interaction.response.send_message(
                "Nie udało się ustalić Twojego kanału głosowego. Spróbuj ponownie.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            assert interaction.guild is not None
            state = self.get_state(interaction.guild.id)

            async with state.lock:
                voice_client = interaction.guild.voice_client
                if isinstance(voice_client, discord.VoiceClient):
                    await voice_client.move_to(channel)
                else:
                    await channel.connect()

                new_voice_client = interaction.guild.voice_client
                if not isinstance(new_voice_client, discord.VoiceClient):
                    raise TypeError("Nie udało się połączyć z kanałem głosowym.")
                state.voice_client = new_voice_client

            if isinstance(interaction.channel, discord.abc.Messageable):
                state.channel = interaction.channel

            items = await resolve_items(muzyka)
            state.queue.extend(items)

            if len(items) > 1:
                await interaction.followup.send(
                    f"Dodano **{len(items)}** utworów z playlisty do kolejki."
                )
            else:
                await interaction.followup.send(
                    f"Dodano do kolejki (pozycja {len(state.queue)})."
                )

            async with state.lock:
                voice_client = state.voice_client
                if voice_client is not None and (
                    not voice_client.is_playing() and not voice_client.is_paused()
                ):
                    await self.play_next(interaction.guild.id)

        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view)

    async def play_next(self, guild_id: int):
        state = self.get_state(guild_id)
        if not state.queue:
            return
        if state.voice_client is None:
            logger.warning(f"Brak aktywnego voice_client (guild {guild_id}).")
            return

        search = state.queue.pop(0)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(search, download=False)
        )
        if "entries" in data:
            entries = data["entries"]
            first_entry = next(iter(entries), None)
            if first_entry is None:
                logger.warning(f"Brak dostępnych wpisów w entries (guild {guild_id}).")
                await self.play_next(guild_id)
                return
            data = first_entry

        stream_url = data.get("url")
        if stream_url is None:
            logger.error(
                f"Brak dostępnego URL streamu dla '{search}' (guild {guild_id})."
            )
            if state.channel:
                asyncio.run_coroutine_threadsafe(
                    state.channel.send(f"Nie udało się odtworzyć: {search}"),
                    self.bot.loop,
                )
            await self.play_next(guild_id)
            return

        title = data.get("title", "Nieznany utwór")
        state.current_title = title

        source = discord.FFmpegPCMAudio(
            stream_url,
            before_options=ffmpeg_options["before_options"],
            options=ffmpeg_options["options"],
        )

        def after_playing(error):
            if error:
                logger.error(f"Błąd odtwarzania (guild {guild_id}): {error}")
            fut = self.play_next(guild_id)
            asyncio.run_coroutine_threadsafe(fut, self.bot.loop)

        state.voice_client.play(source, after=after_playing)
        if state.channel:
            asyncio.run_coroutine_threadsafe(
                state.channel.send(f"Teraz gra: **{title}**"), self.bot.loop
            )

    @app_commands.guild_only()
    @app_commands.command(name="skip", description="Skipuje obecny utwór.")
    async def skip(self, interaction: discord.Interaction):
        if (
            not isinstance(interaction.user, discord.Member)
            or interaction.user.voice is None
        ):
            await interaction.response.send_message(
                "Musisz być na kanale głosowym, żeby użyć tej komendy.", ephemeral=True
            )
            return
        else:
            await interaction.response.defer()
        try:
            assert interaction.guild is not None
            state = self.get_state(interaction.guild.id)
            if state.voice_client and (
                state.voice_client.is_playing() or state.voice_client.is_paused()
            ):
                state.voice_client.stop()
            await interaction.followup.send("Pominięto utwór.")
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.guild_only()
    @app_commands.command(name="clearqueue", description="Czyści kolejkę.")
    async def clearqueue(self, interaction: discord.Interaction):
        if (
            not isinstance(interaction.user, discord.Member)
            or interaction.user.voice is None
        ):
            await interaction.response.send_message(
                "Musisz być na kanale głosowym, żeby użyć tej komendy.", ephemeral=True
            )
            return
        else:
            await interaction.response.defer()
        try:
            assert interaction.guild is not None
            state = self.get_state(interaction.guild.id)
            if state.voice_client and (
                state.voice_client.is_playing() or state.voice_client.is_paused()
            ):
                state.queue.clear()
                state.voice_client.stop()
            await interaction.followup.send("Wyczyszczono kolejkę.")
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.guild_only()
    @app_commands.command(
        name="pauza", description="Pauzuje aktualnie odtwarzany utwór."
    )
    async def pause(self, interaction: discord.Interaction):
        if (
            not isinstance(interaction.user, discord.Member)
            or interaction.user.voice is None
        ):
            await interaction.response.send_message(
                "Musisz być na kanale głosowym, żeby użyć tej komendy.", ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            assert interaction.guild is not None
            state = self.get_state(interaction.guild.id)
            if state.voice_client and state.voice_client.is_playing():
                state.voice_client.pause()
                await interaction.followup.send("Wstrzymano.")
            else:
                await interaction.followup.send("Nic teraz nie gra.")
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view)

    @app_commands.guild_only()
    @app_commands.command(name="wznow", description="Wznawia odtwarzanie.")
    async def resume(self, interaction: discord.Interaction):
        if (
            not isinstance(interaction.user, discord.Member)
            or interaction.user.voice is None
        ):
            await interaction.response.send_message(
                "Musisz być na kanale głosowym, żeby użyć tej komendy.", ephemeral=True
            )
            return
        await interaction.response.defer()
        try:
            assert interaction.guild is not None
            state = self.get_state(interaction.guild.id)
            if state.voice_client and state.voice_client.is_paused():
                state.voice_client.resume()
                await interaction.followup.send("Wznowiono.")
            else:
                await interaction.followup.send("Nic nie jest wstrzymane.")
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Muzyka(bot))
