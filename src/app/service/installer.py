import platform
import threading
import shutil
from tkinter import Label, ttk
from typing import List, Optional


def _detect_engine() -> str:
    system = platform.system().lower()
    if system == "windows":
        return "choco"
    if system == "linux":
        distro_id = ""
        try:
            with open("/etc/os-release", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_id = line.split("=", 1)[1].strip().strip('"').lower()
                        break
        except FileNotFoundError:
            pass
        if distro_id in ("redos", "rhel", "centos", "fedora", "rocky", "almalinux"):
            return "dnf"
        if distro_id in ("debian", "ubuntu", "linuxmint", "pop", "kali"):
            return "apt"
        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("apt-get"):
            return "apt"
        if shutil.which("snap"):
            return "snap"
    return "unknown"


def install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
    winget_mapping: Optional[dict] = None,
    snap_mapping: Optional[dict] = None,
    cancel_event: threading.Event = None,
) -> threading.Thread:

    engine = _detect_engine()
    try:
        from utils.logging import logger

        logger.info(f"[Installer] Выбран движок: {engine}")
    except Exception:
        print(f"[Installer] Выбран движок: {engine}")

    if engine == "choco":
        from engines.chocoEngine import choco_install
        from engines.wingetEngine import winget_install

        def chain_worker():
            current_thread = threading.current_thread()
            current_thread.failed_packages = []
            current_thread.already_installed = []

            pkgs = list(packages) if packages else []
            if not pkgs:
                return

            choco_thread = choco_install(
                action=action,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=pkgs,
                choco_args=args,
                cancel_event=cancel_event,
            )
            if hasattr(choco_thread, "join"):
                choco_thread.join()

            failed = getattr(choco_thread, "failed_packages", [])
            already = getattr(choco_thread, "already_installed", [])
            current_thread.already_installed = already

            if not failed or (cancel_event and cancel_event.is_set()):
                return

            winget_pkgs = []
            for p in failed:
                if winget_mapping and p in winget_mapping and winget_mapping[p]:
                    winget_pkgs.append(winget_mapping[p])
                else:
                    winget_pkgs.append(p)

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="[Choco упал] Запуск Winget...")
            )

            winget_thread = winget_install(
                action="install",
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=winget_pkgs,
                cancel_event=cancel_event,
            )
            if hasattr(winget_thread, "join"):
                winget_thread.join()

            current_thread.failed_packages = getattr(
                winget_thread, "failed_packages", []
            )

        chain_thread = threading.Thread(
            target=chain_worker, daemon=True, name="ChainWorker"
        )
        chain_thread.start()
        return chain_thread

    if engine == "apt":
        from engines.aptEngine import apt_install
        from engines.snapEngine import snap_install

        def apt_chain_worker():
            current_thread = threading.current_thread()
            current_thread.failed_packages = []
            current_thread.already_installed = []

            pkgs = list(packages) if packages else []
            if not pkgs:
                return

            apt_thread = apt_install(
                action=action,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=pkgs,
                apt_args=args,
                cancel_event=cancel_event,
            )
            if hasattr(apt_thread, "join"):
                apt_thread.join()

            failed = getattr(apt_thread, "failed_packages", [])
            already = getattr(apt_thread, "already_installed", [])
            current_thread.already_installed = already

            if not failed or (cancel_event and cancel_event.is_set()):
                return

            snap_pkgs = []
            for p in failed:
                if snap_mapping and p in snap_mapping:
                    data = snap_mapping[p]
                    if isinstance(data, tuple):
                        snap_name, is_classic = data
                        if snap_name:
                            snap_pkgs.append((snap_name, is_classic))
                    elif isinstance(data, str) and data:
                        snap_pkgs.append((data, False))
                else:
                    snap_pkgs.append((p, False))

            if not snap_pkgs:
                return

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="[Apt упал] Запуск Snap...")
            )

            snap_thread = snap_install(
                action="install",
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=snap_pkgs,
                cancel_event=cancel_event,
            )
            if hasattr(snap_thread, "join"):
                snap_thread.join()

            current_thread.failed_packages = getattr(snap_thread, "failed_packages", [])

        chain_thread = threading.Thread(
            target=apt_chain_worker, daemon=True, name="AptSnapWorker"
        )
        chain_thread.start()
        return chain_thread

    if engine == "snap":
        from engines.snapEngine import snap_install

        snap_pkgs = []
        if packages:
            for p in packages:
                if snap_mapping and p in snap_mapping:
                    data = snap_mapping[p]
                    if isinstance(data, tuple):
                        snap_pkgs.append(data)
                    else:
                        snap_pkgs.append((data, False))
                else:
                    snap_pkgs.append((p, False))

        return snap_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=snap_pkgs,
            snap_args=args,
            cancel_event=cancel_event,
        )

    if engine == "dnf":
        from engines.dnfEngine import dnf_install

        return dnf_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=packages,
            dnf_args=args,
            cancel_event=cancel_event,
        )

    ttk_log_widget.after(0, lambda: ttk_log_widget.config(text="ОС не поддерживается"))
    dummy_thread = threading.Thread(target=lambda: None, daemon=True)
    dummy_thread.failed_packages = packages or []
    dummy_thread.already_installed = []
    dummy_thread.start()
    return dummy_thread


def clear_cache():
    engine = _detect_engine()
    if engine == "choco":
        from engines.chocoEngine import clear_choco_cache

        return clear_choco_cache()
    if engine == "apt":
        from engines.aptEngine import clear_apt_cache

        return clear_apt_cache()
    if engine == "dnf":
        from engines.dnfEngine import clear_dnf_cache

        return clear_dnf_cache()
    if engine == "snap":
        try:
            from utils.logging import logger

            logger.info("[Snap] Очистка кэша не требуется.")
        except Exception:
            pass
        return
