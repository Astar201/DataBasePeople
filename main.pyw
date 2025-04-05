import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime
import hashlib
import sys
import logging
import io
import os
import shutil
from typing import Optional, Dict, List

# Инициализация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# Поддержка datetime в SQLite
def adapt_datetime(dt):
    return dt.isoformat()


def convert_datetime(text):
    return datetime.fromisoformat(text.decode())


sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)


class ThemeManager:
    def __init__(self):
        self.style = ttk.Style()
        self.current_theme = 'light'  # По умолчанию темная тема
        self.themes = {
            'dark': {
                'bg': '#121212',  # Темный фон
                'fg': '#E0E0E0',  # Светлый текст
                'primary': '#1E1E1E',  # Акцентные элементы
                'secondary': '#2D2D2D',
                'text': '#FFFFFF',
                'tree_bg': '#252525',
                'tree_fg': '#E0E0E0',
                'button_bg': '#333333',
                'button_fg': '#FFFFFF',
                'button_active': '#424242',
                'entry_bg': '#252525',
                'entry_fg': '#FFFFFF',
                'text_bg': '#252525',
                'text_fg': '#FFFFFF',
                'select_bg': '#3D3D3D',
                'select_fg': '#FFFFFF',
                'accent': '#BB86FC'
            },
            'light': {
                'bg': '#F5F5F5',
                'fg': '#212121',
                'primary': '#FFFFFF',
                'secondary': '#E0E0E0',
                'text': '#212121',
                'tree_bg': '#FFFFFF',
                'tree_fg': '#212121',
                'button_bg': '#E0E0E0',
                'button_fg': '#212121',
                'button_active': '#BDBDBD',
                'entry_bg': '#FFFFFF',
                'entry_fg': '#212121',
                'text_bg': '#FFFFFF',
                'text_fg': '#212121',
                'select_bg': '#2196F3',
                'select_fg': '#FFFFFF',
                'accent': '#6200EA'
            }
        }
        self._apply_theme()

    def toggle_theme(self):
        """Переключает тему между светлой и темной"""
        self.current_theme = 'light' if self.current_theme == 'dark' else 'dark'
        self._apply_theme()
        return self.current_theme

    def _apply_theme(self):
        """Применяет текущую тему ко всем элементам"""
        colors = self.themes[self.current_theme]

        # Базовые настройки
        self.style.theme_use('clam')  # Базовый стиль, который хорошо кастомизируется

        # Общие настройки
        self.style.configure('.',
                             background=colors['bg'],
                             foreground=colors['fg'],
                             font=('Segoe UI', 10),
                             insertbackground=colors['fg'])

        # Кнопки
        self.style.configure('TButton',
                             background=colors['button_bg'],
                             foreground=colors['button_fg'],
                             padding=6,
                             relief='flat')

        self.style.map('TButton',
                       background=[('active', colors['button_active']),
                                   ('pressed', colors['button_active'])])

        # Поля ввода
        self.style.configure('TEntry',
                             fieldbackground=colors['entry_bg'],
                             foreground=colors['entry_fg'],
                             insertwidth=2)

        # Treeview
        self.style.configure('Treeview',
                             background=colors['tree_bg'],
                             fieldbackground=colors['tree_bg'],
                             foreground=colors['tree_fg'])

        self.style.map('Treeview',
                       background=[('selected', colors['select_bg'])],
                       foreground=[('selected', colors['select_fg'])])

        # Скроллбары
        self.style.configure('Vertical.TScrollbar',
                             background=colors['secondary'],
                             troughcolor=colors['bg'],
                             bordercolor=colors['bg'],
                             arrowcolor=colors['fg'])

        self.style.configure('Horizontal.TScrollbar',
                             background=colors['secondary'],
                             troughcolor=colors['bg'],
                             bordercolor=colors['bg'],
                             arrowcolor=colors['fg'])

        # Вкладки
        self.style.configure('TNotebook',
                             background=colors['bg'])
        self.style.configure('TNotebook.Tab',
                             background=colors['secondary'],
                             foreground=colors['fg'],
                             padding=[10, 5])
        self.style.map('TNotebook.Tab',
                       background=[('selected', colors['primary'])],
                       foreground=[('selected', colors['fg'])])

        # Специальные стили
        self.style.configure('Header.TLabel',
                             font=('Segoe UI', 12, 'bold'),
                             foreground=colors['accent'])

        self.style.configure('Action.TButton',
                             background=colors['accent'],
                             foreground='white',
                             font=('Segoe UI', 10, 'bold'),
                             padding=8)

        self.style.configure('Danger.TButton',
                             background='#5C2B29',
                             foreground='white',
                             padding=8)


class DatabaseManager:
    """Класс для управления базой данных SQLite"""

    def __init__(self, db_path: str = 'user_management.db'):
        self.db_path = db_path
        self.conn = None
        self._setup_logger()
        self._connect()
        self.create_tables()
        self.migrate_database()
        self._create_admin_user()

    def _setup_logger(self):
        """Настройка системы логирования"""
        self.logger = logging.getLogger('DatabaseManager')
        self.logger.setLevel(logging.INFO)

    def _log_error(self, message: str):
        """Логирование ошибок"""
        self.logger.error(message)

    def _connect(self):
        """Устанавливает соединение с базой данных"""
        try:
            self.conn = sqlite3.connect(
                self.db_path,
                timeout=10,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            self.conn.execute("PRAGMA foreign_keys = ON")
            self.conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            self._log_error(f"Ошибка подключения к базе данных: {e}")
            raise

    def create_tables(self):
        """Создает все необходимые таблицы, если они не существуют."""
        try:
            cursor = self.conn.cursor()

            # Таблица system_users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                    created_at TIMESTAMP NOT NULL,
                    added_by INTEGER
                )
            ''')

            # Таблица user_data с полем для изображения
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    birth_date TEXT,
                    job TEXT,
                    rating REAL,
                    description TEXT,
                    added_by INTEGER,
                    created_at TIMESTAMP NOT NULL,
                    image BLOB,
                    FOREIGN KEY (added_by) REFERENCES system_users(id)
                )
            ''')

            self.conn.commit()
        except sqlite3.Error as e:
            self._log_error(f"Ошибка создания таблиц: {e}")
            raise

    def migrate_database(self):
        """Выполняет миграции базы данных при обновлении структуры."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]

            if version < 1:
                cursor.execute("PRAGMA table_info(user_data)")
                columns = [col[1] for col in cursor.fetchall()]
                if 'image' not in columns:
                    cursor.execute("ALTER TABLE user_data ADD COLUMN image BLOB")
                cursor.execute("PRAGMA user_version = 1")
                self.conn.commit()
        except sqlite3.Error as e:
            self._log_error(f"Ошибка миграции БД: {e}")
            raise

    def _create_admin_user(self):
        """Создание администратора по умолчанию"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM system_users WHERE username='admin'")
            if not cursor.fetchone():
                password = "admin123"
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute('''
                    INSERT INTO system_users 
                    (username, password_hash, role, created_at) 
                    VALUES (?, ?, ?, ?)
                ''', ('admin', password_hash, 'admin', datetime.now()))
                self.conn.commit()
        except sqlite3.Error as e:
            self._log_error(f"Ошибка создания администратора: {e}")

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Только проверка учетных данных в БД"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, role FROM system_users WHERE username = ? AND password_hash = ?',
                           (username, password_hash))
            result = cursor.fetchone()
            return dict(result) if result else None
        except sqlite3.Error as e:
            self._log_error(f"Ошибка аутентификации: {e}")
            return None

    def get_all_users(self) -> List[Dict]:
        """Возвращает список всех системных пользователей"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, username, role, created_at FROM system_users ORDER BY username')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self._log_error(f"Ошибка получения пользователей: {e}")
            return []

    def get_all_user_data(self) -> List[Dict]:
        """Возвращает все записи о пользователях с информацией о добавившем."""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT 
                    ud.id,
                    ud.full_name,
                    ud.email,
                    ud.phone,
                    ud.birth_date,
                    ud.job,
                    ud.rating,
                    ud.description,
                    ud.added_by,
                    ud.created_at,
                    ud.image,
                    su.username as added_by_username
                FROM user_data ud
                LEFT JOIN system_users su ON ud.added_by = su.id
                ORDER BY ud.created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self._log_error(f"Ошибка получения данных: {e}")
            return []

    def search_user_data(self, query: str) -> List[Dict]:
        """Ищет пользователей по ФИО, email или телефону."""
        try:
            search_pattern = f"%{query}%"
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT ud.*, su.username as added_by_username
                FROM user_data ud
                LEFT JOIN system_users su ON ud.added_by = su.id
                WHERE ud.full_name LIKE ? OR ud.email LIKE ? OR ud.phone LIKE ?
                ORDER BY ud.created_at DESC
            ''', (search_pattern, search_pattern, search_pattern))
            return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self._log_error(f"Ошибка поиска: {e}")
            return []

    def get_user_image(self, user_id: int) -> Optional[bytes]:
        """Возвращает изображение пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT image FROM user_data WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            return result['image'] if result else None
        except sqlite3.Error as e:
            self._log_error(f"Ошибка получения изображения: {e}")
            return None

    def add_user_data(self, data: Dict, image_data: bytes = None) -> Optional[int]:
        """Добавляет данные пользователя с изображением"""
        required_fields = ['full_name', 'email', 'phone', 'birth_date', 'job', 'added_by']
        if not all(field in data for field in required_fields):
            self._log_error("Отсутствуют обязательные поля")
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO user_data 
                (full_name, email, phone, birth_date, job, rating, description, added_by, created_at, image) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['full_name'],
                data['email'],
                data['phone'],
                data['birth_date'],
                data['job'],
                data.get('rating', 0.0),
                data.get('description', ''),
                data['added_by'],
                datetime.now(),
                image_data
            ))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            self._log_error(f"Ошибка добавления данных: {e}")
            return None

    def delete_user_data(self, user_id: int) -> bool:
        """Удаляет данные пользователя"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM user_data WHERE id = ?', (user_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            self._log_error(f"Ошибка удаления данных: {e}")
            return False

    def reset_admin_password(self):
        """Сброс пароля администратора на 'admin123'"""
        try:
            cursor = self.conn.cursor()
            new_password = "admin123"
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            cursor.execute('''
                UPDATE system_users 
                SET password_hash = ?
                WHERE username = 'admin'
            ''', (password_hash,))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            self._log_error(f"Ошибка сброса пароля: {e}")
            return False


class LoginWindow:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.window = tk.Toplevel(root)
        self._setup_window()
        self._create_widgets()

    def _setup_window(self):
        self.window.title("Авторизация")
        self.window.geometry("350x350")
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        self._center_window()

    def _center_window(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'+{x}+{y}')

    def _create_widgets(self):
        """Создает элементы интерфейса окна авторизации"""
        main_frame = ttk.Frame(self.window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Заголовок
        ttk.Label(
            main_frame,
            text="Авторизация",
            font=('Helvetica', 14, 'bold')
        ).pack(pady=(0, 20))

        # Поле логина
        ttk.Label(main_frame, text="Логин:").pack(anchor=tk.W)
        self.username_entry = ttk.Entry(main_frame)
        self.username_entry.pack(fill=tk.X, pady=5)
        self.username_entry.focus_set()

        # Поле пароля
        ttk.Label(main_frame, text="Пароль:").pack(anchor=tk.W)
        self.password_entry = ttk.Entry(main_frame, show="•")
        self.password_entry.pack(fill=tk.X, pady=5)

        # Чекбокс показа пароля
        self.show_password = tk.BooleanVar()
        ttk.Checkbutton(
            main_frame,
            text="Показать пароль",
            variable=self.show_password,
            command=lambda: self.password_entry.config(show="" if self.show_password.get() else "•")
        ).pack(anchor=tk.W, pady=5)

        # Кнопка входа
        ttk.Button(
            main_frame,
            text="Войти",
            command=self.authenticate
        ).pack(fill=tk.X, pady=10)

        # Привязка Enter к авторизации
        self.password_entry.bind('<Return>', self.authenticate)

    def _toggle_password(self):
        """Переключает видимость пароля"""
        show = self.show_password_var.get()
        self.password_entry.config(show="" if show else "•")

    def authenticate(self, event=None):
        """Проверка учетных данных"""
        # Получаем значения напрямую из виджетов Entry
        username = self.username_entry.get().strip()  # Было self.username_var.get()
        password = self.password_entry.get().strip()  # Было self.password_var.get()

        if not username:
            messagebox.showwarning("Ошибка", "Введите имя пользователя", parent=self.window)
            self.username_entry.focus_set()
            return

        if not password:
            messagebox.showwarning("Ошибка", "Введите пароль", parent=self.window)
            self.password_entry.focus_set()
            return

        try:
            self.on_login_success(username, password)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка авторизации: {str(e)}", parent=self.window)

    def on_close(self):
        if messagebox.askokcancel("Выход", "Вы действительно хотите выйти?", parent=self.window):
            self.root.destroy()


class MainApplication:
    """Главное приложение"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.db = DatabaseManager()
        self.current_user = None
        self.current_image = None
        self.image_data = None
        self.data_tree = None
        self.detail_frame = None
        self.search_entry = None
        self.bg_image = None

        # Инициализация темы
        self.theme_manager = ThemeManager()
        self._setup_main_window()
        self.load_background()
        self.show_login_window()

    def _setup_main_window(self):
        """Настройка главного окна"""
        self.root.title("Система управления пользователями")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self._center_window()

        # Применяем тему к корневому окну
        self._apply_theme_to_window(self.root)

    def _apply_theme_to_window(self, window):
        """Применяет текущую тему к окну и всем его виджетам"""
        colors = self.theme_manager.themes[self.theme_manager.current_theme]

        # Настройка стандартных tk виджетов
        window.config(bg=colors['bg'])

        # Рекурсивное применение к дочерним виджетам
        for widget in window.winfo_children():
            self._apply_theme_to_widget(widget)

    def _apply_theme_to_widget(self, widget):
        """Применяет тему к конкретному виджету и его дочерним элементам"""
        colors = self.theme_manager.themes[self.theme_manager.current_theme]

        try:
            if isinstance(widget, (tk.Entry, tk.Text, tk.Listbox, tk.Spinbox)):
                widget.config(
                    bg=colors['entry_bg'],
                    fg=colors['entry_fg'],
                    insertbackground=colors['fg'],
                    selectbackground=colors['select_bg'],
                    selectforeground=colors['select_fg']
                )
            elif isinstance(widget, (tk.Label, tk.Checkbutton, tk.Radiobutton)):
                widget.config(
                    bg=colors['bg'],
                    fg=colors['fg']
                )
            elif isinstance(widget, (tk.Frame, tk.LabelFrame, tk.PanedWindow)):
                widget.config(bg=colors['bg'])
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=colors['button_bg'],
                    fg=colors['button_fg'],
                    activebackground=colors['button_active'],
                    activeforeground=colors['button_fg']
                )

            # Рекурсивный вызов для дочерних виджетов
            for child in widget.winfo_children():
                self._apply_theme_to_widget(child)

        except Exception as e:
            logger.error(f"Ошибка применения темы к виджету {widget}: {e}")

    def _center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'+{x}+{y}')

    def load_background(self):
        """Загрузка фонового изображения"""
        try:
            if os.path.exists("background.jpg"):
                img = Image.open("background.jpg")
                img = img.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)

                bg_label = tk.Label(self.root, image=self.bg_image)
                bg_label.place(x=0, y=0, relwidth=1, relheight=1)
                bg_label.lower()  # Отправляем фон назад
        except Exception as e:
            print(f"Ошибка загрузки фона: {e}")

    def set_background(self):
        """Установка нового фона"""
        file_path = filedialog.askopenfilename(filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
        if file_path:
            try:
                shutil.copy(file_path, "background.jpg")
                self.load_background()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось установить фон: {e}")

    def show_login_window(self):
        """Показать окно входа"""
        self.root.withdraw()
        LoginWindow(self.root, self.handle_login)

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Аутентифицирует пользователя по логину и паролю."""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT id, username, role 
                FROM system_users 
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))

            result = cursor.fetchone()
            return dict(result) if result else None  # Явное возвращение None

        except sqlite3.Error as e:
            self._log_error(f"Ошибка аутентификации: {e}")
            return None

    def handle_login(self, username: str, password: str):
        """Обработка входа пользователя"""
        try:
            user = self.db.authenticate(username, password)
            if user is None:
                messagebox.showerror("Ошибка", "Неверные учетные данные")
                return

            self.current_user = {
                'id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
            self.show_main_interface()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка авторизации: {str(e)}")

    def show_main_interface(self):
        """Показать главный интерфейс"""
        self.root.deiconify()
        self.clear_window()

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Шапка
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            header_frame,
            text=f"Добро пожаловать, {self.current_user['username']} ({self.current_user['role']})",
            style='Header.TLabel'
        ).pack(side=tk.LEFT)

        # Кнопки управления
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        ttk.Button(
            btn_frame,
            text="Сменить тему",
            command=self.toggle_theme,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Выход",
            command=self.root.quit,
            style='Action.TButton'
        ).pack(side=tk.LEFT)

        # Панель управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))

        if self.current_user['role'] == 'admin':
            ttk.Button(
                control_frame,
                text="Управление пользователями",
                command=self.show_user_management,
                style='Action.TButton'
            ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Добавить данные",
            command=self.show_add_user_data,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Просмотр данных",
            command=self.show_user_data,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

    def toggle_theme(self):
        """Обработчик переключения темы"""
        try:
            # Переключаем тему
            self.theme_manager.toggle_theme()

            # Применяем новую тему ко всему приложению
            self._apply_theme_to_window(self.root)

            # Перестраиваем интерфейс
            self.show_main_interface()

        except Exception as e:
            logger.error(f"Ошибка переключения темы: {e}")
            messagebox.showerror("Ошибка", "Не удалось переключить тему")

    def clear_window(self):
        """Очистка окна"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_user_management(self):
        """Управление пользователями системы"""
        if self.current_user['role'] != 'admin':
            messagebox.showwarning("Ошибка", "Требуются права администратора")
            return

        self.clear_window()

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(
            container,
            text="Управление пользователями",
            style='Header.TLabel'
        ).pack(pady=(0, 20))

        # Таблица пользователей
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        columns = ("ID", "Логин", "Роль", "Дата создания")
        self.users_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse"
        )

        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=100 if col != "Логин" else 150)

        self.users_tree.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.users_tree.yview)

        # Заполнение данными
        for user in self.db.get_all_users():
            self.users_tree.insert('', tk.END, values=(
                user['id'],
                user['username'],
                user['role'],
                user['created_at'].split()[0] if isinstance(user['created_at'], str) else user['created_at'].date()
            ))

        # Кнопки управления
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            button_frame,
            text="Добавить пользователя",
            command=self.show_add_user_dialog,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Удалить выбранного",
            command=self.delete_system_user,
            style='Action.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="Назад",
            command=self.show_main_interface,
            style='Action.TButton'
        ).pack(side=tk.RIGHT)

    def show_add_user_dialog(self):
        """Диалог добавления пользователя"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить пользователя")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # Применяем тему к диалоговому окну
        self._apply_theme_to_window(dialog)

        # Поля формы
        ttk.Label(dialog, text="Логин:").pack(pady=(20, 5))
        username_entry = ttk.Entry(dialog)
        username_entry.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(dialog, text="Пароль:").pack(pady=5)
        password_entry = ttk.Entry(dialog, show="•")
        password_entry.pack(fill=tk.X, padx=20, pady=5)

        ttk.Label(dialog, text="Роль:").pack(pady=5)
        role_var = tk.StringVar(value="user")
        ttk.Radiobutton(dialog, text="Пользователь", variable=role_var, value="user").pack()
        ttk.Radiobutton(dialog, text="Администратор", variable=role_var, value="admin").pack()

        # Кнопки
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)

        ttk.Button(
            button_frame,
            text="Отмена",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Добавить",
            command=lambda: self.add_system_user(
                username_entry.get(),
                password_entry.get(),
                role_var.get(),
                dialog
            )
        ).pack(side=tk.RIGHT)

    def add_system_user(self, username, password, role, dialog):
        """Добавление пользователя системы"""
        if not username or not password:
            messagebox.showwarning("Ошибка", "Заполните все поля", parent=dialog)
            return

        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor = self.db.conn.cursor()
            cursor.execute('''
                INSERT INTO system_users 
                (username, password_hash, role, created_at, added_by) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, role, datetime.now(), self.current_user['id']))
            self.db.conn.commit()
            messagebox.showinfo("Успех", "Пользователь добавлен", parent=dialog)
            dialog.destroy()
            self.show_user_management()
        except sqlite3.IntegrityError:
            messagebox.showerror("Ошибка", "Пользователь уже существует", parent=dialog)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {str(e)}", parent=dialog)

    def delete_system_user(self):
        """Удаление пользователя системы"""
        if not (selected := self.users_tree.selection()):
            messagebox.showwarning("Ошибка", "Выберите пользователя")
            return

        user_id = self.users_tree.item(selected[0])['values'][0]

        if user_id == self.current_user['id']:
            messagebox.showwarning("Ошибка", "Нельзя удалить себя")
            return

        if messagebox.askyesno("Подтверждение", "Удалить пользователя?", parent=self.root):
            try:
                cursor = self.db.conn.cursor()
                cursor.execute('DELETE FROM system_users WHERE id = ?', (user_id,))
                self.db.conn.commit()
                if cursor.rowcount > 0:
                    self.users_tree.delete(selected[0])
                    messagebox.showinfo("Успех", "Пользователь удален")
                else:
                    messagebox.showerror("Ошибка", "Не удалось удалить пользователя")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка удаления: {str(e)}")

    def show_add_user_data(self):
        """Форма добавления данных пользователя"""
        self.clear_window()
        self.current_image = None
        self.image_data = None

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(
            container,
            text="Добавление данных",
            style='Header.TLabel'
        ).pack(pady=(0, 20))

        # Основной фрейм
        main_frame = ttk.Frame(container)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Форма
        form_frame = ttk.Frame(main_frame)
        form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        fields = [
            ("ФИО:", "full_name"),
            ("Email:", "email"),
            ("Телефон:", "phone"),
            ("Дата рождения:", "birth_date"),
            ("Работа:", "job"),
            ("Рейтинг:", "rating"),
            ("Описание:", "description")
        ]

        self.data_entries = {}
        for label, name in fields:
            frame = ttk.Frame(form_frame)
            frame.pack(fill=tk.X, pady=5)

            ttk.Label(frame, text=label, width=15).pack(side=tk.LEFT)

            if name == "description":
                entry = tk.Text(frame, height=5)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            else:
                entry = ttk.Entry(frame)
                entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            self.data_entries[name] = entry

        # Изображение
        image_frame = ttk.Frame(main_frame, width=300)
        image_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.image_label = ttk.Label(image_frame, text="Изображение не выбрано")
        self.image_label.pack(pady=10)

        ttk.Button(
            image_frame,
            text="Выбрать изображение",
            command=self.select_image,
            style='Action.TButton'
        ).pack(pady=5)

        # Кнопки
        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(
            button_frame,
            text="Назад",
            command=self.show_main_interface,
            style='Action.TButton'
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="Добавить",
            command=self.add_user_data,
            style='Action.TButton'
        ).pack(side=tk.RIGHT)

    def select_image(self):
        """Выбор изображения для пользователя"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Изображения", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            try:
                # Открываем и масштабируем изображение для предпросмотра
                img = Image.open(file_path)
                img.thumbnail((300, 300))

                # Конвертируем для отображения в интерфейсе
                self.current_image = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.current_image)

                # Сохраняем оригинальные бинарные данные для БД
                with open(file_path, 'rb') as f:
                    self.image_data = f.read()

                logger.info(f"Изображение выбрано. Размер: {len(self.image_data)} байт")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить изображение: {str(e)}")
                logger.error(f"Ошибка загрузки изображения: {e}")

    def add_user_data(self):
        """Добавление данных пользователя с изображением"""
        data = {}
        try:
            # Сбор данных из полей формы
            for name, entry in self.data_entries.items():
                if isinstance(entry, tk.Text):
                    data[name] = entry.get("1.0", tk.END).strip()
                else:
                    data[name] = entry.get().strip()

            # Валидация обязательных полей
            required = ['full_name', 'email', 'phone', 'birth_date', 'job']
            if not all(data.get(field) for field in required):
                messagebox.showwarning("Ошибка", "Заполните обязательные поля")
                return

            # Валидация рейтинга
            try:
                rating = float(data.get('rating', 0))
                if not 0 <= rating <= 10:
                    raise ValueError
                data['rating'] = rating
            except ValueError:
                messagebox.showwarning("Ошибка", "Рейтинг должен быть числом от 0 до 10")
                return

            # Добавление в БД
            data['added_by'] = self.current_user['id']

            # Передаем image_data в метод добавления
            if user_id := self.db.add_user_data(data, self.image_data):
                messagebox.showinfo("Успех", f"Данные добавлены (ID: {user_id})")
                self.show_main_interface()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить данные")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")
            logger.error(f"Ошибка добавления данных: {e}")

    def show_user_data(self):
        """Показывает список всех пользователей с возможностью просмотра деталей"""
        self.clear_window()

        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель поиска
        search_frame = ttk.Frame(container)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.search_entry.bind('<KeyRelease>', lambda e: self.refresh_user_data())

        # Таблица пользователей
        tree_frame = ttk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        scroll_y = ttk.Scrollbar(tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Колонки таблицы (добавлена колонка "Фото")
        columns = ("ID", "ФИО", "Email", "Телефон", "Дата рождения", "Работа", "Рейтинг", "Фото")
        self.data_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
            selectmode="browse"
        )

        # Настройка колонок
        self.data_tree.column("ID", width=50, anchor=tk.CENTER)
        self.data_tree.column("ФИО", width=150)
        self.data_tree.column("Email", width=150)
        self.data_tree.column("Телефон", width=120)
        self.data_tree.column("Дата рождения", width=100)
        self.data_tree.column("Работа", width=120)
        self.data_tree.column("Рейтинг", width=80, anchor=tk.CENTER)
        self.data_tree.column("Фото", width=100, anchor=tk.CENTER)  # Новая колонка

        # Заголовки колонок
        for col in columns:
            self.data_tree.heading(col, text=col)

        self.data_tree.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.data_tree.yview)
        scroll_x.config(command=self.data_tree.xview)

        # Привязка события выбора записи
        self.data_tree.bind('<<TreeviewSelect>>', lambda e: self.on_user_selected())

        # Область деталей
        self.detail_frame = ttk.Frame(container)
        self.detail_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Кнопки управления
        btn_frame = ttk.Frame(container)
        btn_frame.pack(fill=tk.X)

        ttk.Button(
            btn_frame,
            text="Удалить выбранного",
            command=self.delete_user_data,
            style='Danger.TButton'
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="Назад",
            command=self.show_main_interface,
            style='Action.TButton'
        ).pack(side=tk.RIGHT)

        # Первоначальная загрузка данных
        self.refresh_user_data()

    def on_user_selected(self):
        """Обработчик выбора пользователя в таблице"""
        if selected := self.data_tree.selection():
            user_id = self.data_tree.item(selected[0])['values'][0]
            self.show_user_details(user_id)

    def show_user_details(self, user_id: int):
        """Отображение детальной информации о пользователе с фотографией"""
        # Получаем данные пользователя
        user_data = next((u for u in self.db.get_all_user_data() if u['id'] == user_id), None)
        if not user_data:
            logger.warning(f"Данные пользователя {user_id} не найдены")
            return

        # Очищаем предыдущие виджеты
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        # Основной контейнер
        details_container = ttk.Frame(self.detail_frame)
        details_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая часть - текстовая информация
        info_frame = ttk.Frame(details_container)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        info_text = (
            f"ID: {user_data['id']}\n"
            f"ФИО: {user_data['full_name']}\n"
            f"Email: {user_data['email']}\n"
            f"Телефон: {user_data['phone']}\n"
            f"Дата рождения: {user_data['birth_date']}\n"
            f"Должность: {user_data['job']}\n"
            f"Рейтинг: {user_data['rating']}\n"
            f"Добавил: {user_data['added_by_username']}\n\n"
            f"Описание:\n{user_data['description']}"
        )

        text_widget = tk.Text(
            info_frame,
            wrap=tk.WORD,
            height=12,
            font=('Tahoma', 10),
            padx=10,
            pady=10
        )
        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Правая часть - фотография
        photo_frame = ttk.Frame(details_container, width=300)
        photo_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10)

        ttk.Label(
            photo_frame,
            text="Фотография профиля",
            font=('Tahoma', 10, 'bold')
        ).pack(pady=(0, 10))

        if user_data.get('image'):
            try:
                # Создаем изображение из бинарных данных
                image = Image.open(io.BytesIO(user_data['image']))
                image.thumbnail((300, 300))

                # Конвертируем для Tkinter
                self.user_photo = ImageTk.PhotoImage(image)  # Сохраняем как атрибут класса

                # Отображаем изображение
                img_label = ttk.Label(photo_frame, image=self.user_photo)
                img_label.pack()

                # Кнопка для просмотра в полном размере
                ttk.Button(
                    photo_frame,
                    text="Увеличить",
                    command=lambda: self._show_full_image(user_data['image']),
                    style='Action.TButton'
                ).pack(pady=10)

            except Exception as e:
                logger.error(f"Ошибка загрузки изображения: {e}")
                ttk.Label(
                    photo_frame,
                    text="Ошибка загрузки фото",
                    foreground='red'
                ).pack()
        else:
            ttk.Label(
                photo_frame,
                text="Фото отсутствует",
                foreground='gray'
            ).pack()

    def _show_full_image(self, image_data: bytes):
        """Отображение изображения в полном размере"""
        try:
            # Создаем новое окно
            img_window = tk.Toplevel(self.root)
            img_window.title("Просмотр изображения")

            # Загружаем изображение
            image = Image.open(io.BytesIO(image_data))

            # Конвертируем для Tkinter
            full_photo = ImageTk.PhotoImage(image)

            # Создаем Label для отображения
            img_label = ttk.Label(img_window, image=full_photo)
            img_label.image = full_photo  # Сохраняем ссылку!
            img_label.pack()

            # Центрируем окно
            img_window.update_idletasks()
            width = img_window.winfo_width()
            height = img_window.winfo_height()
            x = (self.root.winfo_screenwidth() // 2) - (width // 2)
            y = (self.root.winfo_screenheight() // 2) - (height // 2)
            img_window.geometry(f'+{x}+{y}')

        except Exception as e:
            logger.error(f"Ошибка отображения изображения: {e}")
            messagebox.showerror("Ошибка", "Не удалось отобразить изображение")

    def refresh_user_data(self):
        """Обновление данных в таблице с фото"""
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)

        search_query = self.search_entry.get().strip()
        data = self.db.search_user_data(search_query) if search_query else self.db.get_all_user_data()

        for row in data:
            # Определяем текст для колонки с фото
            photo_status = "Есть фото" if row['image'] else "Нет фото"

            self.data_tree.insert('', tk.END, values=(
                row['id'],
                row['full_name'],
                row['email'],
                row['phone'],
                row['birth_date'],
                row['job'],
                row['rating'],
                photo_status  # Добавляем статус фото
            ))

        # Очистка деталей
        for widget in self.detail_frame.winfo_children():
            widget.destroy()

        # Показать детали выбранного
        if selected := self.data_tree.selection():
            user_id = self.data_tree.item(selected[0])['values'][0]
            self.show_user_details(user_id)

    def delete_user_data(self):
        """Удаление данных пользователя"""
        if not (selected := self.data_tree.selection()):
            messagebox.showwarning("Ошибка", "Выберите запись для удаления")
            return

        record_id = self.data_tree.item(selected[0])['values'][0]

        if messagebox.askyesno(
                "Подтверждение",
                "Вы действительно хотите удалить эти данные?",
                parent=self.root
        ):
            if self.db.delete_user_data(record_id):
                self.data_tree.delete(selected[0])
                for widget in self.detail_frame.winfo_children():
                    widget.destroy()
                messagebox.showinfo("Успех", "Данные удалены")
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить данные")


if __name__ == "__main__":
    # Инициализация приложения
    root = tk.Tk()

    # Создаем новую БД с таблицами
    db = DatabaseManager()

    # Сбрасываем пароль администратора
    db.reset_admin_password()
    logger.info("Пароль администратора сброшен на 'admin123'")

    app = MainApplication(root)
    root.mainloop()
