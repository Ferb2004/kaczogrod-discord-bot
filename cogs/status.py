import os

import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from mcstatus import JavaServer

from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)

load_dotenv()

ipSerwera = os.getenv("IP_SERWERA")
portSerwera = os.getenv("PORT_SERWERA", "25565")
version = os.getenv("IMAGE_DIGEST")


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_status = None
        self.latest_version = None
        self.gracze: int | None = None
        self.server: JavaServer | None = None

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

        if ipSerwera is None:
            logger.info("Nie wpisano adresu serwera minecraft.")
        else:
            self.server = JavaServer.lookup(f"{ipSerwera}:{portSerwera}")
        await self.get_latest_version()

        if ipSerwera is None and (version is None or version == "unknown"):
            await self.bot.change_presence(
                activity=discord.CustomActivity(name="🔨 Własna kompilacja")
            )
            logger.info("Status ustawiony na: '🔨 Własna kompilacja'")
        elif ipSerwera is None and version:
            self.get_latest_version.start()
            self.status_update.start()
        elif ipSerwera and (version is None or version == "unknown"):
            self.get_players.start()
            self.status_update.start()

    async def cog_unload(self):
        self.get_latest_version.cancel()
        self.status_update.cancel()
        self.get_players.cancel()

    @tasks.loop(minutes=30)
    async def get_latest_version(self):
        url = "https://api.github.com/repos/Ferb2004/kaczogrod-discord-bot/releases/latest"
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers={"Accept": "application/vnd.github+json"}) as r,
        ):
            if r.status == 200:
                data = await r.json()
                self.latest_version = data["tag_name"]
                logger.debug(f"Wykryta wersja: {self.latest_version}")

    @tasks.loop(minutes=1)
    async def get_players(self):
        self.gracze: int | None = None
        if self.server is not None:
            try:
                mc_status = self.server.status(tries=5)
                self.gracze = mc_status.players.online
                logger.debug(f"Pobrano ilość graczy: {self.gracze}")
            except TimeoutError, OSError:
                self.gracze = None
                logger.debug("Nie udało się pobrać graczy")

    @tasks.loop(minutes=5)
    async def status_update(self):
        if self.gracze == 0 or self.gracze is None:
            if version == self.latest_version:
                status = f"{version}"
            else:
                status = f"ℹ️ Dostępna aktualizacja | Obecja wersja: {version}."
        else:
            status = f"{self.gracze} gracz{'y' if self.gracze != 1 else ''} na serwerze {ipSerwera}"

        if self.current_status != status or self.current_status is None:
            try:
                await self.bot.change_presence(
                    activity=discord.CustomActivity(name=status)
                )
                self.current_status = status
                logger.debug(f"Zaktualizowana status na: '{status}'")
            except Exception:
                logger.exception("Wystąpił problem ze zmianią statusu.")

    @status_update.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

    @status_update.error
    async def update_online_count_error(self, error):
        logger.error(f"Błąd w statusUpdate: {error}", exc_info=error)


async def setup(bot):
    await bot.add_cog(Status(bot))
