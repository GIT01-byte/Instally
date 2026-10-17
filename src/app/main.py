import tkinter as tk
from tkinter import ttk
import sys
import subprocess
import queue
import threading

from utils.os_handling import get_admin_permisions
from service.installer import install
from utils.logging import logger

# Импортируем каталог прямо из Python-файла
from data.catalog import CATALOG

# ==============================================================
#                    НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ==============================================================
APP_NAME = "Instally"
APP_TAGLINE = "Избавляет вас от рутины установки программ"

BG_ROOT = "#1e1f29"
BG_PANEL = "#282a36"
BG_CARD = "#2f313e"
BG_CARD_HOVER = "#383a4a"
BG_INPUT = "#21222c"

FG_TITLE = "#f8f8f2"
FG_TEXT = "#d7d7e0"
FG_MUTED = "#8b8d9a"
FG_DIM = "#5f6170"

ACCENT = "#bd93f9"
ACCENT_HOVER = "#caa9fa"
ACCENT_DARK = "#8a5cf6"

SUCCESS = "#50fa7b"
DANGER = "#ff5555"
DANGER_HOVER = "#ff6e6e"
BORDER = "#3a3c4a"

CHOCO_CACHE_DIR = r"C:\ChocolateyCache"


# ==============================================================
#                    МЕНЕДЖЕР ОЧЕРЕДИ ЗАДАЧ
# ==============================================================
class TaskManager:
    def __init__(self, root, status_label, progress_bar, list_frame):
        self.root = root
        self.status_label = status_label
        self.progress_bar = progress_bar
        self.list_frame = list_frame
        self.queue = queue.Queue()
        self.is_running = False

        # Запускаем фоновый обработчик очереди
        threading.Thread(target=self._process_queue, daemon=True).start()

    def add_task(
        self, app_name, package, winget_package, snap_package, is_snap_classic
    ):
        # Создаем визуальную плашку задачи
        lbl = tk.Label(
            self.list_frame,
            text=f"⏸ {app_name} — Ожидание",
            font=("Segoe UI", 9),
            bg=BG_PANEL,
            fg=FG_MUTED,
            anchor="w",
        )
        lbl.pack(fill="x", pady=2)

        # Кладем в очередь
        self.queue.put(
            (app_name, package, winget_package, snap_package, is_snap_classic, lbl)
        )

    def _process_queue(self):
        while True:
            app_name, package, winget_package, snap_package, is_snap_classic, lbl = (
                self.queue.get()
            )

            # Меняем статус в UI на "Установка"
            self.root.after(
                0,
                lambda l=lbl, n=app_name: l.config(
                    text=f"⚙️ {n} — Установка...", fg=ACCENT
                ),
            )

            try:
                # Формируем маппинг для Snap (кортеж из имени и флага)
                snap_map = {}
                if snap_package:
                    snap_map[package] = (snap_package, is_snap_classic)

                # Запускаем установку и ЖДЕМ её завершения
                thread = install(
                    action="install",
                    ttk_log_widget=self.status_label,
                    ttk_progress_bar=self.progress_bar,
                    packages=[package],
                    args=["-y"],
                    winget_mapping={package: winget_package} if winget_package else {},
                    snap_mapping=snap_map,
                )
                if thread:
                    thread.join()  # Ждем, пока поток установки завершится

                # Проверяем, упало ли (по тексту статуса)
                current_status = self.status_label.cget("text")
                if (
                    "ошибок: 0" in current_status
                    or "успешно" in current_status.lower()
                    or "Snap завершен. Успешно: 1" in current_status
                ):
                    self.root.after(
                        0,
                        lambda l=lbl, n=app_name: l.config(
                            text=f"✅ {n} — Готово", fg=SUCCESS
                        ),
                    )
                else:
                    self.root.after(
                        0,
                        lambda l=lbl, n=app_name: l.config(
                            text=f"❌ {n} — Ошибка", fg=DANGER
                        ),
                    )
            except Exception as e:
                logger.error(f"Ошибка в очереди: {e}")
                self.root.after(
                    0,
                    lambda l=lbl, n=app_name: l.config(
                        text=f"❌ {n} — Ошибка", fg=DANGER
                    ),
                )

            self.queue.task_done()


# ==============================================================
#                    ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================
def _get_os():
    if sys.platform == "win32":
        return "windows"
    elif sys.platform.startswith("linux"):
        return "linux"
    return "unknown"


def _configure_choco_cache():
    if _get_os() != "windows":
        return
    import os

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


def _parse_catalog():
    """Парсит встроенный каталог из Python-файла."""
    os_type = _get_os()

    if os_type == "windows":
        pkg_key = "choco"
        winget_key = "winget"
        snap_key = None
    elif os_type == "linux":
        pkg_key = "apt"
        winget_key = None
        snap_key = "snap"
    else:
        pkg_key = "choco"
        winget_key = "winget"
        snap_key = None

    groups = {}
    for item in CATALOG:
        cat = item["category"]
        pkg = item.get(pkg_key, "").strip()

        if not pkg:
            continue

        winget_pkg = item.get(winget_key, "").strip() if winget_key else ""
        snap_pkg = item.get(snap_key, "").strip() if snap_key else ""
        is_snap_classic = item.get("snap_classic", False)

        if cat not in groups:
            groups[cat] = []

        groups[cat].append(
            (item["name"], item["desc"], pkg, winget_pkg, snap_pkg, is_snap_classic)
        )

    return groups


def _make_scrollable(parent: tk.Widget) -> tk.Frame:
    container = tk.Frame(parent, bg=BG_ROOT)
    container.pack(fill="both", expand=True)
    canvas = tk.Canvas(container, bg=BG_ROOT, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_ROOT)

    inner.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def _on_canvas_configure(event):
        canvas.itemconfigure(window_id, width=event.width)

    canvas.bind("<Configure>", _on_canvas_configure)

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    return inner


def _make_card(
    parent,
    row,
    col,
    title,
    desc,
    package,
    winget_package,
    snap_package,
    is_snap_classic,
    task_manager,
):
    card = tk.Frame(
        parent,
        bg=BG_CARD,
        padx=18,
        pady=16,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

    header = tk.Frame(card, bg=BG_CARD)
    header.pack(fill="x")
    tk.Label(
        header,
        text=title,
        font=("Segoe UI Semibold", 13),
        bg=BG_CARD,
        fg=FG_TITLE,
        anchor="w",
    ).pack(side="left")

    tk.Label(
        card,
        text=desc,
        font=("Segoe UI", 9),
        bg=BG_CARD,
        fg=FG_MUTED,
        wraplength=250,
        justify="left",
        anchor="w",
    ).pack(fill="x", pady=(8, 16))

    btn = ttk.Button(
        card,
        text="Установить",
        style="Accent.TButton",
        command=lambda n=title, p=package, w=winget_package, s=snap_package, c=is_snap_classic: task_manager.add_task(
            n, p, w, s, c
        ),
    )
    btn.pack(fill="x", side="bottom")

    def on_enter(_):
        card.configure(bg=BG_CARD_HOVER, highlightbackground=ACCENT_DARK)
        header.configure(bg=BG_CARD_HOVER)
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=BG_CARD_HOVER)

    def on_leave(_):
        card.configure(bg=BG_CARD, highlightbackground=BORDER)
        header.configure(bg=BG_CARD)
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=BG_CARD)

    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    return card


def _make_section(parent, title, apps, task_manager, columns=4):
    header = tk.Frame(parent, bg=BG_ROOT)
    header.pack(fill="x", pady=(20, 4), padx=8)
    tk.Label(
        header,
        text=title,
        font=("Segoe UI Semibold", 15),
        bg=BG_ROOT,
        fg=ACCENT,
        anchor="w",
    ).pack(side="left")
    tk.Label(
        header,
        text=f"  {len(apps)} шт.",
        font=("Segoe UI", 10),
        bg=BG_ROOT,
        fg=FG_DIM,
        anchor="w",
    ).pack(side="left", pady=(4, 0))

    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=8, pady=(0, 12))
    grid = tk.Frame(parent, bg=BG_ROOT)
    grid.pack(fill="x", padx=8)

    # Распаковываем 6 элементов
    for i, (t, d, pkg, winget_pkg, snap_pkg, is_snap_classic) in enumerate(apps):
        r, c = divmod(i, columns)
        _make_card(
            grid, r, c, t, d, pkg, winget_pkg, snap_pkg, is_snap_classic, task_manager
        )

    for i in range(columns):
        grid.columnconfigure(i, weight=1, uniform=f"sect{title}")


def _setup_styles():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        "TNotebook", background=BG_ROOT, borderwidth=0, tabmargins=(8, 6, 8, 0)
    )
    style.configure(
        "TNotebook.Tab",
        background=BG_PANEL,
        foreground=FG_MUTED,
        padding=[16, 9],
        borderwidth=0,
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG_ROOT)],
        foreground=[("selected", ACCENT)],
        expand=[("selected", (0, 0, 0, 0))],
    )
    style.configure("TFrame", background=BG_ROOT)
    style.configure(
        "TLabel", background=BG_ROOT, foreground=FG_TEXT, font=("Segoe UI", 10)
    )
    style.configure(
        "TButton",
        background=BG_CARD,
        foreground=FG_TEXT,
        borderwidth=0,
        focusthickness=0,
        padding=(12, 8),
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "TButton",
        background=[("active", BG_CARD_HOVER), ("pressed", BG_INPUT)],
        foreground=[("active", FG_TITLE)],
    )
    style.configure(
        "Accent.TButton",
        background=ACCENT_DARK,
        foreground="#ffffff",
        borderwidth=0,
        focusthickness=0,
        padding=(12, 9),
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT), ("pressed", ACCENT_DARK)],
        foreground=[("active", "#ffffff")],
    )
    style.configure(
        "Danger.TButton",
        background=BG_CARD,
        foreground=DANGER,
        borderwidth=0,
        focusthickness=0,
        padding=(14, 8),
        font=("Segoe UI Semibold", 10),
    )
    style.map(
        "Danger.TButton",
        background=[("active", BG_CARD_HOVER)],
        foreground=[("active", DANGER_HOVER)],
    )
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=BG_INPUT,
        background=ACCENT,
        bordercolor=BG_INPUT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=8,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=BG_PANEL,
        troughcolor=BG_ROOT,
        bordercolor=BG_ROOT,
        arrowcolor=FG_MUTED,
        gripcount=0,
    )
    style.map("Vertical.TScrollbar", background=[("active", BG_CARD_HOVER)])


# ==============================================================
#                    ГЛАВНАЯ ФУНКЦИЯ
# ==============================================================
def start():
    get_admin_permisions()
    _configure_choco_cache()

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1280x850")
    root.minsize(1000, 700)
    root.configure(bg=BG_ROOT)
    root.eval("tk::PlaceWindow . center")

    _setup_styles()

    # --- ВЕРХНЯЯ ПАНЕЛЬ ---
    top_frame = tk.Frame(root, bg=BG_ROOT)
    top_frame.pack(fill="x", padx=28, pady=(20, 10))
    tk.Label(
        top_frame, text="◆", font=("Segoe UI", 22, "bold"), bg=BG_ROOT, fg=ACCENT
    ).pack(side="left")
    title_block = tk.Frame(top_frame, bg=BG_ROOT)
    title_block.pack(side="left", padx=(10, 0))
    tk.Label(
        title_block,
        text=APP_NAME,
        font=("Segoe UI Semibold", 18),
        bg=BG_ROOT,
        fg=FG_TITLE,
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        title_block,
        text=APP_TAGLINE,
        font=("Segoe UI", 9),
        bg=BG_ROOT,
        fg=FG_MUTED,
        anchor="w",
    ).pack(anchor="w")
    tk.Label(
        top_frame,
        text="  ADMIN  ",
        font=("Segoe UI Semibold", 8),
        bg=BG_CARD,
        fg=ACCENT,
        padx=6,
        pady=4,
    ).pack(side="right", pady=8)

    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(6, 0))

    # --- НИЖНЯЯ ПАНЕЛЬ (ОЧЕРЕДЬ И СТАТУС) ---
    bottom_frame = tk.Frame(root, bg=BG_PANEL)

    # 1. Список задач
    task_container = tk.Frame(bottom_frame, bg=BG_PANEL)
    task_container.pack(fill="x", padx=24, pady=(10, 5))
    tk.Label(
        task_container,
        text="ОЧЕРЕДЬ ЗАДАЧ",
        font=("Segoe UI Semibold", 8),
        bg=BG_PANEL,
        fg=FG_DIM,
    ).pack(anchor="w")

    task_list_frame = tk.Frame(task_container, bg=BG_PANEL)
    task_list_frame.pack(fill="x", pady=2)

    # 2. Текущий статус
    status_container = tk.Frame(bottom_frame, bg=BG_PANEL)
    status_container.pack(fill="x", padx=24, pady=(5, 0))
    status_label = tk.Label(
        status_container,
        text="Система готова.",
        font=("Consolas", 10),
        bg=BG_PANEL,
        fg=FG_TEXT,
        anchor="w",
        justify="left",
    )
    status_label.pack(fill="x", pady=(2, 8))

    # 3. Прогресс-бар
    progress_bar = ttk.Progressbar(
        bottom_frame,
        orient="horizontal",
        mode="determinate",
        style="Accent.Horizontal.TProgressbar",
    )
    progress_bar.pack(fill="x", padx=24, pady=(0, 10))

    # Инициализируем менеджер задач
    task_manager = TaskManager(root, status_label, progress_bar, task_list_frame)

    # --- ОСНОВНОЙ КОНТЕНТ ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=22, pady=(14, 6))

    tab_market = ttk.Frame(notebook)
    notebook.add(tab_market, text="  Маркетплейс  ")
    market_frame = _make_scrollable(tab_market)

    catalog_data = _parse_catalog()
    for cat_name, apps in catalog_data.items():
        _make_section(market_frame, cat_name, apps, task_manager, columns=4)

    # Пакуем нижнюю панель в самом конце
    bottom_frame.pack(fill="x", side="bottom", pady=(0, 0))

    ttk.Button(
        bottom_frame, text="Закрыть", style="Danger.TButton", command=root.destroy
    ).pack(side="right", padx=24, pady=(0, 14))

    def toggle_fullscreen(event=None):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    root.mainloop()


if __name__ == "__main__":
    start()
