import os
import sys
import urllib.request
import zipfile
import threading
from pathlib import Path
from tkinter import Label, ttk
from utils.logging import logger


def download_and_extract_zip(
    url: str, app_name: str, ttk_log_widget: Label, ttk_progress_bar: ttk.Progressbar
) -> threading.Thread:

    def worker():
        try:
            # 1. Создаем папку в "Загрузках" пользователя
            downloads_dir = Path.home() / "Downloads" / "Instally_Apps" / app_name
            downloads_dir.mkdir(parents=True, exist_ok=True)

            zip_path = downloads_dir / f"{app_name}.zip"

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Скачивание {app_name}...")
            )
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=100, value=0)
            )

            # 2. Скачивание с прогресс-баром
            def report_hook(block_num, block_size, total_size):
                if total_size > 0:
                    read_so_far = block_num * block_size
                    percent = int(read_so_far * 100 / total_size)
                    ttk_progress_bar.after(
                        0, lambda p=percent: ttk_progress_bar.config(value=p)
                    )

            urllib.request.urlretrieve(url, zip_path, reporthook=report_hook)

            # 3. Распаковка
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Распаковка архива...")
            )
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(downloads_dir)

            # Удаляем сам архив после распаковки, чтобы не занимать место
            os.remove(zip_path)

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Готово! Папка открыта.")
            )

            # 4. Автоматически открываем папку в системе
            if sys.platform == "win32":
                os.startfile(downloads_dir)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{downloads_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{downloads_dir}"')

        except Exception as e:
            logger.error(f"Ошибка ZIP загрузки: {e}")
            ttk_log_widget.after(0, lambda: ttk_log_widget.config(text=f"Ошибка: {e}"))
            raise e  # Пробрасываем ошибку, чтобы очередь загорелась красным

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread
