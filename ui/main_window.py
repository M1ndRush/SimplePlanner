from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtCore import Qt
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
        
        # Соединение сигналов между вкладками
        self.tasks_tab.task_added.connect(self.calendar_tab.update_available_tasks)
        self.calendar_tab.task_scheduled.connect(self.tasks_tab.update_task_list) 