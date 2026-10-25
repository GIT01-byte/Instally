import tkinter as tk
import queue
import threading
import sys
from service.installer import install
from engines.zipEngine import download_and_extract_zip
from utils.logging import logger
from frontend.ui_config import (
    BG_PANEL,
    FG_MUTED,
    ACCENT,
    SUCCESS,
    WARNING,
    DANGER,
    FONT_CARD_DESC,
)


class TaskManager:
    def __init__(self, root, status_label, progress_bar, list_frame):
        self.root = root
        self.status_label = status_label
        self.progress_bar = progress_bar
        self.list_frame = list_frame
        self.queue = queue.Queue()
        threading.Thread(target=self._process_queue, daemon=True).start()

    def add_task(
        self,
        app_name,
        package,
        winget_package,
        snap_package,
        is_snap_classic,
        download_url=None,
        force=False,
    ):
        lbl = tk.Label(
            self.list_frame,
            text=f"⏸ {app_name} — Ожидание",
            font=FONT_CARD_DESC,
            bg=BG_PANEL,
            fg=FG_MUTED,
            anchor="w",
        )
        lbl.pack(fill="x", pady=2)
        self.queue.put(
            (
                app_name,
                package,
                winget_package,
                snap_package,
                is_snap_classic,
                download_url,
                force,
                lbl,
            )
        )

    def _process_queue(self):
        while True:
            (
                app_name,
                package,
                winget_package,
                snap_package,
                is_snap_classic,
                download_url,
                force,
                lbl,
            ) = self.queue.get()

            self.root.after(
                0,
                lambda l=lbl, n=app_name: l.config(
                    text=f"⚙️ {n} — Установка...", fg=ACCENT
                ),
            )

            try:
                if download_url:
                    thread = download_and_extract_zip(
                        url=download_url,
                        app_name=app_name,
                        ttk_log_widget=self.status_label,
                        ttk_progress_bar=self.progress_bar,
                    )
                else:
                    snap_map = {}
                    if snap_package:
                        snap_map[package] = (snap_package, is_snap_classic)

                    args = ["-y"]
                    if force:
                        if sys.platform == "win32":
                            args.append("--force")
                        elif sys.platform.startswith("linux"):
                            args.append("--reinstall")

                    thread = install(
                        action="install",
                        ttk_log_widget=self.status_label,
                        ttk_progress_bar=self.progress_bar,
                        packages=[package],
                        args=args,
                        winget_mapping=(
                            {package: winget_package} if winget_package else {}
                        ),
                        snap_mapping=snap_map,
                    )

                if thread:
                    thread.join()

                failed = getattr(thread, "failed_packages", [])
                already = getattr(thread, "already_installed", [])

                if download_url or not failed:
                    if already:
                        # 1. Желтая плашка в очереди
                        self.root.after(
                            0,
                            lambda l=lbl, n=app_name: l.config(
                                text=f"⚠️ {n} — Уже установлено", fg=WARNING
                            ),
                        )
                        # 2. Подсказка в нижний лог
                        hint_text = f"[!] '{app_name}' уже установлен. Если хотите переустановить, отметьте флажок 'Принудительно'."
                        self.root.after(
                            0,
                            lambda t=hint_text: self.status_label.config(
                                text=t, fg=WARNING
                            ),
                        )
                    else:
                        self.root.after(
                            0,
                            lambda l=lbl, n=app_name: l.config(
                                text=f"✅ {n} — Готово", fg=SUCCESS
                            ),
                        )
                else:
                    self.root.after(
                        0,
                        lambda l=lbl, n=app_name: l.config(
                            text=f"❌ {n} — Ошибка", fg=DANGER
                        ),
                    )

            except Exception as e:
                logger.error(f"Ошибка в очереди: {e}")
                self.root.after(
                    0,
                    lambda l=lbl, n=app_name: l.config(
                        text=f"❌ {n} — Ошибка", fg=DANGER
                    ),
                )

            self.queue.task_done()
