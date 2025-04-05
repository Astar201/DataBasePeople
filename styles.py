from typing import Dict, Any
from themes import ThemeManager


class AppStyles:
    """
    Класс для управления стилями элементов приложения
    """

    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        self.styles: Dict[str, Dict[str, Any]] = {
            'Main.TFrame': {'background': 'colors.bg'},
            'Header.TLabel': {
                'font': 'fonts.heading',
                'background': 'colors.bg',
                'foreground': 'colors.primary'
            },
            'Action.TButton': {
                'font': 'fonts.default',
                'padding': 5,
                'background': 'colors.button_bg',
                'foreground': 'colors.fg'
            },
            'Login.TLabel': {'font': 'fonts.default'},
            'Login.TButton': {
                'font': 'fonts.default',
                'padding': 5
            },
            'Login.TEntry': {
                'font': 'fonts.default',
                'padding': 5
            },
            'Treeview.Heading': {
                'font': 'fonts.heading',
                'background': 'colors.button_bg',
                'foreground': 'colors.fg'
            }
        }

    def setup_styles(self):
        """Применяет все стили к виджетам"""
        current_theme = self.theme_manager.get_current_theme()

        for style_name, style_config in self.styles.items():
            resolved_config = {}
            for key, value in style_config.items():
                # Разрешаем ссылки на colors и fonts
                if isinstance(value, str) and value.startswith('colors.'):
                    color_key = value.split('.')[1]
                    resolved_config[key] = current_theme['colors'][color_key]
                elif isinstance(value, str) and value.startswith('fonts.'):
                    font_key = value.split('.')[1]
                    resolved_config[key] = current_theme['fonts'][font_key]
                else:
                    resolved_config[key] = value

            self.theme_manager.style.configure(style_name, **resolved_config)