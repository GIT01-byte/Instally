"""
Фасад для установки пакетов на разных ОС.
На Windows — choco, на Debian/Ubuntu — apt, на RedOS/RHEL/Fedora — dnf.
"""

import platform
from tkinter import Label, ttk
from typing import List, Optional


def _detect_engine() -> str:
    """
    Возвращает одно из: 'choco', 'apt', 'dnf', 'unknown'.
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
        import shutil

        if shutil.which("dnf"):
            return "dnf"
        if shutil.which("apt-get"):
            return "apt"

    return "unknown"


def install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
):
    """
    Универсальная точка входа. Сама выбирает движок по текущей ОС.

    action: 'install' | 'upgrade'
    packages: список имён пакетов (для install)
    args: доп. аргументы движка (например, ['-y'])
    """
    engine = _detect_engine()
    logger_msg = f"[Installer] Выбран движок: {engine}"
    try:
        from utils.logging import logger

        logger.info(logger_msg)
    except Exception:
        print(logger_msg)

    if engine == "choco":
        from engines.chocoEngine import choco_install

        return choco_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=packages,
            choco_args=args,
        )

    if engine == "apt":
        from engines.aptEngine import apt_install

        return apt_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=packages,
            apt_args=args,
        )

    if engine == "dnf":
        from engines.dnfEngine import dnf_install

        return dnf_install(
            action=action,
            ttk_log_widget=ttk_log_widget,
            ttk_progress_bar=ttk_progress_bar,
            packages=packages,
            dnf_args=args,
        )

    # unknown
    ttk_log_widget.after(
        0,
        lambda: ttk_log_widget.config(
            text=f"Не удалось определить пакетный менеджер. ОС: {platform.system()}"
        ),
    )
    raise RuntimeError(f"Unsupported OS: {platform.system()}")


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
