import discord
from discord.ext import commands

from logger import logger
import logging as py_logging

from dotenv import load_dotenv

import os
import asyncio

py_logging.getLogger("discord").setLevel(py_logging.INFO)

load_dotenv(".env")
TOKEN: str = os.getenv("TOKEN")


bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())


@bot.event
async def on_ready():
    logger.info("[✅] Bot gotowy!")
    try:
        synced_commands = await bot.tree.sync()
        logger.info(f"[✅] Liczba zsynchronizowanych komend: {len(synced_commands)}")
    except Exception as e:
        logger.error(f"[❌] Problem z synchoronizacją komend: \n {e}")


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())