import os
import sys
import subprocess
import threading
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger
from .baseEngine import InstallEngine

APT_EXE = "/usr/bin/apt-get"


def apt_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    apt_args: Optional[List[str]] = None,
    thread_name: str = "AptWorker",
) -> threading.Thread:

    packages_list = list(packages) if packages else []
    apt_args_list = list(apt_args) if apt_args else []

    if "-y" not in apt_args_list and "--yes" not in apt_args_list:
        apt_args_list.append("-y")
    if "-o" not in apt_args_list:
        apt_args_list.extend(
            [
                "-o",
                "Dpkg::Options::=--force-confnew",
                "-o",
                "Dpkg::Options::=--force-confdef",
            ]
        )

    # Окружение для тихой установки
    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"

    engine = InstallEngine(timeout=120)

    def worker():
        total = len(packages_list)
        apt_thread.failed_packages = []

        try:
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0)
            )
        except Exception:
            pass

        if not packages_list:
            return

        # Обновление индексов
        ttk_log_widget.after(0, lambda: ttk_log_widget.config(text="apt-get update..."))
        engine.run_process(
            [APT_EXE, "update"],
            ttk_log_widget,
            ttk_progress_bar,
            "update",
            0,
            total,
            env=env,
        )

        success_count = 0
        fail_count = 0

        for i, package in enumerate(packages_list, start=1):
            cmd = [APT_EXE, action, package] + apt_args_list

            rc = engine.run_process(
                cmd=cmd,
                log_widget=ttk_log_widget,
                progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
                progress_regex=r"\[\s*(\d+)\s*%\]",
                env=env,
            )

            if rc == 0:
                success_count += 1
            else:
                fail_count += 1
                apt_thread.failed_packages.append(package)

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Готово. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    apt_thread = threading.Thread(target=worker, daemon=True, name=thread_name)
    apt_thread.start()
    return apt_thread
