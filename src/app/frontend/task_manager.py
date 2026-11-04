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
    FG_TEXT,
    ACCENT,
    SUCCESS,
    WARNING,
    DANGER,
    DANGER_HOVER,
    FONT_CARD_DESC,
)


class Task:
    def __init__(
        self,
        app_name,
        package,
        winget_package,
        snap_package,
        is_snap_classic,
        download_url,
        force,
    ):
        self.app_name = app_name
        self.package = package
        self.winget_package = winget_package
        self.snap_package = snap_package
        self.is_snap_classic = is_snap_classic
        self.download_url = download_url
        self.force = force
        self.is_cancelled = False
        self.cancel_event = threading.Event()
        self.frame = None
        self.lbl = None
        self.cancel_btn = None


class TaskManager:
    def __init__(self, root, status_label, progress_bar, list_frame):
        self.root = root
        self.status_label = status_label
        self.progress_bar = progress_bar
        self.list_frame = list_frame
        self.queue = queue.Queue()
        self.current_task = None
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
        for widget in self.list_frame.winfo_children():
            if isinstance(widget, tk.Frame) and len(widget.winfo_children()) > 0:
                first_child = widget.winfo_children()[0]
                if isinstance(first_child, tk.Label) and app_name in first_child.cget(
                    "text"
                ):
                    widget.destroy()

        task = Task(
            app_name,
            package,
            winget_package,
            snap_package,
            is_snap_classic,
            download_url,
            force,
        )
        task.frame = tk.Frame(self.list_frame, bg=BG_PANEL, pady=3)
        task.frame.pack(fill="x", expand=False)
        task.lbl = tk.Label(
            task.frame,
            text=f"⏸ {app_name} — В очереди...",
            font=FONT_CARD_DESC,
            bg=BG_PANEL,
            fg=FG_MUTED,
            anchor="w",
        )
        task.lbl.pack(side="left", fill="x", expand=True, padx=(5, 0))

        task.cancel_btn = tk.Button(
            task.frame,
            text="✖ Отменить",
            font=("Segoe UI", 8),
            bg=BG_PANEL,
            fg=DANGER,
            activebackground=BG_PANEL,
            activeforeground=DANGER_HOVER,
            borderwidth=0,
            cursor="hand2",
            command=lambda t=task: self._cancel_single_task(t),
        )
        task.cancel_btn.pack(side="right", padx=5)
        task.cancel_btn.bind(
            "<Enter>", lambda e, b=task.cancel_btn: b.config(fg=DANGER_HOVER)
        )
        task.cancel_btn.bind(
            "<Leave>", lambda e, b=task.cancel_btn: b.config(fg=DANGER)
        )

        self.queue.put(task)

    def _cancel_single_task(self, task):
        if task.is_cancelled:
            return
        task.is_cancelled = True
        task.cancel_event.set()

        if task.frame and task.frame.winfo_exists():
            task.frame.destroy()

        if task != self.current_task:
            self.root.after(
                0,
                lambda: self.status_label.config(
                    text=f"Задача '{task.app_name}' удалена из очереди.", fg=DANGER
                ),
            )
        else:
            self.root.after(
                0,
                lambda: self.status_label.config(
                    text=f"Задача '{task.app_name}' отменяется...", fg=DANGER
                ),
            )

    def clear_all(self):
        if self.current_task:
            self.current_task.is_cancelled = True
            self.current_task.cancel_event.set()

        while not self.queue.empty():
            try:
                task = self.queue.get_nowait()
                task.is_cancelled = True
                task.cancel_event.set()
                if task.frame and task.frame.winfo_exists():
                    task.frame.destroy()
                self.queue.task_done()
            except queue.Empty:
                break

        for widget in self.list_frame.winfo_children():
            widget.destroy()
        self.root.after(
            0, lambda: self.status_label.config(text="Все задачи отменены.", fg=DANGER)
        )

    def _process_queue(self):
        while True:
            task = self.queue.get()
            self.current_task = task

            if task.is_cancelled:
                self.current_task = None
                self.queue.task_done()
                continue

            self.root.after(
                0,
                lambda n=task.app_name: self.status_label.config(
                    text=f"Установка {n}...", fg=FG_TEXT
                ),
            )
            if task.lbl.winfo_exists():
                self.root.after(
                    0,
                    lambda l=task.lbl, n=task.app_name: l.config(
                        text=f"⚙️ {n} — Установка...", fg=ACCENT
                    ),
                )

            try:
                if task.download_url:
                    thread = download_and_extract_zip(
                        url=task.download_url,
                        app_name=task.app_name,
                        ttk_log_widget=self.status_label,
                        ttk_progress_bar=self.progress_bar,
                        cancel_event=task.cancel_event,
                    )
                else:
                    snap_map = {}
                    if task.snap_package:
                        snap_map[task.package] = (
                            task.snap_package,
                            task.is_snap_classic,
                        )
                    args = ["-y"]
                    if task.force:
                        if sys.platform == "win32":
                            args.append("--force")
                        elif sys.platform.startswith("linux"):
                            args.append("--reinstall")

                    thread = install(
                        action="install",
                        ttk_log_widget=self.status_label,
                        ttk_progress_bar=self.progress_bar,
                        packages=[task.package],
                        args=args,
                        winget_mapping=(
                            {task.package: task.winget_package}
                            if task.winget_package
                            else {}
                        ),
                        snap_mapping=snap_map,
                        cancel_event=task.cancel_event,
                    )

                if thread:
                    thread.join()
                self.current_task = None

                if task.is_cancelled:
                    self.queue.task_done()
                    continue

                failed = getattr(thread, "failed_packages", [])
                already = getattr(thread, "already_installed", [])

                if task.download_url or not failed:
                    if already and not task.force:
                        if task.lbl.winfo_exists():
                            self.root.after(
                                0,
                                lambda l=task.lbl, n=task.app_name: l.config(
                                    text=f"⚠️ {n} — Уже установлено", fg=WARNING
                                ),
                            )
                            self.root.after(0, lambda: task.cancel_btn.pack_forget())
                        hint_text = f"[!] '{task.app_name}' уже установлен. Отметьте 'Принудительно' для переустановки."
                        self.root.after(
                            0,
                            lambda t=hint_text: self.status_label.config(
                                text=t, fg=WARNING
                            ),
                        )
                    else:
                        if task.lbl.winfo_exists():
                            self.root.after(
                                0,
                                lambda l=task.lbl, n=task.app_name: l.config(
                                    text=f"✅ {n} — Готово", fg=SUCCESS
                                ),
                            )
                            self.root.after(0, lambda: task.cancel_btn.pack_forget())
                else:
                    if task.lbl.winfo_exists():
                        self.root.after(
                            0,
                            lambda l=task.lbl, n=task.app_name: l.config(
                                text=f"❌ {n} — Ошибка", fg=DANGER
                            ),
                        )
                        self.root.after(0, lambda: task.cancel_btn.pack_forget())
                    self.root.after(
                        0,
                        lambda: self.status_label.config(
                            text="Ошибка установки. Проверьте лог.", fg=DANGER
                        ),
                    )

            except Exception as e:
                logger.error(f"Ошибка в очереди: {e}")
                self.current_task = None
                if not task.is_cancelled and task.lbl.winfo_exists():
                    self.root.after(
                        0,
                        lambda l=task.lbl, n=task.app_name: l.config(
                            text=f"❌ {n} — Ошибка", fg=DANGER
                        ),
                    )
                    self.root.after(0, lambda: task.cancel_btn.pack_forget())
                    self.root.after(
                        0,
                        lambda: self.status_label.config(
                            text="Критическая ошибка.", fg=DANGER
                        ),
                    )

            self.queue.task_done()
