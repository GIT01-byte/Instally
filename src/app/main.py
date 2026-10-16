import tkinter as tk
from tkinter import ttk

from utils.os_handling import get_admin_permisions
from service.installer import install

# ==============================================================
#                    НАСТРОЙКИ ПРИЛОЖЕНИЯ
# ==============================================================
APP_NAME = "Instally"
APP_TAGLINE = "Избавляет вас от рутины установки программ"

# ==============================================================
#                    ЦВЕТОВАЯ СХЕМА (Dracula-ish)
# ==============================================================
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


# ==============================================================
#                    ДАННЫЕ: КАТЕГОРИИ
# ==============================================================
CATEGORIES = [
    {"title": "Базовый софт", "desc": "7-Zip, VLC, Chrome, Firefox",
     "packages": ["7zip", "vlc", "googlechrome", "firefox"], "action": "install"},
    {"title": "Для разработчика", "desc": "Git, VS Code, Python, DBeaver",
     "packages": ["git", "vscode", "python", "dbeaver"], "action": "install"},
    {"title": "Сисадмину", "desc": "Sysinternals, MobaXterm, WinSCP, PuTTY",
     "packages": ["sysinternals", "mobaxterm", "winscp", "putty"], "action": "install"},
    {"title": "Офисный пакет", "desc": "LibreOffice, Adobe Reader, 7-Zip",
     "packages": ["libreoffice-fresh", "adobereader", "7zip"], "action": "install"},
    {"title": "Мультимедиа", "desc": "VLC, GIMP, Inkscape, Audacity, OBS",
     "packages": ["vlc", "gimp", "inkscape", "audacity", "obs-studio"], "action": "install"},
    {"title": "Графика и 3D", "desc": "GIMP, Inkscape, Blender",
     "packages": ["gimp", "inkscape", "blender"], "action": "install"},
    {"title": "Браузеры", "desc": "Firefox, Opera, Edge, Chrome",
     "packages": ["firefox", "opera", "microsoft-edge", "googlechrome"], "action": "install"},
    {"title": "Для преподавания", "desc": "Scratch, Thonny, GeoGebra, Maxima",
     "packages": ["scratch", "thonny", "geogebra", "maxima"], "action": "install"},
    {"title": "Диагностика системы", "desc": "CPU-Z, GPU-Z, HWMonitor, Speccy",
     "packages": ["cpu-z", "gpu-z", "hwmonitor", "speccy"], "action": "install"},
    {"title": "Виртуализация", "desc": "VirtualBox, Docker Desktop, GNS3",
     "packages": ["virtualbox", "docker-desktop", "gns3"], "action": "install"},
    {"title": "Обновление системы", "desc": "Обновить все установленные программы",
     "packages": ["all"], "action": "upgrade", "button_text": "Обновить"},
]


# ==============================================================
#                    ДАННЫЕ: МАРКЕТПЛЕЙС (группы)
# ==============================================================
MARKETPLACE_GROUPS = [
    ("🛠  Администрирование и мониторинг", [
        ("PowerShell 7",        "Современная оболочка и язык сценариев",   "powershell-core"),
        ("Sysinternals Suite",  "Набор утилит Microsoft для диагностики",  "sysinternals"),
        ("Process Explorer",    "Расширенный диспетчер задач",             "procexp"),
        ("PsTools",             "Консольные утилиты Sysinternals",         "pstools"),
        ("MobaXterm",           "SSH/RDP/VNC-терминал",                    "mobaxterm"),
        ("WinSCP",              "SFTP/SCP/FTP-клиент",                     "winscp"),
        ("PuTTY",               "Классический SSH/Telnet-клиент",          "putty"),
        ("Windows Admin Center","Веб-панель управления серверами",         "windows-admin-center"),
        ("Zabbix Agent",        "Агент системы мониторинга Zabbix",        "zabbix-agent"),
    ]),

    ("💻 Разработка", [
        ("Python 3",            "Интерпретатор Python",                    "python"),
        ("Git",                 "Система контроля версий",                 "git"),
        ("VS Code",             "Редактор кода от Microsoft",              "vscode"),
        ("Visual Studio 2022",  "IDE для .NET, C++, C#",                   "visualstudio2022community"),
        ("IntelliJ IDEA CE",    "IDE для Java и JVM-языков",               "intellijidea-community"),
        ("PyCharm CE",          "IDE для Python",                          "pycharm-community"),
        ("Code::Blocks",        "IDE для C/C++",                           "codeblocks"),
        ("Qt Creator",          "IDE для C++/Qt",                          "qtcreator"),
        ("Android Studio",      "IDE для Android-разработки",              "androidstudio"),
        ("DBeaver",             "Универсальный клиент БД",                 "dbeaver"),
        ("MySQL",               "СУБД MySQL",                              "mysql"),
        ("MariaDB",             "СУБД MariaDB",                            "mariadb"),
        ("Nginx",               "Веб-сервер и reverse-proxy",              "nginx"),
        ("Docker Desktop",      "Контейнеризация",                         "docker-desktop"),
        ("VirtualBox",          "Виртуальные машины",                      "virtualbox"),
        ("GNS3",                "Симулятор сетей",                         "gns3"),
    ]),

    ("📄 Офис и документы", [
        ("LibreOffice",         "Свободный офисный пакет",                 "libreoffice-fresh"),
        ("Adobe Reader",        "Просмотр PDF",                            "adobereader"),
        ("Notepad++",           "Продвинутый текстовый редактор",          "notepadplusplus"),
        ("7-Zip",               "Архиватор",                               "7zip"),
        ("WinRAR",              "Архиватор RAR/ZIP",                       "winrar"),
        ("Everything",          "Мгновенный поиск файлов",                 "everything"),
    ]),

    ("🎨 Мультимедиа и графика", [
        ("VLC",                 "Медиаплеер для всех форматов",            "vlc"),
        ("Spotify",             "Музыкальный стриминг",                    "spotify"),
        ("Audacity",            "Аудиоредактор",                           "audacity"),
        ("OBS Studio",          "Запись и стриминг экрана",                "obs-studio"),
        ("GIMP",                "Растровый графический редактор",          "gimp"),
        ("Inkscape",            "Векторный графический редактор",          "inkscape"),
        ("Blender",             "3D-моделирование и анимация",             "blender"),
    ]),

    ("🎓 Образование", [
        ("Scratch",             "Визуальное программирование",             "scratch"),
        ("Thonny",              "Python-IDE для начинающих",               "thonny"),
        ("GeoGebra",            "Математическая визуализация",             "geogebra"),
        ("Maxima",              "Система компьютерной алгебры",            "maxima"),
        ("RustDesk",            "Удалённое управление компьютером",        "rustdesk"),
    ]),

    ("🔍 Диагностика и браузеры", [
        ("CPU-Z",               "Информация о CPU и памяти",               "cpu-z"),
        ("GPU-Z",               "Информация о видеокарте",                 "gpu-z"),
        ("HWMonitor",           "Температуры и вольтажи",                  "hwmonitor"),
        ("Speccy",              "Подробная информация о железе",           "speccy"),
        ("Chrome",              "Браузер Google Chrome",                   "googlechrome"),
        ("Firefox",             "Браузер Mozilla Firefox",                 "firefox"),
        ("Opera",               "Браузер Opera",                           "opera"),
        ("Edge",                "Браузер Microsoft Edge",                  "microsoft-edge"),
        ("qBittorrent",         "Торрент-клиент",                          "qbittorrent"),
    ]),
]

# ==============================================================
#                    НАСТРОЙКИ CHOCO
# ==============================================================
CHOCO_CACHE_DIR = r"C:\ChocolateyCache"


def _configure_choco_cache():
    """Устанавливает папку кэша Chocolatey. Требует прав администратора."""
    import subprocess
    import os
    import sys

    CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0

    try:
        os.makedirs(CHOCO_CACHE_DIR, exist_ok=True)
    except OSError:
        pass  # если не удалось создать — choco ругнётся сам

    choco_path = r"C:\ProgramData\chocolatey\bin\choco.exe"
    if not os.path.exists(choco_path):
        choco_path = "choco"  # fallback на PATH

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
        pass  # тихо игнорируем — не критично для работы UI

# ==============================================================
#                    ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==============================================================
def _make_scrollable(parent: tk.Widget) -> tk.Frame:
    """Canvas + Scrollbar + возвращает вложенный Frame для карточек."""
    container = tk.Frame(parent, bg=BG_ROOT)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container, bg=BG_ROOT, highlightthickness=0, bd=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_ROOT)

    inner.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
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
    package=None,
    status_label=None,
    progress_bar=None,
    action="install",
    packages=None,
    button_text="Установить",
):
    """Универсальная карточка с заголовком, описанием и кнопкой действия."""
    card = tk.Frame(
        parent,
        bg=BG_CARD,
        padx=18,
        pady=16,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    header = tk.Frame(card, bg=BG_CARD)
    header.pack(fill="x")

    tk.Label(
        header,
        text=title,
        font=("Segoe UI Semibold", 12),
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
        wraplength=240,
        justify="left",
        anchor="w",
    ).pack(fill="x", pady=(6, 14))

    pkg_list = packages if packages is not None else ([package] if package else [])
    args = ["-y"] if action == "install" else []

    ttk.Button(
        card,
        text=button_text,
        style="Accent.TButton",
        command=lambda a=action, p=pkg_list: install(
            action=a,
            ttk_log_widget=status_label,
            ttk_progress_bar=progress_bar,
            packages=p,
            args=args,
        ),
    ).pack(fill="x")

    def on_enter(_):
        card.configure(bg=BG_CARD_HOVER)
        for w in (card, header):
            w.configure(bg=BG_CARD_HOVER)
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=BG_CARD_HOVER)

    def on_leave(_):
        card.configure(bg=BG_CARD)
        header.configure(bg=BG_CARD)
        for w in card.winfo_children():
            if isinstance(w, tk.Label):
                w.configure(bg=BG_CARD)

    card.bind("<Enter>", on_enter)
    card.bind("<Leave>", on_leave)
    return card


def _make_section(parent, title, apps, status_label, progress_bar, columns=4):
    """Секция с заголовком и сеткой карточек."""
    header = tk.Frame(parent, bg=BG_ROOT)
    header.pack(fill="x", pady=(20, 4), padx=6)
    tk.Label(
        header, text=title,
        font=("Segoe UI Semibold", 13),
        bg=BG_ROOT, fg=ACCENT, anchor="w",
    ).pack(side="left")
    tk.Label(
        header, text=f"  {len(apps)} шт.",
        font=("Segoe UI", 9),
        bg=BG_ROOT, fg=FG_DIM, anchor="w",
    ).pack(side="left", pady=(4, 0))

    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=6, pady=(0, 10))

    grid = tk.Frame(parent, bg=BG_ROOT)
    grid.pack(fill="x", padx=2)

    for i, (t, d, pkg) in enumerate(apps):
        r, c = divmod(i, columns)
        _make_card(
            parent=grid, row=r, col=c,
            title=t, desc=d, package=pkg,
            status_label=status_label, progress_bar=progress_bar,
        )

    for i in range(columns):
        grid.columnconfigure(i, weight=1, uniform=f"sect{title}")


# ==============================================================
#                    СТИЛИЗАЦИЯ ttk
# ==============================================================
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
    style.map(
        "Vertical.TScrollbar",
        background=[("active", BG_CARD_HOVER)],
    )


# ==============================================================
#                    ГЛАВНАЯ ФУНКЦИЯ
# ==============================================================
def start():
    get_admin_permisions()
    _configure_choco_cache()

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1120x680")
    root.minsize(900, 560)
    root.configure(bg=BG_ROOT)
    root.eval("tk::PlaceWindow . center")

    _setup_styles()

    # --- ВЕРХНЯЯ ПАНЕЛЬ ---
    top_frame = tk.Frame(root, bg=BG_ROOT)
    top_frame.pack(fill="x", padx=28, pady=(20, 6))

    tk.Label(
        top_frame, text="◆",
        font=("Segoe UI", 22, "bold"),
        bg=BG_ROOT, fg=ACCENT,
    ).pack(side="left")

    title_block = tk.Frame(top_frame, bg=BG_ROOT)
    title_block.pack(side="left", padx=(10, 0))

    tk.Label(
        title_block, text=APP_NAME,
        font=("Segoe UI Semibold", 18),
        bg=BG_ROOT, fg=FG_TITLE, anchor="w",
    ).pack(anchor="w")
    tk.Label(
        title_block, text=APP_TAGLINE,
        font=("Segoe UI", 9),
        bg=BG_ROOT, fg=FG_MUTED, anchor="w",
    ).pack(anchor="w")

    tk.Label(
        top_frame, text="  ADMIN  ",
        font=("Segoe UI Semibold", 8),
        bg=BG_CARD, fg=ACCENT, padx=6, pady=4,
    ).pack(side="right", pady=8)

    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(6, 0))

    # --- НИЖНЯЯ ПАНЕЛЬ (создаём заранее) ---
    bottom_frame = tk.Frame(root, bg=BG_PANEL)

    status_container = tk.Frame(bottom_frame, bg=BG_PANEL)
    status_container.pack(fill="x", padx=24, pady=(12, 0))

    tk.Label(
        status_container, text="СТАТУС",
        font=("Segoe UI Semibold", 8),
        bg=BG_PANEL, fg=FG_DIM,
    ).pack(anchor="w")

    status_label = tk.Label(
        status_container,
        text="Система готова. Выберите действие.",
        font=("Consolas", 10),
        bg=BG_PANEL, fg=FG_TEXT,
        anchor="w", justify="left",
    )
    status_label.pack(fill="x", pady=(2, 8))

    progress_bar = ttk.Progressbar(
        bottom_frame, orient="horizontal",
        mode="determinate", style="Accent.Horizontal.TProgressbar",
    )
    progress_bar.pack(fill="x", padx=24, pady=(0, 10))

    # --- NOTEBOOK ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=22, pady=(14, 6))

    # ==========================================================
    # ВКЛАДКА 1: КАТЕГОРИИ
    # ==========================================================
    tab_install = ttk.Frame(notebook)
    notebook.add(tab_install, text="  Категории  ")
    scrollable_frame = _make_scrollable(tab_install)

    row, col = 0, 0
    for cat in CATEGORIES:
        _make_card(
            parent=scrollable_frame,
            row=row,
            col=col,
            title=cat["title"],
            desc=cat["desc"],
            packages=cat["packages"],
            action=cat.get("action", "install"),
            status_label=status_label,
            progress_bar=progress_bar,
            button_text=cat.get("button_text", "Выполнить"),
        )
        col += 1
        if col > 2:
            col = 0
            row += 1

    for i in range(3):
        scrollable_frame.columnconfigure(i, weight=1, uniform="cat")

    # ==========================================================
    # ВКЛАДКА 2: МАРКЕТПЛЕЙС
    # ==========================================================
    tab_market = ttk.Frame(notebook)
    notebook.add(tab_market, text="  Маркетплейс  ")
    market_frame = _make_scrollable(tab_market)

    for group_title, group_apps in MARKETPLACE_GROUPS:
        _make_section(
            parent=market_frame,
            title=group_title,
            apps=group_apps,
            status_label=status_label,
            progress_bar=progress_bar,
            columns=4,
        )

    # --- ПАКУЕМ НИЖНЮЮ ПАНЕЛЬ В КОНЦЕ ---
    bottom_frame.pack(fill="x", side="bottom", pady=(0, 0))

    ttk.Button(
        bottom_frame, text="Закрыть", style="Danger.TButton",
        command=root.destroy,
    ).pack(side="right", padx=24, pady=(0, 14))

    # --- ГОРЯЧИЕ КЛАВИШИ ---
    def toggle_fullscreen(event=None):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    root.mainloop()


if __name__ == "__main__":
    start()