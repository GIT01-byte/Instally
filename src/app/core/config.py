from configparser import ConfigParser
from pathlib import Path
import sys

# --- Определяем базовую директорию с учётом PyInstaller ---
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parents[2]

CONFIG_PATH = BASE_DIR / "src" / "config.ini"

# ---------------------------------------------------------------------------
# Дефолтные значения (используются, если config.ini нет / битый / неполный)
# ---------------------------------------------------------------------------
DEFAULTS: dict[str, dict[str, str]] = {
    "App": {
        "log_level": "INFO",
    },
}


def _build_default_config() -> ConfigParser:
    """Создаёт ConfigParser из DEFAULTS — эквивалент «нет файла, но всё есть»."""
    cfg = ConfigParser()
    for section, options in DEFAULTS.items():
        cfg.add_section(section)
        for key, value in options.items():
            cfg.set(section, key, value)
    return cfg


def _load_config() -> ConfigParser:
    """
    Пытается прочитать config.ini. Если файла нет, он пуст, битый или в нём
    отсутствуют нужные секции — возвращает дефолтный конфиг и пишет warning.
    """
    cfg = ConfigParser()

    read_ok = cfg.read(CONFIG_PATH, encoding="utf-8")

    if not read_ok:
        # Файла нет, либо он не прочитался (кодировка/BOM/права)
        cfg = _build_default_config()
        print(
            f"[config] Файл конфига не найден или не читается: {CONFIG_PATH}. "
            f"Использую значения по умолчанию."
        )
        return cfg

    # Файл прочитан — но мог не содержать нужных секций.
    # Добавляем недостающие секции/ключи из DEFAULTS, не перетирая существующие.
    changed = False
    for section, options in DEFAULTS.items():
        if not cfg.has_section(section):
            cfg.add_section(section)
            changed = True
        for key, value in options.items():
            if not cfg.has_option(section, key):
                cfg.set(section, key, value)
                changed = True

    if changed:
        print(
            f"[config] В {CONFIG_PATH} не хватает некоторых секций/ключей. "
            f"Недостающие значения взяты по умолчанию."
        )

    return cfg


config = _load_config()

# ---------------------------------------------------------------------------
# Публичные константы, использующиеся в других модулях
# ---------------------------------------------------------------------------
LOG_LEVEL = config.get("App", "log_level", fallback="INFO")
