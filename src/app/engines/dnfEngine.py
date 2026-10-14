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

DNF_EXE = "/usr/bin/dnf"
DNF_CACHE_DIR = Path("/var/cache/dnf")


def _get_console_encoding() -> str:
    return "utf-8"


def _run_dnf_with_logs(
    command_args: list[str],
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    package_label: str = "",
    package_index: int = 1,
    package_total: int = 1,
) -> int:
    """
    Фоновый запуск dnf с выводом логов на экран и в файл.
    """
    current_thread_name = threading.current_thread().name
    prefix = f"[{package_index}/{package_total}] {package_label}".strip()

    logger.info(
        f"Инициализация фонового потока {current_thread_name} для обработки DNF."
    )
    logger.info(f"Переданные аргументы для DNF ({prefix}): {command_args}")

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        if text_line:
            ttk_log_widget.after(0, lambda t=text_line: ttk_log_widget.config(text=t))
        if percent_value is not None:
            ttk_log_widget.after(
                0, lambda v=percent_value: ttk_progress_bar.config(value=v)
            )

    try:
        if not os.path.exists(DNF_EXE):
            error_msg = f"dnf не найден по пути: {DNF_EXE}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        full_command = [DNF_EXE] + command_args
        logger.info(f"Полная системная команда: {' '.join(full_command)}")

        update_ui_text(f"{prefix}: Запуск команды: {' '.join(command_args)}")

        env = os.environ.copy()
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

        # dnf пишет прогресс вида "[ 45%]" или "[45/120]"
        percent_re = re.compile(r"\[\s*(\d+)\s*%\]")
        count_re = re.compile(r"\[\s*(\d+)\s*/\s*(\d+)\s*\]")

        for line in process.stdout:  # type: ignore
            cleaned_line = line.strip()
            if not cleaned_line:
                continue

            m = percent_re.search(cleaned_line)
            if m:
                try:
                    update_ui_text(
                        text_line=f"{prefix} [DNF]: {cleaned_line}",
                        percent_value=int(m.group(1)),
                    )
                    continue
                except ValueError:
                    pass

            m = count_re.search(cleaned_line)
            if m:
                try:
                    cur, tot = int(m.group(1)), int(m.group(2))
                    if tot > 0:
                        percent_int = int(cur * 100 / tot)
                        update_ui_text(
                            text_line=f"{prefix} [DNF]: {cleaned_line}",
                            percent_value=percent_int,
                        )
                        continue
                except (ValueError, ZeroDivisionError):
                    pass

            update_ui_text(text_line=f"{prefix} [DNF]: {cleaned_line}")
            logger.info(f"[DNF Engine Output] {prefix}: {cleaned_line}")

        process.wait()
        rc = process.returncode if process.returncode is not None else -1
        logger.info(f"Процесс DNF завершил работу с кодом возврата: {rc} ({prefix})")
        return rc

    except Exception as e:
        error_type, _, error_tb = sys.exc_info()
        summary = traceback.extract_tb(error_tb)[-1]  # type: ignore
        line_number = summary.lineno
        func_name = summary.name

        detailed_error = (
            f"\n=== КРИТИЧЕСКАЯ ОШИБКА ДВИЖКА DNF ===\n"
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
                    f"Критическая ошибка DNF на пакете {pkg}!\n"
                    f"Сбой зафиксирован на строке {ln}.\n"
                    f"Детали сохранены в логе."
                )
            ),
        )
        return -1


def dnf_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    dnf_args: Optional[List[str]] = None,
    thread_name: str = "DnfWorker",
) -> threading.Thread:
    """
    Универсальный API: запускает dnf ПООЧЕРЁДНО для каждого пакета.

    action='install', packages=['7zip','vlc']:
        -> dnf install 7zip -y
        -> dnf install vlc -y

    action='upgrade' (packages игнорируются):
        -> dnf upgrade -y
    """
    packages_list = list(packages) if packages else []
    dnf_args_list = list(dnf_args) if dnf_args else []

    if "-y" not in dnf_args_list and "--assumeyes" not in dnf_args_list:
        dnf_args_list.append("-y")

    def worker():
        total = len(packages_list)
        is_upgrade = action == "upgrade"

        try:
            ttk_progress_bar.after(
                0,
                lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0),
            )
        except Exception:
            pass

        # --- Обновление системы ---
        if is_upgrade:
            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(
                    text="Обновление всех пакетов (dnf upgrade)..."
                ),
            )
            rc = _run_dnf_with_logs(
                command_args=["upgrade"] + dnf_args_list,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label="upgrade",
                package_index=1,
                package_total=1,
            )
            ttk_progress_bar.after(0, lambda: ttk_progress_bar.config(value=1))

            if rc == 0:
                summary = "Готово. Система обновлена."
            else:
                summary = f"Готово. Обновление завершилось с кодом {rc}."
            logger.info(summary)
            ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))
            return

        # --- Установка пакетов ---
        if total == 0:
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Список пакетов пуст.")
            )
            return

        success_count = 0
        fail_count = 0

        for i, package in enumerate(packages_list, start=1):
            full_command = [action, package] + dnf_args_list

            ttk_log_widget.after(
                0,
                lambda i=i, p=package, t=total: ttk_log_widget.config(
                    text=f"[{i}/{t}] Обработка пакета: {p}"
                ),
            )

            rc = _run_dnf_with_logs(
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

    dnf_thread = threading.Thread(
        target=worker,
        daemon=True,
        name=thread_name,
    )
    dnf_thread.start()
    return dnf_thread


def clear_dnf_cache(dir_path: str | None = None):
    """
    Чистит кэш dnf штатной командой dnf clean all.
    """
    if not os.path.exists(DNF_EXE):
        logger.info(f"[Cache Remover] dnf не найден: {DNF_EXE}. Пропускаю.")
        return

    logger.info("[Cache Remover] Начало очистки кэша DNF...")
    try:
        result = subprocess.run(
            [DNF_EXE, "clean", "all"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode == 0:
            logger.info("[Cache Remover] Очистка кэша DNF завершена успешно.")
        else:
            logger.error(
                f"[Cache Remover] dnf clean all вернул код {result.returncode}: "
                f"{result.stderr.strip()}"
            )
    except Exception as e:
        logger.error(f"[Cache Remover] Не удалось очистить кэш DNF: {e}")
