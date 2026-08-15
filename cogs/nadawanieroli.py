import traceback

import discord
from discord import app_commands
from discord.ext import commands

from utils.config import (
    add_getrole_role,
    get_guild_config,
    remove_getrole_role,
    update_guild_config,
)
from utils.embeds import config_embed, error_embed
from utils.logger import get_logger, log_cog_loaded

logger = get_logger(__name__)


class MinecraftWhitelistModal(discord.ui.Modal):
    minecraft_name = discord.ui.TextInput(
        label="Nick Minecraft", style=discord.TextStyle.short
    )

    def __init__(self, guild_id):
        super().__init__(
            title="Prośba o dodanie do whitelisty",
            timeout=None,
            custom_id=f"mcwl_{guild_id}_modal",
        )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            self.minecraft_name.value, ephemeral=True
        )


def build_role_options(guild_id: int) -> list[discord.SelectOption]:
    """Buduje listę SelectOption na podstawie aktualnego configu gildii."""
    cfg = get_guild_config(guild_id)
    roles_data = cfg.get("getrole", {}).get("roles", [])

    return [
        discord.SelectOption(
            label=role["role_name"],
            value=str(role["role_id"]),
            description=role.get("description"),
            emoji=role.get("emoji"),
        )
        for role in roles_data
    ]


async def refresh_role_select_message(bot, guild_id: int):
    """Aktualizuje istniejącą wiadomość z select menu na podstawie aktualnego configu."""
    cfg = get_guild_config(guild_id)
    getrole_cfg = cfg.get("getrole", {})

    channel_id = getrole_cfg.get("channel_id")
    message_id = getrole_cfg.get("message_id")

    if not channel_id or not message_id:
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        return

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        return

    options = build_role_options(guild_id)

    if not options:
        await message.edit(content="Brak dostępnych ról do wyboru.", view=None)
        return

    view = RoleSelect(max_values=len(options))
    view.select.options = options

    await message.edit(content="Wybierz swoje role:", view=view)


class RoleSelect(discord.ui.View):
    def __init__(self, max_values: int = 25):
        super().__init__(timeout=None)
        self.select = RoleSelectMenu(max_values)
        self.add_item(self.select)


class RoleSelectMenu(discord.ui.Select):
    def __init__(self, max_values: int = 25):
        super().__init__(
            placeholder="Wybierz role",
            min_values=0,
            max_values=max_values,
            options=[discord.SelectOption(label="placeholder", value="0")],
            custom_id="getrole_selectmenu",
        )

    async def callback(self, interaction: discord.Interaction):
        if interaction.guild is None or not isinstance(
            interaction.user, discord.Member
        ):
            return

        guild = interaction.guild
        member = interaction.user
        cfg = get_guild_config(guild.id)

        roles_data = cfg.get("getrole", {}).get(
            "roles", []
        )  # świeże dane, nie z self.options

        selected_ids = [int(v) for v in self.values]
        all_role_ids = [role["role_id"] for role in roles_data]

        roles_to_add = []
        roles_to_remove = []

        for role_id in all_role_ids:
            role = guild.get_role(role_id)
            if role is None:
                continue

            if role_id in selected_ids and role not in member.roles:
                roles_to_add.append(role)

            if role_id not in selected_ids and role in member.roles:
                roles_to_remove.append(role)

        if roles_to_add:
            await member.add_roles(*roles_to_add)
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove)

        await interaction.response.send_message(
            "Twoje role zostały zaktualizowane!", ephemeral=True
        )


class NadawanieRoli(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.name = self.__class__.__name__

        self.group = NadawanieRoliKomendy(self)
        self.bot.tree.add_command(self.group)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.group.name)

    @commands.Cog.listener()
    async def on_ready(self):
        log_cog_loaded(__name__)

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


@app_commands.guild_only()
class NadawanieRoliKomendy(app_commands.Group):
    def __init__(self, cog: NadawanieRoli):
        self.cog = cog
        super().__init__(
            name="nadawanieroli",
            description="Komendy do zarządzania nadawaniem roli przez użytkowników.",
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if (
            not isinstance(interaction.user, discord.Member)
            or not interaction.user.guild_permissions.administrator
        ):
            raise app_commands.MissingPermissions(["administrator"])
        return True

    async def rola_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = []
        guild = interaction.guild
        if guild is None:
            return []

        cfg = get_guild_config(guild.id)
        getrole_cfg = cfg.get("getrole", {})
        roles = getrole_cfg.get("roles", [])
        if not roles:
            return []

        for role_data in roles:
            role_name = role_data.get("role_name")
            role_id = role_data.get("role_id")

            name = f"{role_name} / {role_id}"
            if current.lower() in name.lower():
                choices.append(
                    app_commands.Choice(name=role_name, value=str(role_id))
                )  # <- str()

        return choices[:25]

    @app_commands.command(name="kanal", description="Ustawia kanał, do nadawania ról.")
    @app_commands.describe(kanal="Kanał, do nadawania roli.")
    async def kanal(self, interaction: discord.Interaction, kanal: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            options = build_role_options(interaction.guild.id)

            if not options:
                await interaction.followup.send(
                    "❌ Najpierw dodaj chociaż jedną rolę przez `/nadawanieroli dodaj`.",
                    ephemeral=True,
                )
                return

            view = RoleSelect(max_values=len(options))
            view.select.options = options

            sent_message = await kanal.send("Wybierz swoje role:", view=view)

            update_guild_config(
                interaction.guild.id,
                {
                    "getrole": {
                        "channel_id": kanal.id,
                        "message_id": sent_message.id,
                    }
                },
            )

            await interaction.followup.send(
                embed=config_embed(
                    "Kanał na, którym użytkownicy mogą dawać sobie rolę został ustawiony na:",
                    value=kanal.mention,
                ),
                ephemeral=True,
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="dodaj", description="Dodaje rolę.")
    @app_commands.describe(
        rola="Rola, którą użytkownicy będą mogli sobie dać.",
        opis="Krótki opis tej roli.",
        emoji="Emoji, które będzie wyświetlane.",
    )
    async def rola_dodaj(
        self,
        interaction: discord.Interaction,
        rola: discord.Role,
        opis: str | None = None,
        emoji: str | None = None,
    ):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            parsed_emoji = None
            if emoji is not None:
                try:
                    parsed_emoji = discord.PartialEmoji.from_str(emoji)
                except Exception:
                    logger.exception("Nieoczekiwany błąd.")
                    await interaction.followup.send(
                        "Nie znaleziono emoji.", ephemeral=True
                    )
                    return

            try:
                add_getrole_role(
                    interaction.guild.id,
                    rola.name,
                    rola.id,
                    opis,
                    str(parsed_emoji) if parsed_emoji else None,
                )
            except ValueError as ve:
                await interaction.followup.send(str(ve), ephemeral=True)
                return

            await refresh_role_select_message(self.cog.bot, interaction.guild.id)

            await interaction.followup.send(
                embed=config_embed("Dodano rolę:", value=rola.mention), ephemeral=True
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    @app_commands.command(name="usun", description="Usuwa rolę.")
    @app_commands.describe(
        rola="Rola, którą będzie usunięta.",
    )
    @app_commands.autocomplete(rola=rola_autocomplete)
    async def remove(self, interaction: discord.Interaction, rola: str):
        await interaction.response.defer(ephemeral=True)
        assert interaction.guild is not None
        try:
            role_id = int(rola)  # <- bezpośrednio konwertuj string na int, bez .value
            remove_getrole_role(interaction.guild.id, role_id)

            discord_role = interaction.guild.get_role(role_id)
            role_display = discord_role.mention if discord_role else f"ID {role_id}"

            await refresh_role_select_message(self.cog.bot, interaction.guild.id)

            await interaction.followup.send(
                embed=config_embed("Usunięto rolę:", value=role_display), ephemeral=True
            )
        except Exception as e:
            logger.exception("Nieoczekiwany błąd.")
            embed, view = error_embed(e)
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)


async def setup(bot):
    bot.add_view(RoleSelect())
    await bot.add_cog(NadawanieRoli(bot))
