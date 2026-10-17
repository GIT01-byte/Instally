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
from typing import List, Union, Tuple, Optional

from utils.logging import logger

# Таймаут бездействия для Snap (в секундах)
SNAP_INACTIVITY_TIMEOUT = 120


def _get_console_encoding() -> str:
    return "utf-8"


def _find_snap() -> str | None:
    """Ищет исполняемый файл snap в системе."""
    snap = shutil.which("snap")
    if snap:
        return snap
    # Стандартный путь в Ubuntu
    if os.path.exists("/usr/bin/snap"):
        return "/usr/bin/snap"
    return None


def _run_snap_with_logs(
    command_args: list[str],
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    package_label: str = "",
    package_index: int = 1,
    package_total: int = 1,
) -> int:
    """Фоновый запуск snap с логированием в UI и таймаутом бездействия."""
    prefix = f"[{package_index}/{package_total}] {package_label}".strip()

    def update_ui_text(text_line: str | None, percent_value: int | None = None):
        if text_line:
            ttk_log_widget.after(0, lambda t=text_line: ttk_log_widget.config(text=t))
        if percent_value is not None:
            ttk_log_widget.after(
                0, lambda v=percent_value: ttk_progress_bar.config(value=v)
            )

    try:
        snap_exe = _find_snap()
        if not snap_exe:
            raise FileNotFoundError("snap не найден в системе. Установите snapd.")

        full_command = [snap_exe] + command_args
        logger.info(f"Полная команда: {' '.join(full_command)}")
        update_ui_text(f"{prefix}: Запуск: {' '.join(command_args)}")

        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            encoding=_get_console_encoding(),
            errors="replace",
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

        # Snap пишет прогресс через \r (возврат каретки). Очищаем его.
        progress_re = re.compile(r"(\d+)\s*%")
        last_activity = time.time()

        while True:
            try:
                # Ждем строку 1 секунду
                line = output_queue.get(timeout=1.0)
                last_activity = time.time()  # Сбрасываем таймер активности

                # Удаляем возврат каретки и лишние пробелы
                cleaned_line = line.replace("\r", "").strip()
                if not cleaned_line:
                    continue

                # Убираем мусорные символы спиннера (\, |, /, -)
                cleaned_line = re.sub(r"[\\|/\-]+", "", cleaned_line).strip()
                if not cleaned_line:
                    continue

                # Ищем проценты
                m = progress_re.search(cleaned_line)
                if m:
                    try:
                        percent_int = int(m.group(1))
                        update_ui_text(
                            text_line=f"{prefix} [Snap]: {cleaned_line}",
                            percent_value=percent_int,
                        )
                        continue
                    except ValueError:
                        pass

                update_ui_text(text_line=f"{prefix} [Snap]: {cleaned_line}")
                logger.info(f"[Snap Engine Output] {prefix}: {cleaned_line}")

            except queue.Empty:
                # Если очередь пуста, проверяем: процесс жив? поток чтения жив?
                if (
                    process.poll() is not None
                    and not t_reader.is_alive()
                    and output_queue.empty()
                ):
                    break  # Процесс успешно завершился

                # Проверяем таймаут бездействия
                if time.time() - last_activity > SNAP_INACTIVITY_TIMEOUT:
                    logger.error(
                        f"Таймаут бездействия Snap ({SNAP_INACTIVITY_TIMEOUT} сек). "
                        f"Убиваем процесс {prefix}."
                    )
                    update_ui_text(
                        text_line=f"{prefix} [Snap]: ТАЙМАУТ. Прерывание установки..."
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

        logger.info(f"Процесс Snap завершил работу с кодом: {rc_display} ({prefix})")
        return rc if rc is not None else -1

    except Exception as e:
        logger.critical(f"Ошибка Snap: {e}\n{traceback.format_exc()}")
        update_ui_text(
            text_line=f"Ошибка Snap на пакете {package_label} (детали в логе)"
        )
        return -1


def snap_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[Union[str, Tuple[str, bool]]]] = None,
    snap_args: Optional[List[str]] = None,
    thread_name: str = "SnapWorker",
) -> threading.Thread:
    """
    Запускает установку пакетов через Snap.
    packages может быть списком строк ["code", "vlc"] или кортежей [("code", True), ("vlc", False)],
    где второй элемент кортежа — это флаг необходимости --classic.
    """

    # Нормализуем входной список в список кортежей (name, is_classic)
    normalized_packages = []
    if packages:
        for p in packages:
            if isinstance(p, tuple):
                normalized_packages.append(p)
            else:
                normalized_packages.append((p, False))

    args_list = list(snap_args) if snap_args else []

    def worker():
        total = len(normalized_packages)
        if total == 0:
            threading.current_thread().failed_packages = []
            return

        try:
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0)
            )
        except Exception:
            pass

        success_count = 0
        fail_count = 0
        failed_packages = []

        for i, (package_name, is_classic) in enumerate(normalized_packages, start=1):
            cmd = ["install", package_name]

            # Добавляем флаг --classic, если он передан из CSV
            if is_classic and "--classic" not in args_list:
                cmd.append("--classic")

            cmd.extend(args_list)

            rc = _run_snap_with_logs(
                command_args=cmd,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                package_label=package_name,
                package_index=i,
                package_total=total,
            )

            if rc == 0:
                success_count += 1
                logger.info(
                    f"Пакет '{package_name}' установлен через Snap ({i}/{total})."
                )
            else:
                fail_count += 1
                failed_packages.append(package_name)
                logger.warning(
                    f"Пакет '{package_name}' не установлен через Snap. Код: {rc}"
                )

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = (
            f"Snap завершен. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        )
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

        # Сохраняем список упавших пакетов в текущий поток (для отчетности)
        threading.current_thread().failed_packages = failed_packages

    snap_thread = threading.Thread(
        target=worker,
        daemon=True,
        name=thread_name,
    )
    snap_thread.start()
    return snap_thread
