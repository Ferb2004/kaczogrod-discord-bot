import discord
from discord.ext import commands, tasks
from discord import app_commands

from logger import logger, get_logger, log_cog_loaded
import traceback

import os
from dotenv import load_dotenv
from mcstatus import JavaServer
import aiohttp

logger = get_logger(__name__)

load_dotenv()
ipSerwera = os.getenv("IP_SERWERA")
portSerwera = os.getenv("PORT_SERWERA", "25565")
version = os.getenv("IMAGE_DIGEST")

server = None

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latest_version = None

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

        if ipSerwera is None:
            logger.info("Nie wpisano adresu serwera minecraft.")
        else:
            global server
            server = JavaServer.lookup(f"{ipSerwera}:{portSerwera}")
        self.get_latest_version.start()
        self.status_update.start()

    def cog_unload(self):
        self.get_latest_version.cancel()
        self.status_update.cancel()

    async def on_app_command_error(self, interaction, error):
        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

    @tasks.loop(minutes=30)
    async def get_latest_version(self):
        url = "https://api.github.com/repos/Ferb2004/kaczogrod-discord-bot/releases/latest"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={"Accept": "application/vnd.github+json"}) as r:
                if r.status == 200:
                    data = await r.json()
                    self.latest_version = data["tag_name"]


    @tasks.loop(minutes=5)
    async def status_update(self):
        gracze: int | None = None
        logger.info(f"version={version}, latest={self.latest_version}")
        if server is not None:
            try:
                mc_status = server.status(tries=5)
                gracze = mc_status.players.online
            except (TimeoutError, OSError):
                gracze = None

        if gracze == 0 or gracze is None:
            if version is not None:
                if version == self.latest_version:
                    status = f"✅{version}"
                else:
                    status = f"ℹ️{version} | Dostępna aktualizacja."
            else:
                status = f"🔨Własna kompilacja"
        else:
            status = f"{gracze} gracz{'y' if gracze != 1 else ''} na serwerze {ipSerwera}"


        await self.bot.change_presence(
            activity=discord.CustomActivity(name=status)
        )
        logger.success(f"Zaktualizowana status na {status}")


    @status_update.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

    @status_update.error
    async def update_online_count_error(self, error):
        logger.error(f"Błąd w statusUpdate: {error}", exc_info=error)

async def setup(bot):
    await bot.add_cog(Status(bot))