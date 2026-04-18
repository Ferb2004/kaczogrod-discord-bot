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

def LoadConfig():
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


def SaveConfig(data):
    ''' Funkcja do zapisywania configu.
    '''
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)


def GetGuildConfig(guild_id: int):
    ''' Funkcja do wczytywania configu.

        Args:
            guild_id: Id gildii, której chce dostać się parametry z configu.

        Returns:
            Zwraca parametr gildii z configu.
    '''
    data = LoadConfig()
    return data.setdefault("guilds", {}).setdefault(str(guild_id), {})


def UpdateGuildConfig(
    guild_id: int,
    updates: dict,
    *,
    user_id: int | None = None):
    ''' Funkcja do aktualizacja configu pre guild.

        Args:
            guild_id: Id gildii, z której użytkownik wykonuje komendę. W większości najlepiej użyć "interaction.guild.id".
            updates: Dictionary z danymi do dodania/zmiany.
            user_id: Id użytkownika. Anonimizowane potem w logach.

    '''

    data = LoadConfig()

    guilds = data.setdefault("guilds", {})
    guild_cfg = guilds.setdefault(str(guild_id), {})

    def deep_update(dst, src):
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_update(dst[k], v)
            else:
                dst[k] = v

    deep_update(guild_cfg, updates)
    SaveConfig(data)

    source = _detect_source()

    hashed_user = (hashlib.sha256(f"{guild_id}-{user_id}".encode()).hexdigest() if user_id else "unknown")

    logger.info(
        "Config zmieniony | guild=%s | source=%s | updates=%s | hashed_user=%s",
        guild_id,
        source,
        updates,
        hashed_user
    )


# ─────────────────────────────────────────
# Funkcje do zarządzania hashem commitu
# ─────────────────────────────────────────
def GetStoredCommit() -> str | None:
    data = LoadConfig()
    return data.get("meta", {}).get("last_commit")


def SetStoredCommit(commit_sha: str):
    data = LoadConfig()
    meta = data.setdefault("meta", {})
    meta["last_commit"] = commit_sha
    SaveConfig(data)

#TODO zrobić żeby usuwanie z configu działało
def DeleteFromConfig(data):
    del data
