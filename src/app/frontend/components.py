import tkinter as tk
from tkinter import ttk
from frontend.ui_config import (
    BG_ROOT,
    BG_CARD,
    BG_CARD_HOVER,
    BORDER,
    ACCENT,
    ACCENT_DARK,
    FG_TITLE,
    FG_MUTED,
    FG_DIM,
    FONT_SECTION,
    FONT_SECTION_COUNT,
    FONT_CARD_TITLE,
    FONT_CARD_DESC,
    PAD_CARD_X,
    PAD_CARD_Y,
    PAD_CARD_GRID,
    PAD_SECTION_X,
    PAD_SECTION_Y,
)


def make_scrollable(parent: tk.Widget) -> tk.Frame:
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

    canvas.bind(
        "<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width)
    )
    canvas.bind_all(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
    )
    return inner


def make_card(
    parent,
    row,
    col,
    title,
    desc,
    package,
    winget_package,
    snap_package,
    is_snap_classic,
    download_url,
    task_manager,
    force_var,
):
    card = tk.Frame(
        parent,
        bg=BG_CARD,
        padx=PAD_CARD_X,
        pady=PAD_CARD_Y,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    card.grid(
        row=row, column=col, padx=PAD_CARD_GRID, pady=PAD_CARD_GRID, sticky="nsew"
    )

    header = tk.Frame(card, bg=BG_CARD)
    header.pack(fill="x")
    tk.Label(
        header, text=title, font=FONT_CARD_TITLE, bg=BG_CARD, fg=FG_TITLE, anchor="w"
    ).pack(side="left")

    tk.Label(
        card,
        text=desc,
        font=FONT_CARD_DESC,
        bg=BG_CARD,
        fg=FG_MUTED,
        wraplength=250,
        justify="left",
        anchor="w",
    ).pack(fill="x", pady=(8, 16))

    btn_text = "Скачать ZIP" if download_url else "Установить"

    btn = ttk.Button(
        card,
        text=btn_text,
        style="Accent.TButton",
        command=lambda n=title, p=package, w=winget_package, s=snap_package, c=is_snap_classic, u=download_url, f=force_var: task_manager.add_task(
            n, p, w, s, c, u, force=f.get()
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


def make_section(parent, title, apps, task_manager, force_var, columns=4):
    header = tk.Frame(parent, bg=BG_ROOT)
    header.pack(fill="x", pady=(PAD_SECTION_Y, 4), padx=PAD_SECTION_X)
    tk.Label(
        header, text=title, font=FONT_SECTION, bg=BG_ROOT, fg=ACCENT, anchor="w"
    ).pack(side="left")
    tk.Label(
        header,
        text=f"  {len(apps)} шт.",
        font=FONT_SECTION_COUNT,
        bg=BG_ROOT,
        fg=FG_DIM,
        anchor="w",
    ).pack(side="left", pady=(4, 0))

    tk.Frame(parent, bg=BORDER, height=1).pack(
        fill="x", padx=PAD_SECTION_X, pady=(0, 12)
    )
    grid = tk.Frame(parent, bg=BG_ROOT)
    grid.pack(fill="x", padx=PAD_SECTION_X)

    for i, (
        t,
        d,
        pkg,
        winget_pkg,
        snap_pkg,
        is_snap_classic,
        download_url,
    ) in enumerate(apps):
        r, c = divmod(i, columns)
        make_card(
            grid,
            r,
            c,
            t,
            d,
            pkg,
            winget_pkg,
            snap_pkg,
            is_snap_classic,
            download_url,
            task_manager,
            force_var,
        )

    for i in range(columns):
        grid.columnconfigure(i, weight=1, uniform=f"sect{title}")
