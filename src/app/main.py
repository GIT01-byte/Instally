import tkinter as tk
import sys
import subprocess
import os

from utils.os_handling import get_admin_permisions
from frontend.window import AppWindow

CHOCO_CACHE_DIR = r"C:\ChocolateyCache"


def _configure_choco_cache():
    if sys.platform != "win32":
        return
    CREATE_NO_WINDOW = 0x08000000
    try:
        os.makedirs(CHOCO_CACHE_DIR, exist_ok=True)
    except OSError:
        pass
    choco_path = r"C:\ProgramData\chocolatey\bin\choco.exe"
    if not os.path.exists(choco_path):
        choco_path = "choco"
    cmd = [choco_path, "config", "set", "cacheLocation", CHOCO_CACHE_DIR]
    try:
        subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=CREATE_NO_WINDOW,
            shell=False,
            timeout=15,
        )
    except Exception:
        pass


def _set_app_icon(root):
    if getattr(sys, "frozen", False):
        icon_path = os.path.join(sys._MEIPASS, "icon.ico")
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_path, "icon.ico")

    try:
        if os.path.exists(icon_path):
            root.iconbitmap(bitmap=icon_path)
        else:
            print(f"[WARN] Иконка не найдена: {icon_path}")
    except Exception as e:
        print(f"[ERROR] Иконка: {e}")


def _set_windows_app_id():
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "mycompany.instally.app.1"
        )


def start():
    get_admin_permisions()
    _configure_choco_cache()
    _set_windows_app_id()

    root = tk.Tk()
    _set_app_icon(root)

    app = AppWindow(root)
    root.mainloop()


if __name__ == "__main__":
    start()
