from datetime import UTC, datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import format_dt
from github import Github
from github.GithubException import RateLimitExceededException

from utils.embeds import error_embed, github_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


repo_name: str = "ferb2004/kaczogrod-discord-bot"

g = Github(lazy=True)
repo = g.get_repo(repo_name)


class GithubRepo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

    @app_commands.command(name="github", description="Wysyła link do kodu źródłowego.")
    async def github(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            embed, view = github_embed(
                name=repo.name,
                description=repo.description,
                language=repo.language,
                stars=repo.stargazers_count,
                latest_version=next(
                    r for r in repo.get_releases() if not r.draft
                ).tag_name,
                published_at=repo.get_latest_release().published_at,
                issues=repo.open_issues_count,
                last_push=repo.pushed_at,
            )

            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except RateLimitExceededException as e:
            reset_timestamp = (e.headers or {}).get("x-ratelimit-reset")
            if reset_timestamp:
                reset_time = datetime.fromtimestamp(int(reset_timestamp), tz=UTC)
                await interaction.followup.send(
                    f"Został osiągnięty limit requestów do GitHuba. Spróbuj ponownie za: "
                    f"{format_dt(reset_time, style='R')}.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "Został osiągnięty limit requestów do GitHuba. Spróbuj ponownie za jakiś czas.",
                    ephemeral=True,
                )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GithubRepo(bot))
