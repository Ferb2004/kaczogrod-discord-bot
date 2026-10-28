import os
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands

from utils.embeds import error_embed, ggdeals_embed
from utils.logger import get_logger, log_cog_loaded
from utils.requests import Request, get_all_requests, get_request

logger = get_logger(__name__)


GGDEALS_KEY = os.getenv("GGDEALS_KEY")


class GGDeals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session: aiohttp.ClientSession | None = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10),)

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

    async def steamid_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []
        if not current:
            return []

        url = "https://store.steampowered.com/api/storesearch/"
        params = {"term": current, "cc": "pl", "l": "polish"}


        data = await get_request(self.session, Request(url, params))

        for item in data.json.get("items", []):
            choices.append(
                app_commands.Choice(name=item["name"], value=item['id'])
            )

        return choices[:25]

    @app_commands.command(name="ggdeals", description="Informacje o cenie gry.")
    @app_commands.autocomplete(gra=steamid_autocomplete)
    @app_commands.describe(gra="Gra musi być na Steamie.")
    async def ggdeals(self, interaction: discord.Interaction, gra: int):
        await interaction.response.defer()
        try:
            requests_list = [
                Request(
                    "https://api.gg.deals/v1/prices/by-steam-app-id/",
                    {"ids": str(gra), "key": GGDEALS_KEY, "region": "pl"},
                ),
                Request(
                    "https://store.steampowered.com/api/appdetails",
                    {"appids": str(gra), "cc": "pl", "l": "polish"},
                ),
            ]

            api_data, steam_data = await get_all_requests(self.session, requests_list)

            game_data = api_data.json["data"][f"{gra}"]
            game_price_data = game_data["prices"]

            image_data = steam_data.json[str(gra)]
            
            if image_data["success"]:
                image_url = image_data["data"]["header_image"]


            if len(image_data["data"]["short_description"]) > 300:
                description = image_data["data"]["short_description"][:297] + "..."
            else:
                description = image_data["data"]["short_description"]


            embed, view = ggdeals_embed(name=game_data["title"],
                                        ggdeals_url=game_data["url"],
                                        steam_url=f"https://store.steampowered.com/app/{gra}",
                                        description=description,
                                        price_current_official=game_price_data["currentRetail"],
                                        price_current_keyshop=game_price_data["currentKeyshops"],
                                        price_historicallow_official=game_price_data["historicalRetail"],
                                        price_historicallow_keyshop=game_price_data["historicalKeyshops"],
                                        currency=game_price_data["currency"],
                                        image_url=image_url
                                        )
            
            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(GGDeals(bot))
