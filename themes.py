import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional


class ThemeManager:
    """
    Менеджер тем для Tkinter приложения.
    Поддерживает светлую и темную темы с настраиваемыми стилями.
    """

    def __init__(self):
        self.current_theme = "light"
        self.themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme()
        }
        self.style = ttk.Style()

    def _get_light_theme(self) -> Dict[str, Any]:
        """Возвращает параметры светлой темы."""
        return {
            "name": "light",
            "colors": {
                "primary": "#4a6fa5",
                "secondary": "#6c757d",
                "success": "#28a745",
                "danger": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8",
                "bg": "#f8f9fa",
                "fg": "#212529",
                "entry_bg": "#ffffff",
                "select_bg": "#e2e6ea",
                "select_fg": "#000000",
                "border": "#ced4da",
                "button_bg": "#e9ecef",
                "button_active": "#d3d9df",
                "text_bg": "#ffffff"
            },
            "fonts": {
                "default": ("Segoe UI", 10),
                "heading": ("Segoe UI", 12, "bold"),
                "title": ("Segoe UI", 14, "bold")
            }
        }

    def _get_dark_theme(self) -> Dict[str, Any]:
        """Возвращает параметры темной темы."""
        return {
            "name": "dark",
            "colors": {
                "primary": "#5a86c2",
                "secondary": "#5c636a",
                "success": "#2ecc71",
                "danger": "#e74c3c",
                "warning": "#f39c12",
                "info": "#3498db",
                "bg": "#2d2d2d",
                "fg": "#e0e0e0",
                "entry_bg": "#1e1e1e",
                "select_bg": "#3d3d3d",
                "select_fg": "#ffffff",
                "border": "#444444",
                "button_bg": "#3d3d3d",
                "button_active": "#4d4d4d",
                "text_bg": "#252525"
            },
            "fonts": {
                "default": ("Segoe UI", 10),
                "heading": ("Segoe UI", 12, "bold"),
                "title": ("Segoe UI", 14, "bold")
            }
        }

    def setup_themes(self):
        """Инициализирует все стили для виджетов."""
        for theme in self.themes.values():
            self._configure_theme(theme)

    def _configure_theme(self, theme: Dict[str, Any]):
        """Настраивает стили для конкретной темы."""
        colors = theme["colors"]
        fonts = theme["fonts"]

        # Базовые настройки
        self.style.theme_create(theme["name"], parent="alt")
        self.style.theme_use(theme["name"])

        # Общие параметры
        self.style.configure(".",
            background=colors["bg"],
            foreground=colors["fg"],
            font=fonts["default"],
            borderwidth=1
        )

        # Frame
        self.style.configure("TFrame", background=colors["bg"])

        # Label
        self.style.configure("TLabel",
            background=colors["bg"],
            foreground=colors["fg"]
        )

        # Entry
        self.style.configure("TEntry",
            fieldbackground=colors["entry_bg"],
            foreground=colors["fg"],
            insertcolor=colors["fg"],
            bordercolor=colors["border"],
            lightcolor=colors["border"],
            darkcolor=colors["border"]
        )

        # Button
        self.style.configure("TButton",
            background=colors["button_bg"],
            foreground=colors["fg"],
            bordercolor=colors["border"],
            focusthickness=3,
            focuscolor=colors["primary"]
        )
        self.style.map("TButton",
            background=[("active", colors["button_active"])],
            foreground=[("active", colors["fg"])]
        )

        # Treeview
        self.style.configure("Treeview",
            background=colors["entry_bg"],
            foreground=colors["fg"],
            fieldbackground=colors["entry_bg"],
            rowheight=25
        )
        self.style.configure("Treeview.Heading",
            background=colors["button_bg"],
            foreground=colors["fg"],
            font=fonts["heading"]
        )
        self.style.map("Treeview",
            background=[("selected", colors["select_bg"])],
            foreground=[("selected", colors["select_fg"])]
        )

    def toggle_theme(self) -> Dict[str, Any]:
        """Переключает между светлой и темной темой и возвращает текущую тему."""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.style.theme_use(self.current_theme)
        return self.themes[self.current_theme]

    def get_current_theme(self) -> Dict[str, Any]:
        """Возвращает параметры текущей темы."""
        return self.themes[self.current_theme]

    def get_style(self, style_name: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает конфигурацию стиля для текущей темы.
        (Может быть расширен для возврата кастомных стилей.)
        """
        # Пример: если нужно получить стиль кнопки
        if style_name == "Action.TButton":
            current_theme = self.get_current_theme()
            return {
                "background": current_theme["colors"]["button_bg"],
                "foreground": current_theme["colors"]["fg"],
                "font": current_theme["fonts"]["default"],
                "padding": 5
            }
        return None