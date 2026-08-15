import asyncio
import os
import sys

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger(__name__)


load_dotenv()


def get_token() -> str:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("Brak zmiennej środowiskowej DISCORD_TOKEN!")
    return token


TOKEN = get_token()

# Mimo, że "command_prefix" nie jest nigdzie
# wykorzystywane, to bez tego bot się nie uruchamia.
bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())


def global_exception_handler(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Nieobsłużony wyjątek globalny", exc_info=(exc_type, exc_value, exc_traceback)
    )


sys.excepthook = global_exception_handler


def asyncio_exception_handler(_loop, context):
    exception = context.get("exception")
    message = context.get("message")

    if exception:
        logger.error("Nieobsłużony wyjątek asyncio", exc_info=exception)
    else:
        logger.error(f"Asyncio error: {message}")


@bot.event
async def on_ready():
    logger.info("Bot gotowy!")
    try:
        synced_commands = await bot.tree.sync()
        logger.info(f"Liczba zsynchronizowanych komend: {len(synced_commands)}")
        for cmd in synced_commands:
            logger.info(f"- {cmd.name}")
    except Exception:
        logger.exception("Problem z synchoronizacją komend:")


@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Błąd w komendzie {ctx.command}", exc_info=error)


async def load():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                logger.info(f"cogs.{filename[:-3]} załadowany.")
            except Exception:
                logger.exception(f"Nie udało się załadować coga {filename}:")


async def main():
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(asyncio_exception_handler)

    async with bot:
        await load()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
