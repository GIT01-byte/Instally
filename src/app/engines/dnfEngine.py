import os
import threading
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger
from .baseEngine import InstallEngine

DNF_EXE = "/usr/bin/dnf"


def dnf_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    dnf_args: Optional[List[str]] = None,
    thread_name: str = "DnfWorker",
) -> threading.Thread:

    packages_list = list(packages) if packages else []
    dnf_args_list = list(dnf_args) if dnf_args else []
    if "-y" not in dnf_args_list:
        dnf_args_list.append("-y")

    env = os.environ.copy()
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"

    engine = InstallEngine(timeout=120)

    def worker():
        total = len(packages_list)
        dnf_thread.failed_packages = []
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
            cmd = [DNF_EXE, action, package] + dnf_args_list

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
                dnf_thread.failed_packages.append(package)

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Готово. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    dnf_thread = threading.Thread(target=worker, daemon=True, name=thread_name)
    dnf_thread.start()
    return dnf_thread
