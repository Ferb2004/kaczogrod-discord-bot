import discord
from discord.ext import commands, tasks
from discord import app_commands

from logger import logger, get_logger, log_cog_loaded
import traceback

import os
from dotenv import load_dotenv
from mcstatus import JavaServer

logger = get_logger(__name__)

load_dotenv()
ipSerwera = os.getenv("IP_SERWERA")
portSerwera = os.getenv("PORT_SERWERA", "25565")

server = None

class DiscordStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

        if ipSerwera is None:
            logger.info("Nie wpisano serwera, status nie będzie pokazywany.")
            return

        global server
        server = JavaServer.lookup(f"{ipSerwera}:{portSerwera}")
        self.statusUpdate.start()

    def cog_unload(self):
        self.statusUpdate.cancel()

    async def on_app_command_error(self, interaction, error):
        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

    @tasks.loop(minutes=1)
    async def statusUpdate(self):
        try:
            status = server.status(tries=5)
            gracze = status.players.online
            if gracze == 1:
                status = f"{gracze} gracz na serwerze {ipSerwera}"
            else:
                status = f"{gracze} graczy na serwerze {ipSerwera}"

            await self.bot.change_presence(
                activity=discord.CustomActivity(name=status)
            )
            logger.success("Zaktualizowana status")
        except (TimeoutError, TimeoutError):
            logger.warning("Nie zaktualizowana statusu", exc_info=True)
        except Exception as e:
            logger.error("Nie zaktualizowana status", exc_info=e)

    @statusUpdate.before_loop
    async def before_status_update(self):
        await self.bot.wait_until_ready()

    @statusUpdate.error
    async def update_online_count_error(self, error):
        logger.error(f"Błąd w statusUpdate: {error}", exc_info=error)

async def setup(bot):
    await bot.add_cog(DiscordStatus(bot))