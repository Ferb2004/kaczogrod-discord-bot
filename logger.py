import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = "bot.log"

os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger():
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # nie dubluj handlerów przy reloadach

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Konsola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

#TODO różnie pliki dla różnych serwerów, tylko błędy trafiają do ogólnego pliku z logami
    # Plik (rotacja)
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, LOG_FILE),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()