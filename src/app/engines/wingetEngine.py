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
from .baseEngine import InstallEngine


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


def winget_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    winget_args: Optional[List[str]] = None,
    thread_name: str = "WingetWorker",
    cancel_event: threading.Event = None,
) -> threading.Thread:

    packages_list = list(packages) if packages else []
    default_args = [
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
    ]
    cmd_args = default_args + (list(winget_args) if winget_args else [])

    engine = InstallEngine(timeout=120)

    def worker():
        total = len(packages_list)
        winget_thread.failed_packages = []
        if total == 0:
            return

        winget_exe = _find_winget()
        if not winget_exe:
            logger.error("winget.exe не найден.")
            winget_thread.failed_packages = packages_list
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
            cmd = [winget_exe, action, "--id", package] + cmd_args

            rc = engine.run_process(
                cmd=cmd,
                log_widget=ttk_log_widget,
                progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
                cancel_event=cancel_event,
            )

            if rc in (0, 3010):
                success_count += 1
            else:
                fail_count += 1
                winget_thread.failed_packages.append(package)

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Winget завершен. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    winget_thread = threading.Thread(target=worker, daemon=True, name=thread_name)
    winget_thread.start()
    return winget_thread
