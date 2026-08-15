import logging
import os
from logging.handlers import RotatingFileHandler
from typing import ClassVar

# TODO wyczyścić kod

# ─────────────────────────────────────────
# Konfiguracja katalogu i ścieżek
# ─────────────────────────────────────────
PROJECT_ROOT: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "bot.log")
os.makedirs(LOG_DIR, exist_ok=True)


# ─────────────────────────────────────────
# Formattery i handlery
# ─────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_cog_loaded(module_name: str):
    get_logger(module_name).info("Cog aktywny i gotowy")


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    if logger.handlers:
        return logger

    class DefaultFormatter(logging.Formatter):
        LEVEL_EMOJI: ClassVar[dict[int, str]] = {
            logging.INFO: "[ℹ]",
            logging.WARNING: "[⚠️]",
            logging.ERROR: "[❌]",
            logging.CRITICAL: "[🔥]",
        }

        def format(self, record):
            record.emoji = self.LEVEL_EMOJI.get(record.levelno, "")
            return super().format(record)

        def formatException(self, ei):
            import os
            import traceback

            tb_lines = traceback.format_exception(*ei)
            cleaned_lines = []

            for line in tb_lines:
                if 'File "' in line:
                    parts = line.split('File "')
                    if len(parts) > 1:
                        before, after = parts[0], parts[1]
                        path, rest = after.split('"', 1)

                        try:
                            rel_path = os.path.relpath(path, PROJECT_ROOT)

                            # Ścieżki zaczynające się od ".." wskazują na zależności zewnętrzne
                            # (venv, biblioteki systemowe) — skracamy do samej nazwy pliku
                            # żeby logi nie ujawniały struktury środowiska deweloperskiego
                            if rel_path.startswith(".."):
                                rel_path = os.path.basename(path)

                        except ValueError:
                            # Windows: os.path.relpath() rzuca ValueError przy różnych dyskach
                            # (np. plik w C:\ gdy PROJECT_ROOT jest w D:\) — fallback do nazwy pliku
                            rel_path = os.path.basename(path)

                        line = f'{before}File "{rel_path}"{rest}'

                cleaned_lines.append(line)

            return "".join(cleaned_lines)

    formatter = DefaultFormatter(
        "[%(asctime)s] %(emoji)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 5MB na plik — kompromis między rozmiarem a zachowaniem
    # wystarczającej historii przy typowym ruchu bota (~1k eventów/h)
    # backupCount=5 daje łącznie ~25MB historii logów
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
