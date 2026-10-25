import os
import sys
import subprocess
import threading
import shutil
from pathlib import Path
from tkinter import Label, ttk
from typing import List, Optional

from utils.logging import logger
from .baseEngine import InstallEngine

_CHOCO_EXE_CACHE: str | None = None


def ensure_choco() -> str:
    global _CHOCO_EXE_CACHE
    if _CHOCO_EXE_CACHE:
        return _CHOCO_EXE_CACHE

    choco = shutil.which("choco") or (
        str(Path(r"C:\ProgramData\chocolatey\bin\choco.exe"))
        if Path(r"C:\ProgramData\chocolatey\bin\choco.exe").exists()
        else None
    )
    if choco:
        _CHOCO_EXE_CACHE = choco
        return choco

    logger.info("[Choco] Устанавливаю системный...")
    install_cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"

    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            install_cmd,
        ],
        creationflags=0x08000000,
    )

    choco = shutil.which("choco")
    if not choco:
        raise RuntimeError("Choco не установлен.")
    _CHOCO_EXE_CACHE = choco
    return choco


def choco_install(
    action: str,
    ttk_log_widget: Label,
    ttk_progress_bar: ttk.Progressbar,
    packages: Optional[List[str]] = None,
    choco_args: Optional[List[str]] = None,
    thread_name: str = "ChocoWorker",
) -> threading.Thread:

    packages_list = list(packages) if packages else []
    choco_args_list = list(choco_args) if choco_args else []
    if "-y" not in choco_args_list:
        choco_args_list.append("-y")

    engine = InstallEngine(timeout=120)

    # Паттерны для отлова ошибок 404 от Choco
    error_pats = [
        r"404\s+Not\s+Found",
        r"remote file either doesn't exist",
        r"\(404\)",
        r"The remote server returned an error",
    ]

    # Паттерн для определения, что пакет уже установлен (ДОБАВЛЕНО)
    already_pats = [r"already installed"]

    def worker():
        total = len(packages_list)
        choco_thread.failed_packages = []
        choco_thread.already_installed = []  # <--- Сохраняем список "уже установленных"

        if total == 0:
            return

        try:
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text="Проверяю Choco...")
            )
            choco_exe = ensure_choco()
        except Exception as e:
            choco_thread.failed_packages = packages_list
            ttk_log_widget.after(
                0, lambda: ttk_log_widget.config(text=f"Ошибка Choco: {e}")
            )
            return

        try:
            ttk_progress_bar.after(
                0, lambda: ttk_progress_bar.configure(maximum=max(total, 1), value=0)
            )
        except Exception:
            pass

        success_count = 0
        fail_count = 0
        already_count = 0

        for i, package in enumerate(packages_list, start=1):
            cmd = [choco_exe, action, package] + choco_args_list

            rc = engine.run_process(
                cmd=cmd,
                log_widget=ttk_log_widget,
                progress_bar=ttk_progress_bar,
                package_label=package,
                package_index=i,
                package_total=total,
                progress_regex=r"(\d+)\s*%",
                error_patterns=error_pats,
                already_installed_patterns=already_pats,  # <--- Передаем паттерн
            )

            if rc in (0, 3010):
                success_count += 1
            elif rc == -2:  # <--- Обрабатываем код "Уже установлено"
                already_count += 1
                choco_thread.already_installed.append(package)
            else:
                fail_count += 1
                choco_thread.failed_packages.append(package)

            ttk_progress_bar.after(0, lambda i=i: ttk_progress_bar.config(value=i))

        summary = f"Готово. Установлено: {success_count}, уже было: {already_count}, ошибок: {fail_count}."
        logger.info(summary)
        ttk_log_widget.after(0, lambda s=summary: ttk_log_widget.config(text=s))

    choco_thread = threading.Thread(target=worker, daemon=True, name=thread_name)
    choco_thread.start()
    return choco_thread


def clear_choco_cache():
    try:
        choco_exe = ensure_choco()
        subprocess.run(
            [choco_exe, "cache", "remove", "--all", "-y"], creationflags=0x08000000
        )
    except Exception:
        pass
