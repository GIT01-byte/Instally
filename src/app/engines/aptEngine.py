import os
import sys
import subprocess
import threading
import traceback
import re
from pathlib import Path
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger

# ---------------------------------------------------------------------------
# Пути к apt и кэшу пакетов
# ---------------------------------------------------------------------------
APT_EXE = "/usr/bin/apt-get"
APT_CACHE_DIR = Path("/var/cache/apt/archives")


# ---------------------------------------------------------------------------
# Кодировка вывода apt — на Linux всегда UTF-8
# ---------------------------------------------------------------------------
def _get_console_encoding() -> str:
    return "utf-8"


# ---------------------------------------------------------------------------
# Ядро: запуск одной команды apt для ОДНОГО пакета
# ---------------------------------------------------------------------------
def _run_apt_with_logs(
    command_args: list[str],
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    package_label: str = "",
    package_index: int = 1,
    package_total: int = 1,
) -> int:
    """
    Фоновый запуск apt-get с выводом логов на экран и в файл.

    Возвращает код возврата процесса:
        0       — успех,
        иное    — ошибка (типичные: 1 — общая, 100 — пакет не найден).
    """
    current_thread_name = threading.current_thread().name
    prefix = f"[{package_index}/{package_total}] {package_label}".strip()

    logger.info(
        f"Инициализация фонового потока {current_thread_name} для обработки APT."
    )
    logger.info(f"Переданные аргументы для APT ({prefix}): {command_args}")

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        """Обновление интерфейса из фонового потока через .after()."""
        if text_line:
            ttk_log_widget.after(0, lambda t=text_line: ttk_log_widget.config(text=t))
        if percent_value is not None:
            ttk_log_widget.after(
                0, lambda v=percent_value: ttk_progress_bar.config(value=v)
            )

    try:
        if not os.path.exists(APT_EXE):
            error_msg = f"apt-get не найден по пути: {APT_EXE}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        full_command = [APT_EXE] + command_args
        logger.info(f"Полная системная команда: {' '.join(full_command)}")

        update_ui_text(f"{prefix}: Запуск команды: {' '.join(command_args)}")

        # Окружение: DEBIAN_FRONTEND=noninteractive — чтобы apt не задавал
        # интерактивных вопросов (аналог -y у choco).
        env = os.environ.copy()
        env["DEBIAN_FRONTEND"] = "noninteractive"
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"

        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding=_get_console_encoding(),
            errors="replace",
            env=env,
        )

        # apt/dpkg пишут прогресс вроде "Progress: [ 45%]" или "[ 45%]"
        progress_re = re.compile(r"\[\s*(\d+)\s*%\]")

        for line in process.stdout:  # type: ignore
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            # Обработка строк прогресса
            m = progress_re.search(cleaned_line)
            if m:
                try:
                    percent_int = int(m.group(1))
                    update_ui_text(
                        text_line=f"{prefix} [APT]: {cleaned_line}",
                        percent_value=percent_int,
                    )
                    # В файл прогресс не пишем — только в UI.
                    continue
                except ValueError:
                    pass

            update_ui_text(text_line=f"{prefix} [APT]: {cleaned_line}")
            logger.info(f"[APT Engine Output] {prefix}: {cleaned_line}")

        process.wait()

        rc = process.returncode if process.returncode is not None else -1
        logger.info(f"Процесс APT завершил работу с кодом возврата: {rc} ({prefix})")
        return rc

    except Exception as e:
        error_type, error_value, error_tb = sys.exc_info()
        summary = traceback.extract_tb(error_tb)[-1]  # type: ignore
        line_number = summary.lineno
        func_name = summary.name

        detailed_error = (
            f"\n=== КРИТИЧЕСКАЯ ОШИБКА ДВИЖКА APT ===\n"
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
                    f"Критическая ошибка APT на пакете {pkg}!\n"
                    f"Сбой зафиксирован на строке {ln}.\n"
                    f"Детали сохранены в логе."
                )
            ),
        )
        return -1


# ---------------------------------------------------------------------------
# Публичный API: последовательный запуск apt по каждому пакету
# ---------------------------------------------------------------------------
def apt_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    apt_args: Optional[List[str]] = None,
    thread_name: str = "AptWorker",
) -> threading.Thread:
    """
    Универсальный API-метод: запускает команды apt ПООЧЕРЁДНО для каждого пакета.

    Пример: action='install', packages=['7zip','vlc','firefox']
        -> apt-get install 7zip -y
        -> apt-get install vlc -y
        -> apt-get install firefox -y

    Для action='upgrade' пакеты игнорируются, выполняется:
        -> apt-get update
        -> apt-get upgrade -y

    Возвращает объект запущенного потока (не блокирует UI).
    """
    packages_list = list(packages) if packages else []
    apt_args_list = list(apt_args) if apt_args else []

    # Защита 1: Автосогласие
    if "-y" not in apt_args_list and "--yes" not in apt_args_list:
        apt_args_list.append("-y")

    # Защита 2: Неинтерактивный режим на уровне аргументов
    if "-o" not in apt_args_list:
        apt_args_list.extend(
            [
                "-o",
                "Dpkg::Options::=--force-confnew",
                "-o",
                "Dpkg::Options::=--force-confdef",
            ]
        )

    def worker():
        total = len(packages_list)
        is_upgrade = action == "upgrade"

        # Настроим прогресс-бар под количество пакетов
        try:
            ttk_progress_bar.after(
                0,
                lambda: ttk_progress_bar.configure(
                    maximum=max(total if not is_upgrade else 2, 1), value=0
                ),
            )
        except Exception:
            pass

        # --- Ветка обновления всей системы ---
        if is_upgrade:
            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(
                    text="[1/2] Обновление индексов пакетов (apt-get update)..."
                ),
            )
            _run_apt_with_logs(
                command_args=["update"],
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label="update",
                package_index=1,
                package_total=2,
            )
            ttk_progress_bar.after(0, lambda: ttk_progress_bar.config(value=1))

            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(
                    text="[2/2] Обновление всех пакетов (apt-get upgrade)..."
                ),
            )
            rc = _run_apt_with_logs(
                command_args=["upgrade"] + apt_args_list,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label="upgrade",
                package_index=2,
                package_total=2,
            )
            ttk_progress_bar.after(0, lambda: ttk_progress_bar.config(value=2))

            if rc in (0, 3010):
                summary = "Готово. Система обновлена."
            else:
                summary = f"Готово. Обновление завершилось с кодом {rc}."
            logger.info(summary)
            ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))
            return

        # --- Ветка установки пакетов ---
        if total == 0:
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Список пакетов пуст.")
            )
            return

        # Перед установкой всегда обновляем индексы — иначе пакет может не найтись.
        ttk_log_widget.after(
            0,
            lambda: ttk_log_widget.config(
                text="Обновление индексов пакетов (apt-get update)..."
            ),
        )
        _run_apt_with_logs(
            command_args=["update"],
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            package_label="update",
            package_index=0,
            package_total=total,
        )

        success_count = 0
        fail_count = 0

        for i, package in enumerate(packages_list, start=1):
            full_command = [action, package] + apt_args_list

            ttk_log_widget.after(
                0,
                lambda i=i, p=package, t=total: ttk_log_widget.config(
                    text=f"[{i}/{t}] Обработка пакета: {p}"
                ),
            )

            rc = _run_apt_with_logs(
                command_args=full_command,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
            )

            if rc == 0:
                success_count += 1
                logger.info(f"Пакет '{package}' обработан успешно ({i}/{total}).")
            else:
                fail_count += 1
                logger.warning(
                    f"Пакет '{package}' завершился с кодом {rc} ({i}/{total})."
                )

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Готово. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    apt_thread = threading.Thread(
        target=worker,
        daemon=True,
        name=thread_name,
    )
    apt_thread.start()
    return apt_thread


# ---------------------------------------------------------------------------
# Очистка кеша apt
# ---------------------------------------------------------------------------
def clear_apt_cache(dir_path: str | None = None):
    """
    Чистит кэш скачанных .deb-пакетов.
    Требует прав root — обычно приложение уже запущено под sudo.
    """
    apt_cache_path = Path(dir_path) if dir_path else APT_CACHE_DIR

    if not apt_cache_path.exists():
        logger.info(
            f"[Cache Remover] Очистка не требуется: "
            f"путь '{apt_cache_path}' не существует."
        )
        return

    logger.info(f"[Cache Remover] Начало удаления кэша APT по пути: {apt_cache_path}")
    try:
        # apt-get clean — штатный способ, не требует ручного rmtree
        result = subprocess.run(
            [APT_EXE, "clean"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            logger.info("[Cache Remover] Удаление кэша APT завершено успешно.")
        else:
            logger.error(
                f"[Cache Remover] apt-get clean вернул код {result.returncode}: "
                f"{result.stderr.strip()}"
            )
    except Exception as e:
        logger.error(f"[Cache Remover] Не удалось очистить кэш APT: {e}")
