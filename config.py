import json
import os
import inspect
import hashlib
from logger import logger, get_logger


logger = get_logger(__name__)


CONFIG_PATH = os.path.join("data", "config.json")
os.makedirs("data", exist_ok=True)

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
    except json.JSONDecodeError as e:
        logger.error("[CONFIG] ❌ Uszkodzony config.json — reset do domyślnego")
        return {"guilds": {}}


def save_config(data):
    ''' Funkcja do zapisywania configu.
    '''
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)


def get_guild_config(guild_id: int):
    ''' Funkcja do wczytywania configu.

        Args:
            guild_id: Id gildii, której chce dostać się parametry z configu.

        Returns:
            Parametr gildii z configu.
    '''
    data = load_config()
    return data.setdefault("guilds", {}).setdefault(str(guild_id), {})


def update_guild_config(
    guild_id: int,
    updates: dict,
    *,
    user_id: int | None = None,
    note: str | None = None,):
    ''' Funkcja do aktualizacja configu pre guild.

        Args:
            guild_id: Id gildii, z której użytkownik wykonuje komendę. W większości najlepiej użyć "interaction.guild.id".
            updates: Dictionary z danymi do dodania/zmiany.
            user_id: Id użytkownika. Anonimizowane potem w logach.
            note: Dodatkowa notatka

    '''

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

    hashed_user = (hashlib.sha256(f"{guild_id}-{user_id}".encode()).hexdigest() if user_id else "unknown")

    logger.info(
        "Config zmieniony | guild=%s | source=%s | updates=%s | hashed_user=%s | note=%s" ,
        guild_id,
        source,
        updates,
        hashed_user,
        note
    )

def delete_from_guild_config(
    guild_id: int,
    keys: dict,
    *,
    user_id: int | None = None,
    note: str | None = None,
):
    ''' Funkcja do usuwania wartości z configu per guild.
        Args:
            guild_id: Id gildii.
            keys: Dictionary z kluczami do usunięcia. Wartości są ignorowane, liczy się tylko struktura.
            user_id: Id użytkownika.
            note: Dodatkowa notatka.
    '''
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
    hashed_user = (hashlib.sha256(f"{guild_id}-{user_id}".encode()).hexdigest() if user_id else "unknown")
    logger.info(
        "Config usunięty | guild=%s | source=%s | keys=%s | hashed_user=%s | note=%s" ,
        guild_id,
        source,
        keys,
        hashed_user,
        note
    )