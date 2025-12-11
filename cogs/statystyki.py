import discord
from discord.ext import commands, tasks
from discord import app_commands

from app import SERWER

import os
import yaml

def ensure_yaml_file(filename):
    if not (filename.endswith(".yaml") or filename.endswith(".yml")):
        raise ValueError("Nazwa pliku musi kończyć się na .yaml lub .yml")

    if not os.path.isfile(filename):
        with open(filename, "w", encoding="utf-8") as f:
            yaml.safe_dump({}, f)

class Statystyki(commands.Cog):
    def __init__(self, bot, guild_id: int, online_channel: int, bots_channel: int):
        self.bot = bot
        self.guild_id = guild_id
        self.online_channel_id = online_channel
        self.bots_channel_id = bots_channel
        self.update_online_count.start()

    def cog_unload(self):
        self.update_online_count.cancel()

    @tasks.loop(minutes=1)
    async def update_online_count(self):

        guild = self.bot.get_guild(self.guild_id)

        online_channel = guild.get_channel(self.online_channel_id)
        bots_channel = guild.get_channel(self.bots_channel_id)

        #if guild is None:
        #    print("❌ Nie znaleziono gildii!")
        #    return
        #if online_channel is None:
        #    print("❌ Nie znaleziono kanału online!")
        #    return
        #if bots_channel is None:
        #    print("❌ Nie znaleziono kanału botów!")
        #    return

        # Liczenie członków online
        online_members = sum(1 for m in guild.members
                             if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd))

        # --- LICZENIE BOTÓW ---
        bot_members = sum(1 for m in guild.members if m.bot)



        # --- AKTUALIZACJA NAZW KANAŁÓW ---
        online_name = f"Online: {online_members-bot_members}"
        bots_name = f"Boty: {bot_members}"

        if online_channel.name != online_name:
            await online_channel.edit(name=online_name)

        if bots_channel.name != bots_name:
            await bots_channel.edit(name=bots_name)


    @update_online_count.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()



    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{__name__} działa.")

    @app_commands.command(name="statystyki", description="Pełna kulturka.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def czesc(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"{interaction.user.mention} serwus!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Statystyki(bot, guild_id=, online_channel=, bots_channel=))
    #await bot.add_cog(Statystyki(bot), guild=SERWER)