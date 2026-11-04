import tkinter as tk
from tkinter import ttk
import sys
from data.catalog import CATALOG
from frontend.ui_config import (
    BG_ROOT,
    BG_PANEL,
    BG_CARD,
    BG_INPUT,
    BORDER,
    ACCENT,
    FG_TITLE,
    FG_TEXT,
    FG_MUTED,
    FG_DIM,
    FONT_LOGO,
    FONT_TITLE,
    FONT_TAGLINE,
    FONT_BADGE,
    FONT_STATUS,
    PAD_WINDOW_X,
    PAD_WINDOW_Y,
    setup_styles,
)
from frontend.components import make_scrollable, make_section
from frontend.task_manager import TaskManager


class AppWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Instally")
        self.root.geometry("1280x850")
        self.root.minsize(1000, 700)
        self.root.configure(bg=BG_ROOT)
        self.root.eval("tk::PlaceWindow . center")

        setup_styles()
        self.catalog_data = self._parse_catalog()
        self.force_reinstall_var = tk.BooleanVar(value=False)
        self._build_ui()

    def _get_os(self):
        if sys.platform == "win32":
            return "windows"
        elif sys.platform.startswith("linux"):
            return "linux"
        return "unknown"

    def _parse_catalog(self):
        os_type = self._get_os()
        if os_type == "windows":
            pkg_key, winget_key, snap_key = "choco", "winget", None
        elif os_type == "linux":
            pkg_key, winget_key, snap_key = "apt", None, "snap"
        else:
            pkg_key, winget_key, snap_key = "choco", "winget", None

        groups = {}
        for item in CATALOG:
            cat = item["category"]
            pkg = item.get(pkg_key, "").strip()
            download_url = item.get("download_url", "").strip()
            if not pkg and not download_url:
                continue
            winget_pkg = item.get(winget_key, "").strip() if winget_key else ""
            snap_pkg = item.get(snap_key, "").strip() if snap_key else ""
            is_snap_classic = item.get("snap_classic", False)
            if cat not in groups:
                groups[cat] = []
            groups[cat].append(
                (
                    item["name"],
                    item["desc"],
                    pkg,
                    winget_pkg,
                    snap_pkg,
                    is_snap_classic,
                    download_url,
                )
            )
        return groups

    def _build_ui(self):
        # --- ВЕРХНЯЯ ПАНЕЛЬ ---
        top_frame = tk.Frame(self.root, bg=BG_ROOT)
        top_frame.pack(fill="x", padx=PAD_WINDOW_X, pady=(PAD_WINDOW_Y, 10))

        tk.Label(top_frame, text="◆", font=FONT_LOGO, bg=BG_ROOT, fg=ACCENT).pack(
            side="left"
        )
        title_block = tk.Frame(top_frame, bg=BG_ROOT)
        title_block.pack(side="left", padx=(10, 0))
        tk.Label(
            title_block,
            text="Instally",
            font=FONT_TITLE,
            bg=BG_ROOT,
            fg=FG_TITLE,
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text="Избавляет вас от рутины установки программ",
            font=FONT_TAGLINE,
            bg=BG_ROOT,
            fg=FG_MUTED,
            anchor="w",
        ).pack(anchor="w")

        # Поиск
        self.search_frame = tk.Frame(
            top_frame,
            bg=BG_INPUT,
            padx=10,
            pady=5,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.search_frame.pack(side="left", padx=40, fill="x", expand=True)
        self.search_frame.bind("<Button-1>", lambda e: self.search_entry.focus_set())

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        self.search_entry = tk.Entry(
            self.search_frame,
            textvariable=self.search_var,
            bg=BG_INPUT,
            fg=FG_MUTED,
            insertbackground=FG_TITLE,
            font=FONT_TAGLINE,
            borderwidth=0,
            highlightthickness=0,
        )
        self.search_entry.pack(fill="x", expand=True)
        self.search_entry.insert(0, "Поиск...")
        self.search_entry.bind("<FocusIn>", self._on_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_focus_out)

        self.root.bind("<Button-1>", self._on_global_click)

        # Чекбокс
        chk = tk.Checkbutton(
            top_frame,
            text="Принудительно",
            variable=self.force_reinstall_var,
            bg=BG_ROOT,
            fg=FG_TEXT,
            selectcolor=BG_INPUT,
            activebackground=BG_ROOT,
            activeforeground=ACCENT,
            font=FONT_TAGLINE,
            borderwidth=0,
            highlightthickness=0,
        )
        chk.pack(side="right", padx=15)

        tk.Label(
            top_frame,
            text="  ADMIN  ",
            font=FONT_BADGE,
            bg=BG_CARD,
            fg=ACCENT,
            padx=6,
            pady=4,
        ).pack(side="right", pady=8)
        tk.Frame(self.root, bg=BORDER, height=1).pack(
            fill="x", padx=PAD_WINDOW_X, pady=(6, 0)
        )

        # --- НИЖНЯЯ ПАНЕЛЬ (ОЧЕРЕДЬ) ---
        bottom_frame = tk.Frame(self.root, bg=BG_PANEL)
        task_container = tk.Frame(bottom_frame, bg=BG_PANEL)
        task_container.pack(fill="x", padx=PAD_WINDOW_X - 4, pady=(10, 5))

        tk.Label(
            task_container,
            text="ОЧЕРЕДЬ ЗАДАЧ",
            font=FONT_BADGE,
            bg=BG_PANEL,
            fg=FG_DIM,
        ).pack(anchor="w")

        queue_wrapper = tk.Frame(task_container, bg=BG_PANEL, height=65)
        queue_wrapper.pack(fill="x", pady=2)
        queue_wrapper.pack_propagate(False)

        self.queue_canvas = tk.Canvas(
            queue_wrapper, bg=BG_PANEL, highlightthickness=0, bd=0
        )
        queue_scroll = ttk.Scrollbar(
            queue_wrapper, orient="vertical", command=self.queue_canvas.yview
        )

        self.task_list_frame = tk.Frame(self.queue_canvas, bg=BG_PANEL)
        self.task_list_frame.bind(
            "<Configure>",
            lambda e: self.queue_canvas.configure(
                scrollregion=self.queue_canvas.bbox("all")
            ),
        )

        window_id = self.queue_canvas.create_window(
            (0, 0), window=self.task_list_frame, anchor="nw"
        )
        self.queue_canvas.bind(
            "<Configure>",
            lambda e: self.queue_canvas.itemconfig(window_id, width=e.width),
        )
        self.queue_canvas.configure(yscrollcommand=queue_scroll.set)

        self.queue_canvas.pack(side="left", fill="both", expand=True)
        queue_scroll.pack(side="right", fill="y")

        # Умный скролл для очереди
        def _on_queue_mousewheel(event):
            x, y = self.queue_canvas.winfo_pointerxy()
            c_x = self.queue_canvas.winfo_rootx()
            c_y = self.queue_canvas.winfo_rooty()
            c_w = self.queue_canvas.winfo_width()
            c_h = self.queue_canvas.winfo_height()

            if c_x <= x <= c_x + c_w and c_y <= y <= c_y + c_h:
                self.queue_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.queue_canvas.bind_all("<MouseWheel>", _on_queue_mousewheel)

        # Статус-бар
        status_container = tk.Frame(bottom_frame, bg=BG_PANEL)
        status_container.pack(fill="x", padx=PAD_WINDOW_X - 4, pady=(5, 0))
        self.status_label = tk.Label(
            status_container,
            text="Система готова.",
            font=FONT_STATUS,
            bg=BG_PANEL,
            fg=FG_TEXT,
            anchor="w",
            justify="left",
        )
        self.status_label.pack(fill="x", pady=(2, 8))

        self.progress_bar = ttk.Progressbar(
            bottom_frame,
            orient="horizontal",
            mode="determinate",
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress_bar.pack(fill="x", padx=PAD_WINDOW_X - 4, pady=(0, 10))

        self.task_manager = TaskManager(
            self.root, self.status_label, self.progress_bar, self.task_list_frame
        )

        # Контент
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=22, pady=(14, 6))
        self.tab_market = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_market, text="  Маркетплейс  ")
        self.market_frame = make_scrollable(self.tab_market)

        self._render_catalog(self.catalog_data)

        bottom_frame.pack(fill="x", side="bottom", pady=(0, 0))

        # Кнопки внизу
        ttk.Button(
            bottom_frame,
            text="Закрыть",
            style="Danger.TButton",
            command=self.root.destroy,
        ).pack(side="right", padx=PAD_WINDOW_X - 4, pady=(0, 14))
        ttk.Button(
            bottom_frame,
            text="Очистить очередь",
            style="TButton",
            command=self._clear_logs,
        ).pack(side="right", padx=10, pady=(0, 14))

        self.root.bind(
            "<F11>",
            lambda e: self.root.attributes(
                "-fullscreen", not self.root.attributes("-fullscreen")
            ),
        )
        self.root.bind("<Escape>", lambda e: self.root.attributes("-fullscreen", False))

    def _on_global_click(self, event):
        if event.widget != self.search_entry:
            self.root.focus_set()

    def _on_focus_in(self, e):
        if self.search_entry.get() == "Поиск...":
            self.search_entry.delete(0, "end")
            self.search_entry.config(fg=FG_TITLE)

    def _on_focus_out(self, e):
        if not self.search_entry.get().strip():
            self.search_entry.delete(0, "end")
            self.search_entry.insert(0, "Поиск...")
            self.search_entry.config(fg=FG_MUTED)

    def _clear_logs(self):
        self.status_label.config(text="Система готова.", fg=FG_TEXT)
        self.progress_bar.config(value=0)
        self.task_manager.clear_all()
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

    def _render_catalog(self, data):
        for widget in self.market_frame.winfo_children():
            widget.destroy()
        if not data:
            tk.Label(
                self.market_frame,
                text="Ничего не найдено",
                font=FONT_TITLE,
                bg=BG_ROOT,
                fg=FG_MUTED,
            ).pack(pady=50)
            return
        for cat_name, apps in data.items():
            make_section(
                self.market_frame,
                cat_name,
                apps,
                self.task_manager,
                self.force_reinstall_var,
                columns=4,
            )

    def _on_search(self, *args):
        if not hasattr(self, "market_frame"):
            return

        text = self.search_var.get()

        if not text.strip() or text == "Поиск...":
            self._render_catalog(self.catalog_data)
            return

        query = text.lower().strip()
        filtered_data = {}
        for cat, apps in self.catalog_data.items():
            for app in apps:
                name, desc = app[0], app[1]
                if query in name.lower() or query in desc.lower():
                    if cat not in filtered_data:
                        filtered_data[cat] = []
                    filtered_data[cat].append(app)

        self._render_catalog(filtered_data)
