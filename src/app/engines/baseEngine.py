import os
import sys
import subprocess
import threading
import traceback
import re
import time
import queue
from tkinter import Label, ttk
from typing import List, Dict

from utils.logging import logger


class InstallEngine:
    """Базовый класс для всех пакетных менеджеров."""

    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def _get_console_encoding(self) -> str:
        try:
            import locale

            enc = locale.getpreferredencoding(False)
            if enc:
                return enc
        except Exception:
            pass
        return "utf-8"

    def _update_ui(
        self,
        text: str | None,
        percent: int | None,
        log_widget: Label,
        progress_bar: ttk.Progressbar,
    ):
        if text:
            log_widget.after(0, lambda t=text: log_widget.config(text=t))
        if percent is not None:
            progress_bar.after(0, lambda v=percent: progress_bar.config(value=v))

    def run_process(
        self,
        cmd: List[str],
        log_widget: Label,
        progress_bar: ttk.Progressbar,
        package_label: str = "",
        package_index: int = 1,
        package_total: int = 1,
        progress_regex: str = r"(\d+)\s*%",
        error_patterns: List[str] = None,
        already_installed_patterns: List[str] = None,
        env: Dict[str, str] = None,
        cancel_event: threading.Event = None,
    ) -> int:
        prefix = f"[{package_index}/{package_total}] {package_label}".strip()
        logger.info(f"Запуск ({prefix}): {' '.join(cmd)}")
        self._update_ui(f"{prefix}: Запуск...", None, log_widget, progress_bar)

        try:
            CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding=self._get_console_encoding(),
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
                env=env,
            )

            output_queue = queue.Queue()

            def enqueue_output(out, q):
                try:
                    for line in iter(out.readline, ""):
                        q.put(line)
                    out.close()
                except Exception:
                    pass

            t_reader = threading.Thread(
                target=enqueue_output, args=(process.stdout, output_queue), daemon=True
            )
            t_reader.start()

            progress_re = re.compile(progress_regex)
            compiled_errors = (
                [re.compile(p, re.IGNORECASE) for p in error_patterns]
                if error_patterns
                else []
            )
            compiled_already = (
                [re.compile(p, re.IGNORECASE) for p in already_installed_patterns]
                if already_installed_patterns
                else []
            )

            last_activity = time.time()
            has_custom_error = False
            is_already_installed = False

            while True:
                # Проверка на отмену
                if cancel_event and cancel_event.is_set():
                    logger.warning(
                        f"Задача отменена пользователем. Убиваем процесс {prefix}."
                    )
                    try:
                        process.kill()
                        process.wait(timeout=3)
                        if process.stdout:
                            process.stdout.close()
                    except Exception:
                        pass
                    return -1

                try:
                    line = output_queue.get(timeout=1.0)
                    last_activity = time.time()

                    cleaned_line = line.replace("\r", "").strip()
                    if not cleaned_line:
                        continue

                    if "winget" in cmd[0].lower() or "snap" in cmd[0].lower():
                        cleaned_line = re.sub(
                            r"[█▓▒░\\|/\-]+", "", cleaned_line
                        ).strip()
                        if not cleaned_line:
                            continue

                    if compiled_already and any(
                        p.search(cleaned_line) for p in compiled_already
                    ):
                        is_already_installed = True
                        self._update_ui(
                            f"{prefix} [УЖЕ УСТАНОВЛЕНО]: {cleaned_line}",
                            None,
                            log_widget,
                            progress_bar,
                        )
                        continue

                    if compiled_errors and any(
                        p.search(cleaned_line) for p in compiled_errors
                    ):
                        has_custom_error = True
                        self._update_ui(
                            f"{prefix} [ОШИБКА]: {cleaned_line}",
                            None,
                            log_widget,
                            progress_bar,
                        )
                        continue

                    m = progress_re.search(cleaned_line)
                    if m:
                        try:
                            percent = int(m.group(1))
                            self._update_ui(
                                f"{prefix}: {cleaned_line}",
                                percent,
                                log_widget,
                                progress_bar,
                            )
                            continue
                        except ValueError:
                            pass

                    self._update_ui(
                        f"{prefix}: {cleaned_line}", None, log_widget, progress_bar
                    )

                except queue.Empty:
                    if (
                        process.poll() is not None
                        and not t_reader.is_alive()
                        and output_queue.empty()
                    ):
                        break

                    if time.time() - last_activity > self.timeout:
                        logger.error(
                            f"Таймаут бездействия ({self.timeout} сек). Убиваем {prefix}."
                        )
                        self._update_ui(
                            f"{prefix}: ТАЙМАУТ...", None, log_widget, progress_bar
                        )
                        try:
                            process.kill()
                            process.wait(timeout=5)
                            if process.stdout:
                                process.stdout.close()
                        except Exception:
                            pass
                        return -1

            process.wait()
            rc = process.returncode

            if has_custom_error and rc in (0, None):
                rc = -404
            elif is_already_installed and rc in (0, None):
                rc = -2

            return rc if rc is not None else -1

        except Exception as e:
            logger.critical(f"Ошибка процесса {prefix}: {e}\n{traceback.format_exc()}")
            return -1
