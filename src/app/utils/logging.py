import os
import sys
from pathlib import Path
from loguru import logger


def _get_log_dir() -> Path:
    """Возвращает правильную папку для логов в зависимости от ОС (без прав админа)."""
    if sys.platform == "win32":
        # C:\Users\<User>\AppData\Local\Instally\logs
        base_dir = os.getenv("LOCALAPPDATA", os.path.expanduser("~"))
        log_dir = Path(base_dir) / "Instally" / "logs"
    elif sys.platform.startswith("linux"):
        # ~/.local/share/Instally/logs
        log_dir = Path.home() / ".local" / "share" / "Instally" / "logs"
    else:
        # macOS и прочие
        log_dir = Path.home() / ".instally" / "logs"
        
    return log_dir


# Папка для логов
LOGS_DIR = _get_log_dir()
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# --- Настройка логгера ---
logger.remove()  # Удаляем стандартный обработчик

# Консоль — с цветом и кратким форматом (для отладки в IDE)
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
    rotation="10 MB",       # Ротация при достижении 10 МБ
    retention="7 days",     # Храним логи за последние 7 дней
    encoding="utf-8",
    enqueue=True,           # Безопасно для многопоточности (ChocoWorker)
    backtrace=True,
    diagnose=True,
)