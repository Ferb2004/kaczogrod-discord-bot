import discord
from discord.ext import commands, tasks
from discord import app_commands, TextChannel

from logger import logger, get_logger, log_cog_loaded
from config import update_guild_config, get_guild_config, delete_from_guild_config
from embeds import config_embed, error_embed, custom_error_embed

from collections import Counter


logger = get_logger(__name__)


async def set_channel_name(guild: discord.Guild, kanal_id: int, nazwa: str, liczba: int):
    channel = guild.get_channel(kanal_id)
    if channel is None:
        return
    channelName = f"{nazwa} {liczba}"
    if channel.name != channelName:
        await channel.edit(name=channelName)

async def update_channel_online(guild, kanal_id, nazwa):
    liczba = sum(1 for m in guild.members if m.status != discord.Status.offline and not m.bot)
    await set_channel_name(guild, kanal_id, nazwa, liczba)

async def update_channel_bots(guild, kanal_id, nazwa):
    liczba = sum(1 for m in guild.members if m.bot)
    await set_channel_name(guild, kanal_id, nazwa, liczba)

async def update_channel_members(guild, kanal_id, nazwa):
    liczba = sum(1 for m in guild.members if not m.bot)
    await set_channel_name(guild, kanal_id, nazwa, liczba)


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


# ─────────────────────────────────────────
# Główna pętla
# ─────────────────────────────────────────
    @tasks.loop(minutes=1)
    async def update_online_count(self):
        try:
            for guild in self.bot.guilds:
                cfg = get_guild_config(guild.id)

                stat = cfg.get("statistics")
                if not stat:
                    continue

                channel_online_id = stat.get("channel_online_id")
                channel_members_id = stat.get("channel_members_id")
                channel_bots_id = stat.get("channel_bots_id")
                category_id = stat.get("category_id")
                category_autodetect = stat.get("category_autodetect", True)

                if channel_online_id:
                    channel = guild.get_channel(channel_online_id)
                    if channel:
                        channel_online_name = stat.get("channel_online_name")
                        await update_channel_online(guild, channel_online_id, channel_online_name)
                    else:
                        delete_from_guild_config(guild.id, {"statistics": {"channel_online_id": None, "channel_online_name": None}})

                if channel_members_id:
                    channel = guild.get_channel(channel_members_id)
                    if channel:
                        channel_members_name = stat.get("channel_members_name")
                        await update_channel_members(guild, channel_members_id, channel_members_name)
                    else:
                        delete_from_guild_config(guild.id, {"statistics": {"channel_members_id": None, "channel_members_name": None}})

                if channel_bots_id:
                    channel = guild.get_channel(channel_bots_id)
                    if channel:
                        channel_bots_name = stat.get("channel_bots_name")
                        await update_channel_bots(guild, channel_bots_id, channel_bots_name)
                    else:
                        delete_from_guild_config(guild.id, {"statistics": {"channel_bots_id": None, "channel_bots_name": None}})


                if category_id is None and category_autodetect:
                    category_list = []
                    for channel_id in [channel_online_id, channel_members_id, channel_bots_id]:
                        if channel_id:
                            channel = guild.get_channel(channel_id)
                            category = channel.category
                            if category:
                                category_list.append(category.id)
                    if len(category_list) >= 2:
                        most_common_category_id = Counter(category_list).most_common(1)[0][0]
                        category = guild.get_channel(most_common_category_id)
                        update_guild_config(guild.id, {"statistics": {"category_id": most_common_category_id, "category_name": category.name}}, note="Zmiana dokonana przez automatyczne sprawdzanie kategori.")

        except Exception as e:
            logger.error(f"Błąd w tasku update_online_count", exc_info=True)

    @update_online_count.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)


# ─────────────────────────────────────────
# Komendy
# ─────────────────────────────────────────

async def create_or_get_voice_channel(interaction: discord.Interaction, kanal: str, nazwa: str) -> discord.VoiceChannel | None:
    if kanal == "__new__":
        cfg = get_guild_config(interaction.guild.id)
        stat = cfg.get("statistics")
        category_id = stat.get("category_id")
        if category_id:
            category =interaction.guild.get_channel(category_id)
        else:
            category = None

        channel = await interaction.guild.create_voice_channel(
            name=nazwa,
            category=category
            )
    else:
        channel = interaction.guild.get_channel(int(kanal))

    return channel

class StatystykiKomendy(app_commands.Group):
    def __init__(self, cog: "Statystyki"):
        self.cog = cog
        super().__init__(
            name="statystyki",
            description="Komendy do ustawienia kanałów ze statystykami."
        )
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()

    async def channel_autocomplete(self, interaction: discord.Interaction, current: str) -> list[
        app_commands.Choice[str]]:
        choices = []

        for channel in interaction.guild.voice_channels:
            if current.lower() in channel.name.lower():
                choices.append(app_commands.Choice(name=channel.name, value=str(channel.id)))

        if "nowy".startswith(current.lower()) or current == "":
            choices.append(app_commands.Choice(name="➕ Utwórz nowy kanał", value="__new__"))

        return choices[:25]

    async def category_autocomplete(self, interaction: discord.Interaction, current: str) -> list[
        app_commands.Choice[str]]:
        choices = []

        for category in interaction.guild.categories:
            if current.lower() in category.name.lower():
                choices.append(app_commands.Choice(name=category.name, value=str(category.id)))

        if "nowy".startswith(current.lower()) or current == "":
            choices.append(app_commands.Choice(name="➕ Utwórz nową kategorię", value="__new__"))

        return choices[:25]

    @app_commands.command(name="online", description="Ustawia kanał do liczenia członków online.")
    @app_commands.autocomplete(kanal=channel_autocomplete)
    @app_commands.describe(kanal='Kanał, który będzie wyświetlał ilość użytkowników online.', nazwa="Nazwa kanału.")
    async def online(self, interaction: discord.Interaction, kanal: str, nazwa: str | None = None):
        await interaction.response.defer(ephemeral=True)
        try:
            if nazwa is None:
                cfg = get_guild_config(interaction.guild.id)
                stat = cfg.get("statistics") or {}
                nazwa = stat.get("channel_online_name")
                if nazwa is None:
                    nazwa = 'Online: '

            channel = await create_or_get_voice_channel(interaction, kanal, nazwa)

            update_guild_config(interaction.guild.id, {"statistics": {"channel_online_id": channel.id, "channel_online_name": nazwa}}, user_id=interaction.user.id)
            await interaction.followup.send(embed=config_embed(f"Kanał do liczenia użytkowników online ustawiony na:",channel.mention), ephemeral=True)
        except Exception as e:
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="czlonkowie", description="Ustawia kanał do liczenia członków.")
    @app_commands.autocomplete(kanal=channel_autocomplete)
    @app_commands.describe(kanal='Kanał, który będzie wyświetlał ilość członków.', nazwa="Nazwa kanału.")
    async def members(self, interaction: discord.Interaction, kanal: str, nazwa: str | None = None):
        await interaction.response.defer(ephemeral=True)
        try:
            if nazwa is None:
                cfg = get_guild_config(interaction.guild.id)
                stat = cfg.get("statistics") or {}
                nazwa = stat.get("channel_members_name")
                if nazwa is None:
                    nazwa = 'Na serwerze: '

            channel = await create_or_get_voice_channel(interaction, kanal, nazwa)

            update_guild_config(interaction.guild.id, {"statistics": {"channel_members_id": channel.id, "channel_members_name": nazwa}}, user_id=interaction.user.id)
            await interaction.followup.send(embed=config_embed(f"Kanał do liczenia członków ustawiony na:",channel.mention), ephemeral=True)
        except Exception as e:
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="boty", description="Ustawia kanał do liczenia botów.")
    @app_commands.autocomplete(kanal=channel_autocomplete)
    @app_commands.describe(kanal='Kanał, który będzie wyświetlał ilość botów.', nazwa="Nazwa kanału.")
    async def bots(self, interaction: discord.Interaction, kanal: str, nazwa: str | None = None):
        await interaction.response.defer(ephemeral=True)
        try:
            if nazwa is None:
                cfg = get_guild_config(interaction.guild.id)
                stat = cfg.get("statistics") or {}
                nazwa = stat.get("channel_bots_name")
                if nazwa is None:
                    nazwa = 'Boty: '

            channel = await create_or_get_voice_channel(interaction, kanal, nazwa)

            update_guild_config(interaction.guild.id, {"statistics": {"channel_bots_id": channel.id, "channel_bots_name": nazwa}}, user_id=interaction.user.id)
            await interaction.followup.send(embed= config_embed(f"Kanał do liczenia botów ustawiony na:",channel.mention), ephemeral=True)
        except Exception as e:
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="kategoria", description="Ustawia kategorię do wyświetlania statystyk serwera.")
    @app_commands.autocomplete(kategoria=category_autocomplete)
    @app_commands.describe(kategoria='Kategoria, która będzie wyświetlała statystyki.', nazwa="Nazwa kategorii.")
    async def category(self, interaction: discord.Interaction, kategoria: str, nazwa: str | None = 'Statystyki'):
        await interaction.response.defer(ephemeral=True)
        try:
            category_obj = interaction.guild.get_channel(int(kategoria))
            update_guild_config(interaction.guild.id, {"statistics": {"category_id": category_obj.id, "category_name": nazwa}}, user_id=interaction.user.id)
            await interaction.followup.send(embed= config_embed(f"Kategoria do wyświetlania statystyk ustawiona na:", category_obj.name), ephemeral=True)
        except Exception as e:
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="automatyczne-kategori", description="Włącza lub wyłącza automatyczne wykrywanie kategorii.")
    @app_commands.describe(wlaczone='Czy funkcja jest włączona.')
    async def category_autodetect(self, interaction: discord.Interaction, wlaczone: bool):
        await interaction.response.defer(ephemeral=True)
        try:
            update_guild_config(interaction.guild.id, {"statistics": {"category_autodetect": wlaczone}}, user_id=interaction.user.id)
            await interaction.followup.send(embed=config_embed(f"Automatyczne sprawdzanie kategorii ustawione na:", wlaczone), ephemeral=True)
        except Exception as e:
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Statystyki(bot))