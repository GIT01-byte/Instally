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
BG_ROOT = "#1e1f29"  # фон окна
BG_PANEL = "#282a36"  # панели, нижний бар
BG_CARD = "#2f313e"  # карточки
BG_CARD_HOVER = "#383a4a"
BG_INPUT = "#21222c"

FG_TITLE = "#f8f8f2"
FG_TEXT = "#d7d7e0"
FG_MUTED = "#8b8d9a"
FG_DIM = "#5f6170"

ACCENT = "#bd93f9"  # основной акцент (фиолет)
ACCENT_HOVER = "#caa9fa"
ACCENT_DARK = "#8a5cf6"

SUCCESS = "#50fa7b"
DANGER = "#ff5555"
DANGER_HOVER = "#ff6e6e"
BORDER = "#3a3c4a"


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

    # Растягиваем inner по ширине canvas
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

    # Верхняя строка: заголовок
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

    # Описание
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

    # Кнопка
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

    # Плавный ховер всей карточки
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


# ==============================================================
#                    СТИЛИЗАЦИЯ ttk
# ==============================================================
def _setup_styles():
    style = ttk.Style()
    style.theme_use("clam")

    # --- Notebook ---
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

    # --- Frame / Label ---
    style.configure("TFrame", background=BG_ROOT)
    style.configure(
        "TLabel", background=BG_ROOT, foreground=FG_TEXT, font=("Segoe UI", 10)
    )

    # --- Обычная кнопка ---
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

    # --- Акцентная кнопка ---
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

    # --- Danger-кнопка (Закрыть) ---
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

    # --- Прогрессбар ---
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=BG_INPUT,
        background=ACCENT,
        bordercolor=BG_INPUT,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=8,
    )

    # --- Скроллбар ---
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

    root = tk.Tk()
    root.title(APP_NAME)
    root.geometry("1120x680")
    root.minsize(900, 560)
    root.configure(bg=BG_ROOT)
    root.eval("tk::PlaceWindow . center")

    _setup_styles()

    # ----------------------------------------------------------
    # ВЕРХНЯЯ ПАНЕЛЬ
    # ----------------------------------------------------------
    top_frame = tk.Frame(root, bg=BG_ROOT)
    top_frame.pack(fill="x", padx=28, pady=(20, 6))

    logo = tk.Label(
        top_frame,
        text="◆",
        font=("Segoe UI", 22, "bold"),
        bg=BG_ROOT,
        fg=ACCENT,
    )
    logo.pack(side="left")

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

    # Бейдж «Администратор»
    badge = tk.Label(
        top_frame,
        text="  ADMIN  ",
        font=("Segoe UI Semibold", 8),
        bg=BG_CARD,
        fg=ACCENT,
        padx=6,
        pady=4,
    )
    badge.pack(side="right", pady=8)

    # Разделитель
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=28, pady=(6, 0))

    # ----------------------------------------------------------
    # НИЖНЯЯ ПАНЕЛЬ (создаём заранее, pack() — в самом конце)
    # ----------------------------------------------------------
    bottom_frame = tk.Frame(root, bg=BG_PANEL)

    status_container = tk.Frame(bottom_frame, bg=BG_PANEL)
    status_container.pack(fill="x", padx=24, pady=(12, 0))

    tk.Label(
        status_container,
        text="СТАТУС",
        font=("Segoe UI Semibold", 8),
        bg=BG_PANEL,
        fg=FG_DIM,
    ).pack(anchor="w")

    status_label = tk.Label(
        status_container,
        text="Система готова. Выберите действие.",
        font=("Consolas", 10),
        bg=BG_PANEL,
        fg=FG_TEXT,
        anchor="w",
        justify="left",
    )
    status_label.pack(fill="x", pady=(2, 8))

    progress_bar = ttk.Progressbar(
        bottom_frame,
        orient="horizontal",
        mode="determinate",
        style="Accent.Horizontal.TProgressbar",
    )
    progress_bar.pack(fill="x", padx=24, pady=(0, 10))

    # ----------------------------------------------------------
    # NOTEBOOK
    # ----------------------------------------------------------
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=22, pady=(14, 6))

    # ==========================================================
    # ВКЛАДКА 1: КАТЕГОРИИ
    # ==========================================================
    tab_install = ttk.Frame(notebook)
    notebook.add(tab_install, text="  Категории  ")
    scrollable_frame = _make_scrollable(tab_install)

    categories = [
        {
            "title": "Базовый софт",
            "desc": "7-Zip, VLC, Chrome",
            "packages": ["7zip", "vlc", "googlechrome"],
            "action": "install",
        },
        {
            "title": "Для разработчика",
            "desc": "Git, VS Code, Python",
            "packages": ["git", "vscode", "python"],
            "action": "install",
        },
        {
            "title": "Обновление системы",
            "desc": "Обновить все установленные программы",
            "packages": ["all"],
            "action": "upgrade",
            "button_text": "Обновить",
        },
        {
            "title": "Браузеры",
            "desc": "Firefox, Opera, Edge",
            "packages": ["firefox", "opera", "microsoft-edge"],
            "action": "install",
        },
        {
            "title": "Мультимедиа",
            "desc": "Spotify, Audacity, GIMP",
            "packages": ["spotify", "audacity", "gimp"],
            "action": "install",
        },
        {
            "title": "Утилиты",
            "desc": "Полезные инструменты системы",
            "packages": ["7zip", "everything", "notepadplusplus"],
            "action": "install",
        },
    ]

    row, col = 0, 0
    for cat in categories:
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

    apps = [
        ("CPU-Z", "Информация о процессоре, памяти, плате", "cpu-z"),
        ("GPU-Z", "Мониторинг видеокарты и её параметров", "gpu-z"),
        ("HWMonitor", "Температуры, вольтажи, вентиляторы", "hwmonitor"),
        ("Speccy", "Подробная информация о железе", "speccy"),
        ("Notepad++", "Продвинутый текстовый редактор", "notepadplusplus"),
        ("WinRAR", "Архиватор RAR / ZIP", "winrar"),
        ("Everything", "Мгновенный поиск файлов по имени", "everything"),
        ("Process Explorer", "Расширенный диспетчер задач", "procexp"),
        ("Chrome", "Браузер Google Chrome", "googlechrome"),
        ("Firefox", "Браузер Mozilla Firefox", "firefox"),
        ("VLC", "Медиаплеер для большинства форматов", "vlc"),
        ("qBittorrent", "Лёгкий торрент-клиент", "qbittorrent"),
    ]

    row, col = 0, 0
    for title, desc, pkg in apps:
        _make_card(
            parent=market_frame,
            row=row,
            col=col,
            title=title,
            desc=desc,
            package=pkg,
            status_label=status_label,
            progress_bar=progress_bar,
        )
        col += 1
        if col > 3:
            col = 0
            row += 1

    for i in range(4):
        market_frame.columnconfigure(i, weight=1, uniform="app")

    # ----------------------------------------------------------
    # ПАКУЕМ НИЖНЮЮ ПАНЕЛЬ В САМОМ КОНЦЕ — она окажется снизу
    # ----------------------------------------------------------
    bottom_frame.pack(fill="x", side="bottom", pady=(0, 0))

    # Кнопка «Закрыть» и хоткей
    ttk.Button(
        bottom_frame,
        text="Закрыть",
        style="Danger.TButton",
        command=root.destroy,
    ).pack(side="right", padx=24, pady=(0, 14))

    # ----------------------------------------------------------
    # ГОРЯЧИЕ КЛАВИШИ
    # ----------------------------------------------------------
    def toggle_fullscreen(event=None):
        root.attributes("-fullscreen", not root.attributes("-fullscreen"))

    root.bind("<F11>", toggle_fullscreen)
    root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

    root.mainloop()


if __name__ == "__main__":
    start()
