"""
Фасад для установки пакетов на разных ОС.
На Windows — choco -> при неудаче -> winget.
На Linux (Debian/Ubuntu) — apt -> при неудаче -> snap.
На Linux (RedOS/RHEL/Fedora) — dnf.
"""

import platform
import threading
import shutil
from tkinter import Label, ttk
from typing import List, Optional


def _detect_engine() -> str:
    """
    Возвращает одно из: 'choco', 'apt', 'dnf', 'snap', 'unknown'.
    """
    system = platform.system().lower()

    if system == "windows":
        return "choco"

    if system == "linux":
        # Читаем /etc/os-release, чтобы понять дистрибутив
        distro_id = ""
        try:
            with open("/etc/os-release", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro_id = line.split("=", 1)[1].strip().strip('"').lower()
                        break
        except FileNotFoundError:
            pass

        # dnf-дистрибутивы
        if distro_id in ("redos", "rhel", "centos", "fedora", "rocky", "almalinux"):
            return "dnf"

        # apt-дистрибутивы
        if distro_id in ("debian", "ubuntu", "linuxmint", "pop", "kali"):
            return "apt"

        # Если не поняли — смотрим, какой менеджер есть в системе
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
    snap_mapping: Optional[
        dict
    ] = None,  # Формат: {"код-apt": ("код-snap", is_classic)}
) -> threading.Thread:
    """
    Универсальная точка входа. Сама выбирает движок по текущей ОС.
    Всегда возвращает объект threading.Thread, чтобы менеджер очередей мог ждать завершения.
    """
    engine = _detect_engine()
    logger_msg = f"[Installer] Выбран движок: {engine}"
    try:
        from utils.logging import logger

        logger.info(logger_msg)
    except Exception:
        print(logger_msg)

    # =========================================================
    # WINDOWS: CHOCO -> WINGET
    # =========================================================
    if engine == "choco":
        from engines.chocoEngine import choco_install
        from engines.wingetEngine import winget_install

        def chain_worker():
            # Ссылка на текущий поток, чтобы сохранить в него финальный статус
            current_thread = threading.current_thread()
            current_thread.failed_packages = []

            pkgs = list(packages) if packages else []
            if not pkgs:
                return

            # 1. Запускаем Choco
            choco_thread = choco_install(
                action=action,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=pkgs,
                choco_args=args,
            )
            if hasattr(choco_thread, "join"):
                choco_thread.join()

            # 2. Проверяем ошибки
            failed = getattr(choco_thread, "failed_packages", [])
            if not failed:
                return

            # 3. Формируем список для Winget
            winget_pkgs = []
            for p in failed:
                if winget_mapping and p in winget_mapping and winget_mapping[p]:
                    winget_pkgs.append(winget_mapping[p])
                else:
                    winget_pkgs.append(p)

            try:
                from utils.logging import logger

                logger.warning(
                    f"[Installer] Choco упал на: {failed}. Запускаю Winget для: {winget_pkgs}"
                )
            except Exception:
                pass

            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="[Choco упал] Запуск Winget...")
            )

            # 4. Запускаем Winget
            winget_thread = winget_install(
                action="install",
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=winget_pkgs,
            )
            if hasattr(winget_thread, "join"):
                winget_thread.join()

            # 5. Сохраняем финальный результат от Winget в наш поток
            current_thread.failed_packages = getattr(
                winget_thread, "failed_packages", []
            )

        chain_thread = threading.Thread(
            target=chain_worker, daemon=True, name="ChainWorker"
        )
        chain_thread.start()
        return chain_thread

    # =========================================================
    # LINUX (DEBIAN/UBUNTU): APT -> SNAP
    # =========================================================
    if engine == "apt":
        from engines.aptEngine import apt_install
        from engines.snapEngine import snap_install

        def apt_chain_worker():
            # Ссылка на текущий поток
            current_thread = threading.current_thread()
            current_thread.failed_packages = []

            pkgs = list(packages) if packages else []
            if not pkgs:
                return

            # 1. Запускаем Apt
            apt_thread = apt_install(
                action=action,
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=pkgs,
                apt_args=args,
            )
            if hasattr(apt_thread, "join"):
                apt_thread.join()

            # 2. Проверяем ошибки (упавшие пакеты)
            failed = getattr(apt_thread, "failed_packages", [])
            if not failed:
                return

            # 3. Формируем список для Snap (с учетом флага is_classic)
            snap_pkgs = []
            for p in failed:
                # snap_mapping имеет формат { "apt_code": ("snap_code", is_classic) }
                if snap_mapping and p in snap_mapping:
                    snap_pkg_data = snap_mapping[p]
                    if isinstance(snap_pkg_data, tuple):
                        snap_name, is_classic = snap_pkg_data
                        if snap_name:
                            snap_pkgs.append((snap_name, is_classic))
                    elif isinstance(snap_pkg_data, str) and snap_pkg_data:
                        snap_pkgs.append((snap_pkg_data, False))
                else:
                    # Если маппинга нет, пробуем поставить как есть
                    snap_pkgs.append((p, False))

            if not snap_pkgs:
                return

            try:
                from utils.logging import logger

                logger.warning(
                    f"[Installer] Apt упал на: {failed}. Запускаю Snap для: {snap_pkgs}"
                )
            except Exception:
                pass

            ttk_log_widget.after(
                0,
                lambda: ttk_log_widget.config(
                    text="[Apt упал] Запуск Snap для установки..."
                ),
            )

            # 4. Запускаем Snap
            snap_thread = snap_install(
                action="install",
                ttk_log_widget=ttk_log_widget,
                ttk_progress_bar=ttk_progress_bar,
                packages=snap_pkgs,
            )
            if hasattr(snap_thread, "join"):
                snap_thread.join()

            # 5. Сохраняем финальный результат от Snap в наш поток
            current_thread.failed_packages = getattr(snap_thread, "failed_packages", [])

        chain_thread = threading.Thread(
            target=apt_chain_worker, daemon=True, name="AptSnapWorker"
        )
        chain_thread.start()
        return chain_thread

    # =========================================================
    # LINUX: ЧИСТЫЙ SNAP (Если apt нет)
    # =========================================================
    if engine == "snap":
        from engines.snapEngine import snap_install

        # Если пакеты пришли строками, конвертируем их в кортежи, чтобы сохранить логику
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
        )

    # =========================================================
    # LINUX: DNF (Fedora / RedOS)
    # =========================================================
    if engine == "dnf":
        from engines.dnfEngine import dnf_install

        return dnf_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=packages,
            dnf_args=args,
        )

    # =========================================================
    # UNKNOWN
    # =========================================================
    ttk_log_widget.after(
        0,
        lambda: ttk_log_widget.config(
            text=f"Не удалось определить пакетный менеджер. ОС: {platform.system()}"
        ),
    )

    dummy_thread = threading.Thread(target=lambda: None, daemon=True)
    dummy_thread.failed_packages = packages or []  # Помечаем как ошибку
    dummy_thread.start()
    return dummy_thread


def clear_cache():
    """Универсальная очистка кэша выбранного движка."""
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

            logger.info(
                "[Snap] Очистка кэша не требуется (snap делает это автоматически)."
            )
        except Exception:
            pass
        return
