import tkinter as tk


class ActivityRings(tk.Canvas):
    def __init__(self, parent, width=300, height=300, bg="#1e1f29"):
        super().__init__(
            parent, width=width, height=height, bg=bg, highlightthickness=0
        )
        self.width = width
        self.height = height
        self.center_x = width / 2
        self.center_y = height / 2

        # Параметры колец
        self.ring_thickness = 18
        self.gap = 4

        self.r1 = min(width, height) / 2 - 15  # Внешнее (Красное - Ошибки)
        self.r2 = (
            self.r1 - self.ring_thickness - self.gap
        )  # Среднее (Желтое - Fallback)
        self.r3 = self.r2 - self.ring_thickness - self.gap  # Внутреннее (Зеленое - OK)

    def draw(self, ok_count, warn_count, error_count):
        self.delete("all")
        total = ok_count + warn_count + error_count
        if total == 0:
            total = 1  # Защита от деления на ноль

        # Фоновые кольца (темно-серые)
        self._draw_ring(self.center_x, self.center_y, self.r1, 360, "#333544")
        self._draw_ring(self.center_x, self.center_y, self.r2, 360, "#333544")
        self._draw_ring(self.center_x, self.center_y, self.r3, 360, "#333544")

        # Рисуем активные кольца (снизу вверх, чтобы перекрывали друг друга красиво)
        # 1. Внутреннее - Зеленое (Успешно)
        if ok_count > 0:
            angle = (ok_count / total) * 360
            self._draw_ring(self.center_x, self.center_y, self.r3, -angle, "#50fa7b")

        # 2. Среднее - Желтое (Найдено только в Fallback)
        if warn_count > 0:
            angle = (warn_count / total) * 360
            self._draw_ring(self.center_x, self.center_y, self.r2, -angle, "#f1fa8c")

        # 3. Внешнее - Красное (Ошибки)
        if error_count > 0:
            angle = (error_count / total) * 360
            self._draw_ring(self.center_x, self.center_y, self.r1, -angle, "#ff5555")

        # Текст по центру
        self.create_text(
            self.center_x,
            self.center_y - 10,
            text="Тест",
            fill="#8b8d9a",
            font=("Segoe UI", 12),
        )
        self.create_text(
            self.center_x,
            self.center_y + 15,
            text=f"{total} шт.",
            fill="#f8f8f2",
            font=("Segoe UI Semibold", 16),
        )

    def _draw_ring(self, cx, cy, radius, extent, color):
        bbox = (cx - radius, cy - radius, cx + radius, cy + radius)
        self.create_arc(
            bbox,
            start=90,
            extent=extent,
            style=tk.ARC,
            outline=color,
            width=self.ring_thickness,
        )
