import time
import traceback
from datetime import UTC, datetime

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import error_embed, github_embed, github_ratelimit_embed
from utils.logger import get_logger, log_cog_loaded
from utils.requests import Request, get_all_requests

logger = get_logger(__name__)


repo_url = "https://api.github.com/repos/ferb2004/kaczogrod-discord-bot"
releases_url = f"{repo_url}/releases"

headers = {"Accept": "application/vnd.github+json"}

class RateLimitExceededException(Exception):
    def __init__(self, reset_timestamp: int | None = None) -> None:
        super().__init__("GitHub rate limit exceeded")
        self.reset_timestamp = reset_timestamp


class GithubRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),
                                             headers={"Accept": "application/vnd.github+json"},)

    async def cog_unload(self):
        await self.session.close()

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

    @app_commands.command(name="github", description="Wysyła link do repozytorium z kodem źródłym.")
    async def github(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            requests_list = [
                Request(
                    repo_url,
                ),
                Request(
                    releases_url,
                ),
            ]
            
            repo_data, releases_data = await get_all_requests(self.session, requests_list)

            for resp in (repo_data, releases_data):
                if (
                    resp.status_code in (403, 429)
                    and resp.headers.get("x-ratelimit-remaining") == "0"
                ):
                    reset = resp.headers.get("x-ratelimit-reset")
                    retry_after = resp.headers.get("retry-after")

                    if reset:
                        reset_timestamp = int(reset)
                    elif retry_after:
                        reset_timestamp = int(time.time()) + int(retry_after)
                    else:
                        reset_timestamp = None

                    raise RateLimitExceededException(reset_timestamp)

            
            latest_release = next((r for r in releases_data.json if not r["draft"]), None)
            
            embed, view = github_embed(
                name=repo_data.json["name"],
                description=repo_data.json["description"],
                language=repo_data.json["language"],
                stars=repo_data.json["stargazers_count"],
                latest_version=latest_release["tag_name"],
                published_at=datetime.fromisoformat(latest_release["published_at"]),
                issues=repo_data.json["open_issues_count"],
                last_push=datetime.fromisoformat(repo_data.json["pushed_at"]),
            )

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except RateLimitExceededException as e:
            logger.exception("Rate limit exceeded.")
            reset_time = (
                datetime.fromtimestamp(e.reset_timestamp, tz=UTC)
                if e.reset_timestamp
                else None
            )
            embed, view = github_ratelimit_embed(timestamp=reset_time)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GithubRepo(bot))
