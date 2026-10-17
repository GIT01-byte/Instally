import os
import sys
import subprocess
import threading
import shutil
import traceback
import re
from pathlib import Path
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger

# ---------------------------------------------------------------------------
# Кэш найденного пути к choco.exe
# ---------------------------------------------------------------------------
_CHOCO_EXE_CACHE: str | None = None


# ---------------------------------------------------------------------------
# Кодировка вывода
# ---------------------------------------------------------------------------
def _get_console_encoding() -> str:
    try:
        import locale

        enc = locale.getpreferredencoding(False)
        if enc:
            return enc
    except Exception:
        pass
    return "utf-8"


# ---------------------------------------------------------------------------
# Поиск и установка системного choco.exe
# ---------------------------------------------------------------------------
def _find_system_choco() -> str | None:
    """Ищет choco.exe в PATH и в стандартной папке установки Chocolatey."""
    choco = shutil.which("choco")
    if choco:
        return choco

    default = Path(r"C:\ProgramData\chocolatey\bin\choco.exe")
    if default.exists():
        return str(default)

    return None


def _install_choco_via_powershell() -> str:
    """Ставит системный Chocolatey официальным скриптом."""
    logger.info("[Choco] Chocolatey не найден. Устанавливаю системный...")

    install_cmd = (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "[System.Net.ServicePointManager]::SecurityProtocol = "
        "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        "iex ((New-Object System.Net.WebClient).DownloadString("
        "'https://community.chocolatey.org/install.ps1'))"
    )

    # Скрываем окно PowerShell
    CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

    process = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            install_cmd,
        ],
        capture_output=True,
        text=True,
        encoding=_get_console_encoding(),
        errors="replace",
        creationflags=CREATE_NO_WINDOW,
    )

    if process.returncode != 0:
        logger.error(
            f"[Choco] Установка Chocolatey завершилась с кодом "
            f"{process.returncode}.\nSTDOUT: {process.stdout}\nSTDERR: {process.stderr}"
        )
        raise RuntimeError(
            "Не удалось установить Chocolatey. Проверьте подключение к интернету "
            "и права администратора."
        )

    choco = _find_system_choco()
    if not choco:
        raise RuntimeError(
            "Chocolatey установлен, но choco.exe не найден в PATH. "
            "Перезапустите приложение."
        )

    logger.info(f"[Choco] Chocolatey установлен: {choco}")
    return choco


def ensure_choco() -> str:
    """
    Возвращает путь к системному choco.exe.
    Порядок: кэш -> PATH -> ProgramData -> установка через PowerShell.
    """
    global _CHOCO_EXE_CACHE

    if _CHOCO_EXE_CACHE:
        return _CHOCO_EXE_CACHE

    choco = _find_system_choco()
    if choco:
        logger.info(f"[Choco] Использую системный choco.exe: {choco}")
        _CHOCO_EXE_CACHE = choco
        return choco

    installed = _install_choco_via_powershell()
    _CHOCO_EXE_CACHE = installed
    return installed


# ---------------------------------------------------------------------------
# Ядро: запуск одной команды choco для ОДНОГО пакета
# ---------------------------------------------------------------------------
def _run_choco_with_logs(
    command_args: list[str],
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    package_label: str = "",
    package_index: int = 1,
    package_total: int = 1,
) -> int:
    """
    Фоновый запуск choco.exe. Никаких PowerShell-обёрток:
    системный choco.exe сам умеет настраивать PSModulePath.
    """
    current_thread_name = threading.current_thread().name
    prefix = f"[{package_index}/{package_total}] {package_label}".strip()

    logger.info(
        f"Инициализация фонового потока {current_thread_name} для обработки Choco."
    )
    logger.info(f"Переданные аргументы для Choco ({prefix}): {command_args}")

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        if text_line:
            ttk_log_widget.after(0, lambda t=text_line: ttk_log_widget.config(text=t))
        if percent_value is not None:
            ttk_log_widget.after(
                0, lambda v=percent_value: ttk_progress_bar.config(value=v)
            )

    try:
        choco_exe = ensure_choco()

        if not os.path.exists(choco_exe):
            error_msg = f"choco.exe отсутствует по пути: {choco_exe}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        full_command = [choco_exe] + command_args
        logger.info(f"Полная команда: {' '.join(full_command)}")

        update_ui_text(f"{prefix}: Запуск команды: {' '.join(command_args)}")

        # Скрываем окно консоли
        CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding=_get_console_encoding(),
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )

        progress_re = re.compile(r"(\d+)\s*%")

        for line in process.stdout:  # type: ignore
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            if "Progress" in cleaned_line:
                m = progress_re.search(cleaned_line)
                if m:
                    try:
                        percent_int = int(m.group(1))
                        update_ui_text(
                            text_line=f"{prefix} [Choco]: {cleaned_line}",
                            percent_value=percent_int,
                        )
                        continue
                    except ValueError:
                        pass
                update_ui_text(text_line=f"{prefix} [Choco]: {cleaned_line}")
                continue

            update_ui_text(text_line=f"{prefix} [Choco]: {cleaned_line}")
            logger.info(f"[Choco Engine Output] {prefix}: {cleaned_line}")

        process.wait()

        rc = process.returncode
        rc_display = rc
        if rc is not None and rc >= 2**31:
            rc_display = rc - 2**32
        logger.info(
            f"Процесс Choco завершил работу с кодом возврата: {rc_display} ({prefix})"
        )
        return rc if rc is not None else -1

    except Exception as e:
        error_type, error_value, error_tb = sys.exc_info()
        summary = traceback.extract_tb(error_tb)[-1]  # type: ignore
        line_number = summary.lineno
        func_name = summary.name

        detailed_error = (
            f"\n=== КРИТИЧЕСКАЯ ОШИБКА ДВИЖКА ===\n"
            f"Тип исключения: {error_type.__name__}\n"  # type: ignore
            f"Описание ошибки: {str(e)}\n"
            f"Локация сбоя: файл {os.path.basename(__file__)}, "
            f"функция '{func_name}', строка {line_number}\n"
            f"Входные аргументы при падении: {command_args}\n"
            f"Контекст: {prefix}\n"
            f"Полный Traceback сбоя:\n{traceback.format_exc()}"
            f"================================="
        )
        logger.critical(detailed_error)

        ttk_log_widget.after(
            0,
            lambda ln=line_number, pkg=package_label: ttk_log_widget.config(
                text=(
                    f"Критическая ошибка движка на пакете {pkg}!\n"
                    f"Сбой зафиксирован на строке {ln}.\n"
                    f"Детали сохранены в логе."
                )
            ),
        )
        return -1


# ---------------------------------------------------------------------------
# Публичный API
# ---------------------------------------------------------------------------
def choco_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    choco_args: Optional[List[str]] = None,
    thread_name: str = "ChocoWorker",
) -> threading.Thread:
    """Запускает команды Chocolatey ПООЧЕРЁДНО для каждого пакета."""
    packages_list = list(packages) if packages else []
    choco_args_list = list(choco_args) if choco_args else []

    if "-y" not in choco_args_list and "--yes" not in choco_args_list:
        choco_args_list.append("-y")

    if "-pre" not in choco_args_list:
        choco_args_list.append("-pre")

    if "--ignore-powershell-home" not in choco_args_list:
        choco_args_list.append("--ignore-powershell-home")

    def worker():
        try:
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Проверяю наличие Chocolatey...")
            )
            ensure_choco()
        except Exception as e:
            logger.critical(f"[Choco] Не удалось подготовить Chocolatey: {e}")
            ttk_log_widget.after(
                0,
                lambda msg=str(e): ttk_log_widget.config(
                    text=f"Не удалось установить Chocolatey:\n{msg}"
                ),
            )
            # Сохраняем ошибку в поток, чтобы фасад знал
            choco_thread.failed_packages = packages_list
            return

        total = len(packages_list)

        try:
            ttk_progress_bar.after(
                0,
                lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0),
            )
        except Exception:
            pass

        if total == 0:
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Список пакетов пуст.")
            )
            choco_thread.failed_packages = []
            return

        success_count = 0
        fail_count = 0
        failed_packages = []  # <--- Список упавших пакетов

        for i, package in enumerate(packages_list, start=1):
            full_command = [action, package] + choco_args_list

            ttk_log_widget.after(
                0,
                lambda i=i, p=package, t=total: ttk_log_widget.config(
                    text=f"[{i}/{t}] Обработка пакета: {p}"
                ),
            )

            rc = _run_choco_with_logs(
                command_args=full_command,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
            )

            if rc in (0, 3010):
                success_count += 1
                logger.info(f"Пакет '{package}' обработан успешно ({i}/{total}).")
            else:
                fail_count += 1
                failed_packages.append(package)  # <--- Запоминаем упавший пакет
                logger.warning(
                    f"Пакет '{package}' завершился с кодом {rc} ({i}/{total})."
                )

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Готово. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

        # Сохраняем упавшие пакеты в поток
        choco_thread.failed_packages = failed_packages

    choco_thread = threading.Thread(
        target=worker,
        daemon=True,
        name=thread_name,
    )
    choco_thread.start()
    return choco_thread


# ---------------------------------------------------------------------------
# Очистка кеша
# ---------------------------------------------------------------------------
def clear_choco_cache():
    """
    Чистит кэш системного Chocolatey штатной командой choco cache remove.
    """
    try:
        choco_exe = ensure_choco()
    except Exception as e:
        logger.error(f"[Cache Remover] Chocolatey недоступен: {e}")
        return

    logger.info("[Cache Remover] Очистка кэша Chocolatey...")
    try:
        CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
        result = subprocess.run(
            [choco_exe, "cache", "remove", "--all", "-y"],
            capture_output=True,
            text=True,
            encoding=_get_console_encoding(),
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )
        if result.returncode == 0:
            logger.info("[Cache Remover] Очистка кэша завершена успешно.")
        else:
            logger.error(
                f"[Cache Remover] choco cache remove вернул код "
                f"{result.returncode}: {result.stderr.strip()}"
            )
    except Exception as e:
        logger.error(f"[Cache Remover] Не удалось очистить кэш: {e}")
