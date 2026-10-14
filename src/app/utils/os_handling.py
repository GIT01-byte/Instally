import ctypes
import os
import platform
import subprocess
import sys

from utils.logging import logger


def _is_admin_windows() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _is_admin_unix() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False


def _relaunch_as_admin_windows() -> None:
    """Запускает текущий exe заново через UAC и завершает текущий процесс."""
    params = subprocess.list2cmdline(sys.argv[1:])
    ret = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, params, None, 1
    )
    # ret <= 32 означает ошибку (пользователь отклонил UAC и т.п.)
    if ret <= 32:
        logger.error(
            f"[WINDOWS] Не удалось получить права администратора (код {ret}). "
            f"Возможно, пользователь отклонил запрос UAC."
        )
    else:
        logger.info("[WINDOWS] Права администратора запрошены, перезапуск...")
    # Завершаем текущий процесс, чтобы не было двух окон
    sys.exit(0)


def get_admin_permisions() -> None:
    """
    Гарантирует, что приложение запущено с правами администратора.
    Windows — UAC, Linux/macOS — root.
    На Windows при недостатке прав перезапускает приложение и завершает текущий процесс.
    """
    system = platform.system().lower()

    if system == "windows":
        if _is_admin_windows():
            logger.info("[WINDOWS] Программа уже запущена с правами администратора")
            return
        _relaunch_as_admin_windows()
        return

    if system in ("linux", "darwin"):
        if _is_admin_unix():
            logger.info(f"[{system.upper()}] Программа уже запущена с правами root")
            return
        # На Linux/macOS самопроизвольный перезапуск под sudo — плохая идея:
        # нужен пароль, и пользователь не ждёт, что GUI сам спросит его.
        logger.error(
            f"[{system.upper()}] Программа не запущена с правами root. "
            f"Запустите через sudo или от имени root."
        )
        sys.exit(1)

    logger.error(f"[{system.upper()}] Неизвестная ОС, не могу проверить права.")
    sys.exit(1)
