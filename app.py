import discord
from discord.ext import commands
from dotenv import load_dotenv

import os
import asyncio


load_dotenv(".env")
TOKEN: str = os.getenv("TOKEN")
SERWER: str = os.getenv("SERWER")


bot = commands.Bot(command_prefix="$", intents=discord.Intents.all())


@bot.event
async def on_ready():
    print("Bot gotowy!")
    try:
        synced_commands = await bot.tree.sync()
        print(f"Liczba zsynchronizowanych komend: {len(synced_commands)}")
    except Exception as e:
        print("Problem z synchoronizacją komend:", e)


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