import os
import sys
import urllib.request
import urllib.error
import zipfile
import threading
from pathlib import Path
from tkinter import Label, ttk
from utils.logging import logger


def download_and_extract_zip(
    url: str,
    app_name: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    cancel_event: threading.Event = None,
) -> threading.Thread:

    def worker():
        downloads_dir = Path.home() / "Downloads" / "Instally_Apps" / app_name
        zip_path = downloads_dir / f"{app_name}.zip"

        try:
            # 1. Создаем папку
            downloads_dir.mkdir(parents=True, exist_ok=True)

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Скачивание {app_name}...")
            )
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=100, value=0)
            )

            # 2. Скачивание
            def report_hook(block_num, block_size, total_size):
                if cancel_event and cancel_event.is_set():
                    raise InterruptedError("Скачивание отменено пользователем.")
                if total_size > 0:
                    read_so_far = block_num * block_size
                    percent = int(read_so_far * 100 / total_size)
                    ttk_progress_bar.after(
                        0, lambda p=percent: ttk_progress_bar.config(value=p)
                    )

            urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

            # Если отменили сразу после скачивания
            if cancel_event and cancel_event.is_set():
                raise InterruptedError("Скачивание отменено пользователем.")

            # 3. Распаковка
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Распаковка архива...")
            )
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(downloads_dir)

            # 4. Завершение
            os.remove(zip_path)
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Готово! Папка открыта.")
            )

            if sys.platform == "win32":
                os.startfile(downloads_dir)
            elif sys.platform == "darwin":
                os.system(f'open "{downloads_dir}"')
            else:
                os.system(f'xdg-open "{downloads_dir}"')

        # --- ОБРАБОТКА ОШИБОК ---

        except InterruptedError:
            logger.info(f"[ZIP] Скачивание '{app_name}' прервано пользователем.")
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Отменено пользователем.")
            )
            # Удаляем недокачанный файл
            if zip_path.exists():
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

        except urllib.error.URLError as e:
            logger.error(f"[ZIP] Ошибка сети при скачивании '{app_name}': {e.reason}")
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Ошибка сети: {e.reason}")
            )

        except zipfile.BadZipFile:
            logger.error(
                f"[ZIP] Файл '{app_name}.zip' поврежден или не является ZIP-архивом."
            )
            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(text="Ошибка: скачанный файл поврежден."),
            )
            if zip_path.exists():
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

        except PermissionError as e:
            logger.error(f"[ZIP] Ошибка доступа к файлам '{app_name}': {e}")
            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(
                    text="Ошибка: нет прав на запись в папку."
                ),
            )

        except Exception as e:
            logger.exception(
                f"[ZIP] Неизвестная ошибка при установке '{app_name}': {e}"
            )
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Критическая ошибка: {e}")
            )

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
