import base64
import io

import discord
from discord import app_commands
from discord.ext import commands
from mcstatus import JavaServer

from utils.embeds import (
    error_embed,
    minecraftserverinfo_failed_embed,
    minecraftserverinfo_success_embed,
)
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


class Minecraft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    @app_commands.command(
        name="minecraft", description="Wyszukuje dane o serwerze minecraft."
    )
    @app_commands.describe(
        ip_serwera="Ip serwera minecraft.", port_serwera="Porta serwera minecraft."
    )
    async def minecraft(
        self,
        interaction: discord.Interaction,
        ip_serwera: str,
        port_serwera: int | None = 25565,
    ):
        await interaction.response.defer(ephemeral=True)
        try:
            server = JavaServer.lookup(f"{ip_serwera}:{port_serwera}")
            status = server.status(tries=10)

            server_players = f"{status.players.online}/{status.players.max}"
            server_version = status.version.name
            server_motd = status.motd.to_plain()

            if status.icon is None:
                favicon = None
            else:
                b64_data = status.icon.split(",", 1)[
                    1
                ]  # odcinamy "data:image/png;base64,"
                image_bytes = base64.b64decode(b64_data)
                favicon = discord.File(io.BytesIO(image_bytes), filename="favicon.png")

            embed, view = minecraftserverinfo_success_embed(
                ip_serwera,
                port_serwera,
                server_players,
                server_motd,
                server_version,
                has_icon=favicon is not None,
            )

            if favicon is not None:
                await interaction.followup.send(
                    embed=embed, file=favicon, view=view, ephemeral=True
                )
            else:
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)

        except TimeoutError, ConnectionError:
            logger.warning("Nie udało się pobrać informacji o serwerze.", exc_info=True)
            embed, view = minecraftserverinfo_failed_embed()
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Minecraft(bot))
