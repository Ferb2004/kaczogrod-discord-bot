import discord
from discord.ext import commands, tasks
from discord import app_commands, TextChannel

from logger import logger
import traceback

from config import UpdateGuildConfig, GetGuildConfig


#TODO zrobić osobne funkcje dla liczenia online i botów, żeby mogły działać nie zależnie od siebie
#TODO uporządkować kod

class Statystyki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = self.__class__.__name__

        self.group = StatystykiKomendy(self)
        self.bot.tree.add_command(self.group)
        self.update_online_count.start()

    def cog_unload(self):
        self.update_online_count.cancel()
        self.bot.tree.remove_command(
            self.group.name,
            type=self.group.type
        )

    #def loading_data(self):
    #    print(f"[{__name__}] Cog Statystyki został załadowany lub zreloadowany!")

    @tasks.loop(minutes=1)
    async def update_online_count(self):
        try:
            for guild in self.bot.guilds:
                cfg = GetGuildConfig(guild.id)

                stat = cfg.get("statystyki")
                if not stat:
                    continue

                online_id = stat.get("kanal_online")
                bots_id = stat.get("kanal_boty")

                if not online_id or not bots_id:
                    continue

                online_channel = guild.get_channel(online_id)
                bots_channel = guild.get_channel(bots_id)

                if not online_channel or not bots_channel:
                    continue

    #        if guild is None:
    #            print("❌ Nie znaleziono serwera!")
    #            return
    #        if online_channel is None:
    #            print("❌ Nie znaleziono kanału do liczenia członków online!")
    #            pass
    #        if bots_channel is None:
    #            print("❌ Nie znaleziono kanału do liczenia botów!")
    #            pass

            # Liczenie członków online
                online_members = sum(1 for m in guild.members
                                 if m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd))

            # Liczenie botów
                bot_members = sum(1 for m in guild.members if m.bot)



            # --- AKTUALIZACJA NAZW KANAŁÓW ---
                online_name = f"Online: {online_members-bot_members}"
                bots_name = f"Boty: {bot_members}"

                if online_channel.name != online_name:
                    await online_channel.edit(name=online_name)

                if bots_channel.name != bots_name:
                    await bots_channel.edit(name=bots_name)
        except Exception as e:
            logger.error(f"Błąd w tasku update_online_count\n{e}")


    @update_online_count.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

#    @update_online_count.error
#    async def update_online_count_error(self, error):
#        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
#
#        self.bot.cog_status[self.name] = {
#            "ok": False,
#            "error": str(error),
#            "traceback": tb
#        }
#
#        logger.error(f"{self.name} {self.bot.cog_status}")


    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{__name__} działa.")


class StatystykiKomendy(app_commands.Group):
    def __init__(self, cog: "Statystyki"):
        self.cog = cog
        super().__init__(
            name="statystyki",
            description="Komendy do ustawienia kanałów ze statystykami."
        )

    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True

#TODO komendy proponują zrobienie nowego kanału
#TODO kategoria i tworzenie jej

    @app_commands.command(name="online", description="Ustawia kanał do liczenia członków online.")
    @app_commands.describe(kanal= 'Kanał który będzie wyświetlał ilość użytkowników online.')
    async def online(self, interaction: discord.Interaction, kanal: discord.VoiceChannel):

        await interaction.response.defer(ephemeral=True)
        UpdateGuildConfig(
            interaction.guild.id,
            {"statystyki": {"kanal_online": kanal.id}},
            user_id=f"{interaction.user.id}"
        )

        await interaction.followup.send(f"✅ Kanał online ustawiony na {kanal.mention}", ephemeral=True)


    @app_commands.command(name="boty", description="Ustawia kanał do liczenia botów.")
    @app_commands.describe(kanal='Kanał który będzie wyświetlał ilość botów.')
    async def boty(self, interaction: discord.Interaction, kanal: discord.VoiceChannel):

        await interaction.response.defer(ephemeral=True)
        UpdateGuildConfig(
            interaction.guild.id,
            {"statystyki": {"kanal_boty": kanal.id}},
            user_id=f"{interaction.user.id})"
        )

        await interaction.followup.send(f"✅ Kanał do liczenia botów ustawiony na: {kanal.mention}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Statystyki(bot))