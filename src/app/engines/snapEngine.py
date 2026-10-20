import os
import shutil
import threading
from tkinter import Label, ttk
from typing import List, Union, Tuple, Optional

from utils.logging import logger
from .baseEngine import InstallEngine


def _find_snap() -> str | None:
    snap = shutil.which("snap")
    if snap:
        return snap
    if os.path.exists("/usr/bin/snap"):
        return "/usr/bin/snap"
    return None


def snap_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[Union[str, Tuple[str, bool]]]] = None,
    snap_args: Optional[List[str]] = None,
    thread_name: str = "SnapWorker",
) -> threading.Thread:

    normalized_packages = []
    if packages:
        for p in packages:
            normalized_packages.append(p if isinstance(p, tuple) else (p, False))
    args_list = list(snap_args) if snap_args else []

    engine = InstallEngine(timeout=120)

    def worker():
        total = len(normalized_packages)
        snap_thread.failed_packages = []
        if total == 0:
            return

        try:
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0)
            )
        except Exception:
            pass

        snap_exe = _find_snap()
        if not snap_exe:
            logger.error("snap не найден.")
            snap_thread.failed_packages = [p[0] for p in normalized_packages]
            return

        success_count = 0
        fail_count = 0

        for i, (package_name, is_classic) in enumerate(normalized_packages, start=1):
            cmd = [snap_exe, "install", package_name]
            if is_classic and "--classic" not in args_list:
                cmd.append("--classic")
            cmd.extend(args_list)

            rc = engine.run_process(
                cmd=cmd,
                log_widget=ttk_log_widget,
                progress_bar=ttk_progress_bar,
                package_label=package_name,
                package_index=i,
                package_total=total,
                progress_regex=r"(\d+)\s*%",
            )

            if rc == 0:
                success_count += 1
            else:
                fail_count += 1
                snap_thread.failed_packages.append(package_name)
                logger.warning(f"Пакет '{package_name}' не установлен. Код: {rc}")

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = (
            f"Snap завершен. Успешно: {success_count}, ошибок: {fail_count} из {total}."
        )
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    snap_thread = threading.Thread(target=worker, daemon=True, name=thread_name)
    snap_thread.start()
    return snap_thread
