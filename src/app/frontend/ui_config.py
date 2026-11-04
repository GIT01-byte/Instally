from tkinter import ttk

# ==============================================================
#                    ДИЗАЙН-СИСТЕМА (ЦВЕТА)
# ==============================================================
BG_ROOT = "#282a36"  # Основной фон (чуть светлее)
BG_PANEL = "#1e1f29"  # Панель задач (темнее, чтобы выделяться)
BG_CARD = "#343746"  # Карточки (мягкий серо-фиолетовый)
BG_CARD_HOVER = "#42455a"  # Ховер карточки
BG_INPUT = "#1e1f29"

FG_TITLE = "#f8f8f2"
FG_TEXT = "#d7d7e0"
FG_MUTED = "#8b8d9a"
FG_DIM = "#5f6170"

ACCENT = "#bd93f9"
ACCENT_HOVER = "#caa9fa"
ACCENT_DARK = "#8a5cf6"

SUCCESS = "#50fa7b"
WARNING = "#f1fa8c"
DANGER = "#ff5555"
DANGER_HOVER = "#ff6e6e"
BORDER = "#44475a"  # Мягкая рамка

# ==============================================================
#                    ДИЗАЙН-СИСТЕМА (ШРИФТЫ)
# ==============================================================
FONT_LOGO = ("Segoe UI", 22, "bold")
FONT_TITLE = ("Segoe UI Semibold", 18)
FONT_TAGLINE = ("Segoe UI", 9)
FONT_BADGE = ("Segoe UI Semibold", 8)

FONT_SECTION = ("Segoe UI Semibold", 15)
FONT_SECTION_COUNT = ("Segoe UI", 10)

FONT_CARD_TITLE = ("Segoe UI Semibold", 13)
FONT_CARD_DESC = ("Segoe UI", 9)

FONT_STATUS = ("Consolas", 10)
FONT_BUTTON = ("Segoe UI Semibold", 10)

# ==============================================================
#                    ДИЗАЙН-СИСТЕМА (ОТСТУПЫ)
# ==============================================================
PAD_WINDOW_X = 28
PAD_WINDOW_Y = 20
PAD_CARD_X = 18
PAD_CARD_Y = 16
PAD_CARD_GRID = 10
PAD_SECTION_X = 8
PAD_SECTION_Y = 20


def setup_styles():
    style = ttk.Style()
    style.theme_use("clam")

    # Вкладки (Notebook)
    style.configure(
        "TNotebook", background=BG_ROOT, borderwidth=0, tabmargins=(8, 6, 8, 0)
    )
    style.configure(
        "TNotebook.Tab",
        background=BG_PANEL,
        foreground=FG_MUTED,
        padding=[16, 9],
        borderwidth=0,
        font=FONT_BUTTON,
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", BG_ROOT)],
        foreground=[("selected", ACCENT)],
        expand=[("selected", (0, 0, 0, 0))],
    )

    # Базовые элементы
    style.configure("TFrame", background=BG_ROOT)
    style.configure(
        "TLabel", background=BG_ROOT, foreground=FG_TEXT, font=FONT_SECTION_COUNT
    )

    # Обычные кнопки (Закрыть, Очистить)
    style.configure(
        "TButton",
        background=BG_PANEL,
        foreground=FG_TEXT,
        borderwidth=0,
        focusthickness=0,
        padding=(12, 8),
        font=FONT_BUTTON,
    )
    style.map(
        "TButton",
        background=[("active", BG_CARD_HOVER), ("pressed", BG_INPUT)],
        foreground=[("active", FG_TITLE)],
    )

    # Акцентные кнопки (Установить)
    style.configure(
        "Accent.TButton",
        background=ACCENT_DARK,
        foreground="#ffffff",
        borderwidth=0,
        focusthickness=0,
        padding=(12, 9),
        font=FONT_BUTTON,
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT), ("pressed", ACCENT_DARK)],
        foreground=[("active", "#ffffff")],
    )

    # Кнопки опасных действий (Закрыть)
    style.configure(
        "Danger.TButton",
        background=BG_PANEL,
        foreground=DANGER,
        borderwidth=0,
        focusthickness=0,
        padding=(14, 8),
        font=FONT_BUTTON,
    )
    style.map(
        "Danger.TButton",
        background=[("active", BG_CARD_HOVER)],
        foreground=[("active", DANGER_HOVER)],
    )

    # Прогресс-бар
    style.configure(
        "Accent.Horizontal.TProgressbar",
        troughcolor=BG_PANEL,
        background=ACCENT,
        bordercolor=BG_PANEL,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
        thickness=4,
    )

    # СКРОЛЛБАР (Тонкий и аккуратный)
    style.configure(
        "Vertical.TScrollbar",
        background=BG_ROOT,
        troughcolor=BG_ROOT,
        bordercolor=BG_ROOT,
        arrowcolor=BG_ROOT,  # Прячем стрелки
        gripcount=0,
        width=8,
    )  # Делаем тонким
    style.map("Vertical.TScrollbar", background=[("active", BORDER)])
