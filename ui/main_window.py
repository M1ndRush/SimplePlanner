from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMenuBar, QMenu
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QScreen, QAction
from PyQt6.QtWidgets import QApplication
from .calendar_tab import CalendarTab
from .tasks_tab import TasksTab
from database import Database

class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    Содержит две вкладки: календарь с распорядком и управление задачами.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Planner")
        self.setMinimumSize(1000, 600)
        
        # Установка размера окна (80% от размера экрана) и центрирование
        self.setup_window_size()
        
        # Инициализация базы данных
        self.db = Database()
        
        # Создание и настройка вкладок
        self.tabs = QTabWidget()
        self.calendar_tab = CalendarTab(self.db)
        self.tasks_tab = TasksTab(self.db)
        
        self.tabs.addTab(self.calendar_tab, "Календарь и распорядок")
        self.tabs.addTab(self.tasks_tab, "Управление задачами")
        
        # Установка вкладок как центрального виджета
        self.setCentralWidget(self.tabs)
        
        # Создание меню
        self.create_menu()
        
        # Соединение сигналов между вкладками
        self.tasks_tab.task_added.connect(self.calendar_tab.update_available_tasks)
        self.calendar_tab.task_scheduled.connect(self.tasks_tab.update_task_list)
    
    def setup_window_size(self):
        """
        Устанавливает размер окна на 80% от размера экрана и центрирует его.
        """
        # Получение доступного размера экрана
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        
        # Вычисление 80% от размера экрана
        window_width = int(screen_geometry.width() * 0.8)
        window_height = int(screen_geometry.height() * 0.8)
        
        # Установка размера окна
        self.resize(window_width, window_height)
        
        # Центрирование окна
        center_point = screen_geometry.center()
        window_rect = QRect(0, 0, window_width, window_height)
        window_rect.moveCenter(center_point)
        self.setGeometry(window_rect)
    
    def create_menu(self):
        """
        Создает меню приложения с опциями просмотра.
        """
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)
        
        # Создание меню "Вид"
        view_menu = QMenu("Вид", self)
        menubar.addMenu(view_menu)
        
        # Добавление действия для переключения полноэкранного режима
        self.toggle_fullscreen_action = QAction("Полноэкранный режим", self)
        self.toggle_fullscreen_action.setShortcut("F11")
        self.toggle_fullscreen_action.setCheckable(True)
        self.toggle_fullscreen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.toggle_fullscreen_action)
        
        # Добавление действия для сброса размера окна до 80%
        reset_size_action = QAction("Сбросить размер (80% экрана)", self)
        reset_size_action.triggered.connect(self.setup_window_size)
        view_menu.addAction(reset_size_action)
    
    def toggle_fullscreen(self, checked):
        """
        Переключает полноэкранный режим окна.
        """
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
            # Восстановление размера и позиции окна
            self.setup_window_size() 