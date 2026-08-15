import traceback
from collections import Counter

import discord
from discord import app_commands
from discord.ext import commands, tasks

from utils.config import delete_from_guild_config, get_guild_config, update_guild_config
from utils.embeds import config_embed, error_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


async def set_channel_name(
    guild: discord.Guild, kanal_id: int, nazwa: str, liczba: int
):
    channel = guild.get_channel(kanal_id)
    if channel is None:
        return
    channel_name = f"{nazwa} {liczba}"
    if channel.name != channel_name:
        await channel.edit(name=channel_name)


async def update_channel_online(guild, kanal_id, nazwa, current_value):
    liczba = sum(
        1 for m in guild.members if m.status != discord.Status.offline and not m.bot
    )
    if current_value is not None:
        if liczba != current_value:
            await set_channel_name(guild, kanal_id, nazwa, liczba)
            update_guild_config(
                guild.id,
                {
                    "statistics": {
                        "current_online_value": liczba,
                    }
                },
            )
    else:
        await set_channel_name(guild, kanal_id, nazwa, liczba)
        update_guild_config(
            guild.id,
            {
                "statistics": {
                    "current_online_value": liczba,
                }
            },
        )


async def update_channel_bots(guild, kanal_id, nazwa, current_value):
    liczba = sum(1 for m in guild.members if m.bot)
    if current_value is not None:
        if liczba != current_value:
            await set_channel_name(guild, kanal_id, nazwa, liczba)
            update_guild_config(
                guild.id,
                {
                    "statistics": {
                        "current_bots_value": liczba,
                    }
                },
            )
    else:
        await set_channel_name(guild, kanal_id, nazwa, liczba)
        update_guild_config(
            guild.id,
            {
                "statistics": {
                    "current_bots_value": liczba,
                }
            },
        )


async def update_channel_members(guild, kanal_id, nazwa, current_value):
    liczba = sum(1 for m in guild.members if not m.bot)
    if current_value is not None:
        if liczba != current_value:
            await set_channel_name(guild, kanal_id, nazwa, liczba)
            update_guild_config(
                guild.id,
                {
                    "statistics": {
                        "current_members_value": liczba,
                    }
                },
            )
    else:
        await set_channel_name(guild, kanal_id, nazwa, liczba)
        update_guild_config(
            guild.id,
            {
                "statistics": {
                    "current_members_value": liczba,
                }
            },
        )


class Statystyki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = self.__class__.__name__

        self.group = StatystykiKomendy(self)
        self.bot.tree.add_command(self.group)

        self.update_online_count.start()

    async def cog_unload(self):
        self.update_online_count.cancel()
        self.bot.tree.remove_command(self.group.name)

    @commands.Cog.listener()
    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "Nie masz uprawnień do użycia tej komendy.", ephemeral=True
            )
            return

        logger.error("[SlashCommand] Błąd komendy:")
        traceback.print_exception(type(error), error, error.__traceback__)

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

                current_online_value = stat.get("current_online_value")
                current_members_value = stat.get("current_members_value")
                current_bots_value = stat.get("current_bots_value")

                category_id = stat.get("category_id")
                category_autodetect = stat.get("category_autodetect", True)

                if channel_online_id:
                    channel = guild.get_channel(channel_online_id)
                    if channel:
                        channel_online_name = stat.get("channel_online_name")
                        await update_channel_online(
                            guild,
                            channel_online_id,
                            channel_online_name,
                            current_online_value,
                        )
                    else:
                        delete_from_guild_config(
                            guild.id,
                            {
                                "statistics": {
                                    "channel_online_id": None,
                                    "channel_online_name": None,
                                }
                            },
                        )

                if channel_members_id:
                    channel = guild.get_channel(channel_members_id)
                    if channel:
                        channel_members_name = stat.get("channel_members_name")
                        await update_channel_members(
                            guild,
                            channel_members_id,
                            channel_members_name,
                            current_members_value,
                        )
                    else:
                        delete_from_guild_config(
                            guild.id,
                            {
                                "statistics": {
                                    "channel_members_id": None,
                                    "channel_members_name": None,
                                }
                            },
                        )

                if channel_bots_id:
                    channel = guild.get_channel(channel_bots_id)
                    if channel:
                        channel_bots_name = stat.get("channel_bots_name")
                        await update_channel_bots(
                            guild,
                            channel_bots_id,
                            channel_bots_name,
                            current_bots_value,
                        )
                    else:
                        delete_from_guild_config(
                            guild.id,
                            {
                                "statistics": {
                                    "channel_bots_id": None,
                                    "channel_bots_name": None,
                                }
                            },
                        )

                if category_id is None and category_autodetect:
                    category_list = []
                    for channel_id in [
                        channel_online_id,
                        channel_members_id,
                        channel_bots_id,
                    ]:
                        if channel_id:
                            channel = guild.get_channel(channel_id)
                            category = channel.category
                            if category:
                                category_list.append(category.id)
                    if len(category_list) >= 2:
                        most_common_category_id = Counter(category_list).most_common(1)[
                            0
                        ][0]
                        category = guild.get_channel(most_common_category_id)
                        update_guild_config(
                            guild.id,
                            {
                                "statistics": {
                                    "category_id": most_common_category_id,
                                    "category_name": category.name,
                                }
                            },
                            note="Zmiana dokonana przez automatyczne sprawdzanie kategori.",
                        )

        except Exception:
            logger.exception("Błąd w tasku update_online_count")

    @update_online_count.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)


# ─────────────────────────────────────────
# Komendy
# ─────────────────────────────────────────
async def create_or_get_voice_channel(
    interaction: discord.Interaction, kanal: str, nazwa: str
) -> discord.VoiceChannel | None:

    guild = interaction.guild
    if guild is None:
        return None

    if kanal == "__new__":
        cfg = get_guild_config(guild.id)
        stat = cfg.get("statistics")
        category_id = stat.get("category_id")
        if category_id:
            category_obj = guild.get_channel(category_id)
            category = (
                category_obj
                if isinstance(category_obj, discord.CategoryChannel)
                else None
            )
        else:
            category = None

        channel = await guild.create_voice_channel(name=nazwa, category=category)
    else:
        channel_obj = guild.get_channel(int(kanal))
        channel = channel_obj if isinstance(channel_obj, discord.VoiceChannel) else None

    return channel


@app_commands.guild_only()
class StatystykiKomendy(app_commands.Group):
    def __init__(self, cog: Statystyki):
        self.cog = cog
        super().__init__(
            name="statystyki",
            description="Komendy do ustawienia kanałów ze statystykami.",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not isinstance(interaction.user, discord.Member)
            or not interaction.user.guild_permissions.administrator
        ):
            raise app_commands.MissingPermissions(["administrator"])
        return True

    async def channel_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []

        guild = interaction.guild
        if guild is None:
            return []

        for channel in guild.voice_channels:
            if current.lower() in channel.name.lower():
                choices.append(
                    app_commands.Choice(name=channel.name, value=str(channel.id))
                )

        if "nowy".startswith(current.lower()) or current == "":
            choices.append(
                app_commands.Choice(name="➕ Utwórz nowy kanał", value="__new__")
            )

        return choices[:25]

    # noinspection PyMethodMayBeStatic
    async def category_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []

        guild = interaction.guild
        if guild is None:
            return []

        for category in guild.categories:
            if current.lower() in category.name.lower():
                choices.append(
                    app_commands.Choice(name=category.name, value=str(category.id))
                )

        if "nowy".startswith(current.lower()) or current == "":
            choices.append(
                app_commands.Choice(name="➕ Utwórz nową kategorię", value="__new__")
            )

        return choices[:25]

    @app_commands.command(
        name="dodaj", description="Dodaje kanał do liczenia statystyk."
    )
    @app_commands.autocomplete(kanal=channel_autocomplete)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        rodzaj="Rodzaj statystyki.",
        kanal="Kanał, który będzie wyświetlał ilość użytkowników online.",
        nazwa="Nazwa kanału.",
    )
    @app_commands.choices(
        rodzaj=[
            app_commands.Choice(name="Online", value="online"),
            app_commands.Choice(name="Boty", value="bots"),
            app_commands.Choice(name="Członkowie", value="members"),
        ]
    )
    async def dodaj(
        self,
        interaction: discord.Interaction,
        rodzaj: app_commands.Choice[str],
        kanal: str,
        nazwa: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            guild = interaction.guild
            if guild is None:
                return

            if nazwa is None:
                cfg = get_guild_config(guild.id)
                stat = cfg.get("statistics") or {}
                nazwa = stat.get(f"channel_{rodzaj.value}_name")
                if nazwa is None:
                    nazwa = f"{rodzaj.name}: "

            channel = await create_or_get_voice_channel(interaction, kanal, nazwa)

            if channel is None:
                await interaction.followup.send(
                    "Nie udało się utworzyć lub znaleźć kanału głosowego.",
                    ephemeral=True,
                )
                return

            update_guild_config(
                guild.id,
                {
                    "statistics": {
                        f"channel_{rodzaj.value}_id": channel.id,
                        f"channel_{rodzaj.value}_name": nazwa,
                    }
                },
            )
            await interaction.followup.send(
                embed=config_embed(
                    f"Kanał do pokazywania statystyki '{rodzaj.name}' został ustawiony na:",
                    value=channel.mention,
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name="kategoria",
        description="Ustawia kategorię do wyświetlania statystyk serwera.",
    )
    @app_commands.autocomplete(kategoria=category_autocomplete)
    @app_commands.describe(
        kategoria="Kategoria, która będzie wyświetlała statystyki.",
        nazwa="Nazwa kategorii.",
    )
    async def category(
        self,
        interaction: discord.Interaction,
        kategoria: str,
        nazwa: str | None = "Statystyki",
    ):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            guild = interaction.guild
            if guild is None:
                return

            category_obj = guild.get_channel(int(kategoria))
            if category_obj is None:
                await interaction.followup.send(
                    "Nie znaleziono wybranej kategorii.", ephemeral=True
                )
                return

            update_guild_config(
                guild.id,
                {
                    "statistics": {
                        "category_id": category_obj.id,
                        "category_name": nazwa,
                    }
                },
                user_id=interaction.user.id,
            )
            await interaction.followup.send(
                embed=config_embed(
                    "Kategoria do wyświetlania statystyk ustawiona na:",
                    category_obj.name,
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(
        name="automatyczne-kategori",
        description="Włącza lub wyłącza automatyczne wykrywanie kategorii.",
    )
    @app_commands.describe(wlaczone="Czy funkcja jest włączona.")
    async def category_autodetect(
        self, interaction: discord.Interaction, wlaczone: bool
    ):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            guild = interaction.guild
            if guild is None:
                return

            update_guild_config(
                guild.id,
                {"statistics": {"category_autodetect": wlaczone}},
                user_id=interaction.user.id,
            )
            await interaction.followup.send(
                embed=config_embed(
                    "Automatyczne sprawdzanie kategorii ustawione na:", wlaczone
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Statystyki(bot))
