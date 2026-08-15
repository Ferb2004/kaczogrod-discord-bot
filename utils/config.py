import hashlib
import inspect
import json
import os

from utils.logger import get_logger

logger = get_logger(__name__)

PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(PROJECT_ROOT, "data", "config.json")
os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)


def _detect_source() -> str:
    frame = inspect.currentframe()

    while frame:
        module = frame.f_globals.get("__name__", "")
        if module.startswith("cogs."):
            file = os.path.basename(frame.f_code.co_filename)
            func = frame.f_code.co_name
            return f"{module}.{file}.{func}"
        frame = frame.f_back

    return "unknown"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"guilds": {}}

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"guilds": {}}
            return json.loads(content)
    except json.JSONDecodeError:
        logger.error("[CONFIG] ❌ Uszkodzony config.json — reset do domyślnego")
        return {"guilds": {}}


def save_config(data):
    """Funkcja do zapisywania configu."""
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=4)


def get_guild_config(guild_id: int):
    """Funkcja do wczytywania configu.

    Args:
        guild_id: Id gildii, której chce dostać się parametry z configu.

    Returns:
        Parametr gildii z configu.
    """
    data = load_config()
    return data.setdefault("guilds", {}).setdefault(str(guild_id), {})


def update_guild_config(
    guild_id: int,
    updates: dict,
    *,
    user_id: int | None = None,
    note: str | None = None,
):
    """Funkcja do aktualizacja configu pre guild.

    Args:
        guild_id: Id gildii, z której użytkownik wykonuje komendę. W większości najlepiej użyć "interaction.guild.id".
        updates: Dictionary z danymi do dodania/zmiany.
        user_id: Id użytkownika. Anonimizowane potem w logach.
        note: Dodatkowa notatka

    """

    data = load_config()

    guilds = data.setdefault("guilds", {})
    guild_cfg = guilds.setdefault(str(guild_id), {})

    def deep_update(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_update(dst[k], v)
            else:
                dst[k] = v

    deep_update(guild_cfg, updates)
    save_config(data)

    source = _detect_source()

    hashed_user = (
        hashlib.sha256(f"{guild_id}-{user_id}".encode()).hexdigest()
        if user_id
        else "unknown"
    )

    logger.debug(
        "Config zmieniony | guild=%s | source=%s | updates=%s | hashed_user=%s | note=%s",
        guild_id,
        source,
        updates,
        hashed_user,
        note,
    )


def delete_from_guild_config(
    guild_id: int,
    keys: dict,
    *,
    user_id: int | None = None,
    note: str | None = None,
):
    """Funkcja do usuwania wartości z configu per guild.
    Args:
        guild_id: Id gildii.
        keys: Dictionary z kluczami do usunięcia. Wartości są ignorowane, liczy się tylko struktura.
        user_id: Id użytkownika.
        note: Dodatkowa notatka.
    """
    data = load_config()
    guilds = data.setdefault("guilds", {})
    guild_cfg = guilds.setdefault(str(guild_id), {})

    def deep_delete(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_delete(dst[k], v)
            else:
                dst.pop(k, None)

    deep_delete(guild_cfg, keys)
    save_config(data)

    source = _detect_source()
    hashed_user = (
        hashlib.sha256(f"{guild_id}-{user_id}".encode()).hexdigest()
        if user_id
        else "unknown"
    )
    logger.info(
        "Config usunięty | guild=%s | source=%s | keys=%s | hashed_user=%s | note=%s",
        guild_id,
        source,
        keys,
        hashed_user,
        note,
    )


def add_rss_feed(
    guild_id: int, feed_url: str, channel_id: int, *, user_id: int | None = None
):
    """Dodaje nowy feed RSS/Atom do configu gildii."""
    cfg = get_guild_config(guild_id)
    feeds = cfg.get("rss", [])

    feeds.append(
        {
            "feed_url": feed_url,
            "channel_id": channel_id,
            "last_entry_id": None,
            "etag": None,
            "modified": None,
        }
    )

    update_guild_config(
        guild_id, {"rss": feeds}, user_id=user_id, note=f"Dodano feed {feed_url}"
    )


def remove_rss_feed(
    guild_id: int, feed_url: str, channel_id, *, user_id: int | None = None
):
    """Usuwa feed RSS/Atom z configu gildii po URL oraz ID kanału."""
    cfg = get_guild_config(guild_id)
    feeds = cfg.get("rss", [])

    feeds = [
        f
        for f in feeds
        if not (f.get("feed_url") == feed_url and f.get("channel_id") == channel_id)
    ]

    update_guild_config(
        guild_id, {"rss": feeds}, user_id=user_id, note=f"Usunięto feed {feed_url}"
    )


def update_rss_feed_state(guild_id: int, feed_url: str, **state_updates):
    """Aktualizuje stan konkretnego feeda (np. last_entry_id, etag, modified)."""
    cfg = get_guild_config(guild_id)
    feeds = cfg.get("rss", [])

    for feed in feeds:
        if feed.get("feed_url") == feed_url:
            feed.update(state_updates)
            break

    update_guild_config(guild_id, {"rss": feeds})


def add_getrole_role(
    guild_id: int,
    role_name: str,
    role_id: int,
    description: str | None = None,
    emoji: str | None = None,
    *,
    user_id: int | None = None,
):
    """Dodaje nową rolę do configu gildii."""
    cfg = get_guild_config(guild_id)
    getrole_cfg = cfg.get("getrole", {})
    roles = getrole_cfg.get("roles", [])

    if any(r.get("role_id") == role_id for r in roles):
        raise ValueError("Ta rola jest już dodana do listy.")

    roles.append(
        {
            "role_name": role_name,
            "role_id": role_id,
            "description": description,
            "emoji": emoji,
        }
    )

    update_guild_config(
        guild_id,
        {"getrole": {"roles": roles}},
        user_id=user_id,
        note=f"Dodano rolę {role_name}",
    )


def remove_getrole_role(guild_id: int, role_id: int, *, user_id: int | None = None):
    """Usuwa rolę z configu gildii po ID."""
    cfg = get_guild_config(guild_id)
    getrole_cfg = cfg.get("getrole", {})
    roles = getrole_cfg.get("roles", [])

    roles = [f for f in roles if f.get("role_id") != role_id]

    update_guild_config(guild_id, {"getrole": {"roles": roles}}, user_id=user_id)
