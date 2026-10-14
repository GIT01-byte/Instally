import sys

import loguru

from core.config import BASE_DIR

LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = loguru.logger

logger.remove()

# Консоль — с цветом и кратким форматом
if sys.stderr is not None:
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="DEBUG",
        colorize=True,
    )

# Файл — полный формат, с ротацией
logger.add(
    (LOGS_DIR / "app.log"),
    format="{time:YYYY-MM-DD HH:mm:ss,SSS} [{level}] ({thread.name}) {message}",
    level="INFO",
    rotation="10 MB",
    retention="7 days",
    encoding="utf-8",
    enqueue=True,  # безопасно для многопоточности (ChocoWorker)
    backtrace=True,
    diagnose=True,
)
