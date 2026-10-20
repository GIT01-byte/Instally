import os
import sys
import subprocess
import threading
import traceback
import re
import time
import queue
from tkinter import Label, ttk
from typing import List, Optional, Dict

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
        env: Dict[str, str] = None,
    ) -> int:
        """Запускает процесс, парсит вывод и возвращает код возврата."""
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
            last_activity = time.time()
            has_custom_error = False

            while True:
                try:
                    # Ждем строку с таймаутом 1 сек (чтобы проверять общий таймаут)
                    line = output_queue.get(timeout=1.0)
                    last_activity = time.time()

                    cleaned_line = line.replace("\r", "").strip()
                    if not cleaned_line:
                        continue

                    # Очистка от мусорных символов прогресс-баров (winget/snap)
                    if "winget" in cmd[0].lower() or "snap" in cmd[0].lower():
                        cleaned_line = re.sub(
                            r"[█▓▒░\\|/\-]+", "", cleaned_line
                        ).strip()
                        if not cleaned_line:
                            continue

                    # Проверка на кастомные ошибки (например, 404 от choco)
                    if compiled_errors and any(
                        p.search(cleaned_line) for p in compiled_errors
                    ):
                        has_custom_error = True
                        logger.error(f"Ошибка загрузки ({prefix}): {cleaned_line}")
                        self._update_ui(
                            f"{prefix} [ОШИБКА]: {cleaned_line}",
                            None,
                            log_widget,
                            progress_bar,
                        )
                        continue

                    # Парсинг прогресса
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

                    # Обычный вывод
                    self._update_ui(
                        f"{prefix}: {cleaned_line}", None, log_widget, progress_bar
                    )
                    logger.info(f"Вывод ({prefix}): {cleaned_line}")

                except queue.Empty:
                    # Процесс завершился и вывод закончился
                    if (
                        process.poll() is not None
                        and not t_reader.is_alive()
                        and output_queue.empty()
                    ):
                        break

                    # ПРОВЕРКА ТАЙМАУТА (120 секунд)
                    if time.time() - last_activity > self.timeout:
                        logger.error(
                            f"Таймаут бездействия ({self.timeout} сек). Убиваем {prefix}."
                        )
                        self._update_ui(
                            f"{prefix}: ТАЙМАУТ. Прерывание...",
                            None,
                            log_widget,
                            progress_bar,
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

            # Если процесс вернул 0, но были ошибки в тексте
            if has_custom_error and rc in (0, None):
                logger.warning(
                    f"Пакет {package_label} вернул 0, но были ошибки в логах. Код изменен на -404."
                )
                rc = -404

            rc_display = rc if rc is not None else -1
            if rc_display >= 2**31:
                rc_display -= 2**32

            logger.info(f"Процесс завершил работу с кодом: {rc_display} ({prefix})")
            return rc if rc is not None else -1

        except Exception as e:
            logger.critical(f"Ошибка процесса {prefix}: {e}\n{traceback.format_exc()}")
            self._update_ui(
                f"Критическая ошибка на пакете {package_label}",
                None,
                log_widget,
                progress_bar,
            )
            return -1
