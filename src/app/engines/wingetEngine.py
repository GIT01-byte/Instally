import os
import sys
import subprocess
import threading
import shutil
import traceback
import re
import time
import queue
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger

# Таймаут бездействия (в секундах). Если 10 минут нет вывода — убиваем процесс.
WINGET_INACTIVITY_TIMEOUT = 120


def _get_console_encoding() -> str:
    try:
        import locale

        enc = locale.getpreferredencoding(False)
        if enc:
            return enc
    except Exception:
        pass
    return "utf-8"


def _find_winget() -> str | None:
    winget = shutil.which("winget")
    if winget:
        return winget
    appdata = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        path = os.path.join(appdata, r"Microsoft\WindowsApps\winget.exe")
        if os.path.exists(path):
            return path
    return None


def _run_winget_with_logs(
    command_args: list[str],
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    package_label: str = "",
    package_index: int = 1,
    package_total: int = 1,
) -> int:
    current_thread_name = threading.current_thread().name
    prefix = f"[{package_index}/{package_total}] {package_label}".strip()

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        if text_line:
            ttk_log_widget.after(0, lambda t=text_line: ttk_log_widget.config(text=t))
        if percent_value is not None:
            ttk_log_widget.after(
                0, lambda v=percent_value: ttk_progress_bar.config(value=v)
            )

    try:
        winget_exe = _find_winget()
        if not winget_exe:
            raise FileNotFoundError("winget.exe не найден в системе.")

        full_command = [winget_exe] + command_args
        logger.info(f"Полная команда: {' '.join(full_command)}")
        update_ui_text(f"{prefix}: Запуск: {' '.join(command_args)}")

        CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,  # <--- Важно: чтобы не ждал ввода
            text=True,
            encoding=_get_console_encoding(),
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )

        # Очередь для чтения вывода в отдельном потоке
        output_queue = queue.Queue()

        def enqueue_output(out, q):
            try:
                for line in iter(out.readline, ""):
                    q.put(line)
                out.close()
            except Exception:
                pass

        # Запускаем поток чтения
        t_reader = threading.Thread(
            target=enqueue_output, args=(process.stdout, output_queue), daemon=True
        )
        t_reader.start()

        progress_re = re.compile(r"(\d+)\s*%")
        last_activity = time.time()

        # Читаем из очереди с таймаутом
        while True:
            try:
                # Ждем строку 1 секунду
                line = output_queue.get(timeout=1.0)
                last_activity = (
                    time.time()
                )  # Сбрасываем таймер, так как есть активность

                cleaned_line = line.strip()
                if not cleaned_line:
                    continue

                cleaned_line = re.sub(r"[█▓▒░]+", "", cleaned_line).strip()
                if not cleaned_line:
                    continue

                m = progress_re.search(cleaned_line)
                if m:
                    try:
                        percent_int = int(m.group(1))
                        update_ui_text(
                            text_line=f"{prefix} [Winget]: {cleaned_line}",
                            percent_value=percent_int,
                        )
                        continue
                    except ValueError:
                        pass

                update_ui_text(text_line=f"{prefix} [Winget]: {cleaned_line}")
                logger.info(f"[Winget Engine Output] {prefix}: {cleaned_line}")

            except queue.Empty:
                # Если очередь пуста, проверяем: процесс жив? поток чтения жив?
                if (
                    process.poll() is not None
                    and not t_reader.is_alive()
                    and output_queue.empty()
                ):
                    break  # Процесс успешно завершился

                # Проверяем таймаут бездействия
                if time.time() - last_activity > WINGET_INACTIVITY_TIMEOUT:
                    logger.error(
                        f"Таймаут бездействия ({WINGET_INACTIVITY_TIMEOUT} сек). Убиваем процесс {prefix}."
                    )
                    update_ui_text(
                        text_line=f"{prefix} [Winget]: ТАЙМАУТ. Прерывание установки..."
                    )
                    try:
                        process.kill()
                    except Exception:
                        pass
                    return -1

        process.wait()
        rc = process.returncode

        rc_display = rc
        if rc is not None and rc >= 2**31:
            rc_display = rc - 2**32

        logger.info(f"Процесс Winget завершил работу с кодом: {rc_display} ({prefix})")
        return rc if rc is not None else -1

    except Exception as e:
        error_tb = sys.exc_info()[2]
        summary = traceback.extract_tb(error_tb)[-1]  # type: ignore
        detailed_error = (
            f"\n=== ОШИБКА WINGET ===\n"
            f"Описание: {str(e)}\n"
            f"Локация: строка {summary.lineno}\n"
            f"Traceback:\n{traceback.format_exc()}"
            f"====================="
        )
        logger.critical(detailed_error)
        update_ui_text(
            text_line=f"Ошибка Winget на пакете {package_label} (детали в логе)"
        )
        return -1


def winget_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    winget_args: Optional[List[str]] = None,
    thread_name: str = "WingetWorker",
) -> threading.Thread:
    packages_list = list(packages) if packages else []

    default_args = [
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
    ]
    cmd_args = default_args + (list(winget_args) if winget_args else [])

    def worker():
        total = len(packages_list)
        if total == 0:
            return

        try:
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0)
            )
        except Exception:
            pass

        success_count = 0
        fail_count = 0

        for i, package in enumerate(packages_list, start=1):
            cmd = [action]
            cmd.extend(["--id", package])
            cmd.extend(cmd_args)

            rc = _run_winget_with_logs(
                command_args=cmd,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
            )

            if rc in (0, 3010):
                success_count += 1
                logger.info(f"Пакет '{package}' установлен через Winget ({i}/{total}).")
            else:
                fail_count += 1
                logger.warning(
                    f"Пакет '{package}' не установлен через Winget. Код: {rc}"
                )

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Winget завершен. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    winget_thread = threading.Thread(
        target=worker,
        daemon=True,
        name=thread_name,
    )
    winget_thread.start()
    return winget_thread
