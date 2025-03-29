from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QSpinBox, QComboBox, QPushButton,
                               QCheckBox, QGroupBox, QScrollArea, QLabel,
                               QMessageBox, QTextEdit, QTimeEdit, QDialog,
                               QDialogButtonBox, QFrame, QSplitter, QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QTime, QSize
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, time, timedelta
from typing import Union, Optional
from models import SingleTask, DailyTask, TaskType, ScheduledTask
from database import Database
from .edit_task_dialog import EditTaskDialog
from .widgets import TimeInputWidget, DateTimeInputWidget

class TaskForm(QWidget):
    """Базовый класс для форм создания задач."""
    
    task_created = pyqtSignal()
    
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        
        # Создаем основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Создаем form layout с правильными отступами
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QLineEdit, QTextEdit, QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: #f8f9fa;
                color: #212529;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border-color: #80bdff;
                background-color: white;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                background-color: #e9ecef;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #dee2e6;
            }
            QPushButton {
                padding: 8px 16px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        
        self.layout = QFormLayout(form_widget)
        self.layout.setContentsMargins(25, 20, 25, 20)
        self.layout.setSpacing(15)
        self.layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Создаем контейнеры для полей ввода
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent; border: none;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Введите название задачи")
        title_layout.addWidget(self.title_edit)
        
        duration_container = QWidget()
        duration_container.setStyleSheet("background: transparent; border: none;")
        duration_layout = QHBoxLayout(duration_container)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 1440)
        self.duration_spin.setValue(30)
        self.duration_spin.setSuffix(" мин")
        self.duration_spin.setMinimumWidth(120)
        duration_layout.addWidget(self.duration_spin)
        duration_layout.addStretch()
        
        description_container = QWidget()
        description_container.setStyleSheet("background: transparent; border: none;")
        description_layout = QHBoxLayout(description_container)
        description_layout.setContentsMargins(0, 0, 0, 0)
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Добавьте описание задачи (необязательно)")
        self.description_edit.setMaximumHeight(100)
        description_layout.addWidget(self.description_edit)
        
        # Добавляем поля в form layout
        self.layout.addRow("Название", title_container)
        self.layout.addRow("Длительность", duration_container)
        self.layout.addRow("Описание", description_container)
        
        # Добавляем form layout в основной layout
        main_layout.addWidget(form_widget)
    
    def show_error(self, message: str):
        """Отображение диалогового окна с ошибкой."""
        QMessageBox.critical(self, "Ошибка", message)
    
    def get_description(self) -> Optional[str]:
        """Получение описания задачи."""
        text = self.description_edit.toPlainText().strip()
        if len(text) > 300:
            text = text[:300]
        return text if text else None

class SingleTaskForm(TaskForm):
    """Форма для создания единоразовой задачи."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(db, parent)
        
        # Добавление специфичных полей
        self.datetime_widget = DateTimeInputWidget()
        self.layout.addRow("Дата и время:", self.datetime_widget)
        
        # Кнопка создания
        self.create_button = QPushButton("Создать задачу")
        self.create_button.clicked.connect(self._create_task)
        self.layout.addRow(self.create_button)
    
    def _create_task(self):
        """Создание единоразовой задачи."""
        try:
            if not self.title_edit.text().strip():
                raise ValueError("Введите название задачи")
            
            execution_date = self.datetime_widget.get_datetime()
            if not execution_date:
                raise ValueError("Выберите корректную дату и время выполнения")
            
            task = SingleTask(
                title=self.title_edit.text().strip(),
                duration_minutes=self.duration_spin.value(),
                description=self.get_description(),
                scheduled_time=time(execution_date.hour, execution_date.minute),
                execution_date=execution_date
            )
            self.db.add_single_task(task)
            self.task_created.emit()
            
            # Очистка формы
            self.title_edit.clear()
            self.duration_spin.setValue(30)
            self.description_edit.clear()
            self.datetime_widget.set_datetime(None)
            
        except ValueError as e:
            self.show_error(str(e))

class DailyTaskForm(TaskForm):
    """Форма для создания ежедневной задачи."""
    
    def __init__(self, db: Database, parent=None):
        super().__init__(db, parent)
        
        # Чекбоксы для дней недели
        self.weekdays_group = QGroupBox("Дни недели")
        weekdays_layout = QVBoxLayout()
        
        self.weekday_checks = []
        weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг",
                        "Пятница", "Суббота", "Воскресенье"]
        
        for i, name in enumerate(weekday_names):
            checkbox = QCheckBox(name)
            self.weekday_checks.append(checkbox)
            weekdays_layout.addWidget(checkbox)
        
        self.weekdays_group.setLayout(weekdays_layout)
        self.layout.addRow(self.weekdays_group)
        
        # Контейнер для времени с чекбоксом
        time_container = QWidget()
        time_container.setStyleSheet("background: transparent; border: none;")
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(10)
        
        # Чекбокс для включения/выключения времени
        self.time_enabled_check = QCheckBox()
        self.time_enabled_check.setChecked(True)
        
        # Виджет времени
        self.time_widget = TimeInputWidget()
        
        time_layout.addWidget(self.time_enabled_check)
        time_layout.addWidget(self.time_widget)
        time_layout.addStretch()
        
        # Подключаем обработчик изменения состояния чекбокса
        self.time_enabled_check.stateChanged.connect(
            lambda state: self.time_widget.setEnabled(bool(state))
        )
        
        self.layout.addRow("Время:", time_container)
        
        # Флаг неограниченной длительности
        self.unlimited_check = QCheckBox("Неограниченная длительность")
        self.unlimited_check.stateChanged.connect(
            lambda state: self.duration_spin.setEnabled(not bool(state))
        )
        self.layout.addRow(self.unlimited_check)
        
        # Кнопка создания
        self.create_button = QPushButton("Создать задачу")
        self.create_button.clicked.connect(self._create_task)
        self.layout.addRow(self.create_button)
    
    def _schedule_daily_task(self, task: DailyTask, task_id: int):
        """Автоматическое планирование ежедневной задачи на 30 дней вперед."""
        if not task.scheduled_time:
            return
            
        # Планируем на 30 дней вперед
        current_date = datetime.now().date()
        end_date = current_date + timedelta(days=30)
        
        while current_date <= end_date:
            # Проверяем, является ли текущий день недели выбранным
            if current_date.weekday() in task.weekdays:
                scheduled_task = ScheduledTask(
                    task_id=task_id,
                    date=datetime.combine(current_date, time()),
                    start_time=task.scheduled_time,
                    title=task.title,
                    duration_minutes=task.duration_minutes if not task.is_unlimited else 1440,  # 24 часа для неограниченных
                    description=task.description,
                    is_completed=False
                )
                self.db.add_scheduled_task(scheduled_task)
            current_date += timedelta(days=1)

    def _create_task(self):
        """Создание ежедневной задачи."""
        try:
            if not self.title_edit.text().strip():
                raise ValueError("Введите название задачи")
            
            # Получение выбранных дней недели
            weekdays = [i for i, cb in enumerate(self.weekday_checks) if cb.isChecked()]
            
            if not weekdays:
                raise ValueError("Выберите хотя бы один день недели")
            
            # Получаем время только если включен чекбокс
            scheduled_time = None
            if self.time_enabled_check.isChecked():
                scheduled_time = self.time_widget.get_time()
            
            task = DailyTask(
                title=self.title_edit.text().strip(),
                duration_minutes=self.duration_spin.value(),
                description=self.get_description(),
                scheduled_time=scheduled_time,
                weekdays=weekdays,
                is_unlimited=self.unlimited_check.isChecked()
            )
            task_id = self.db.add_daily_task(task)
            
            # Автоматически планируем задачу только если указано время
            if scheduled_time:
                self._schedule_daily_task(task, task_id)
            
            self.task_created.emit()
            
            # Очистка формы
            self.title_edit.clear()
            self.duration_spin.setValue(30)
            self.description_edit.clear()
            self.time_widget.set_time(None)
            for cb in self.weekday_checks:
                cb.setChecked(False)
            self.unlimited_check.setChecked(False)
            self.time_enabled_check.setChecked(True)
            
        except ValueError as e:
            self.show_error(str(e))

class TasksTab(QWidget):
    """Вкладка управления задачами."""
    
    task_added = pyqtSignal()
    
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        
        # Устанавливаем общий стиль для вкладки
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            QGroupBox {
                background-color: white;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                padding-top: 20px;
            }
            QGroupBox::title {
                color: #212529;
                padding: 0 15px;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                color: #212529;
                font-size: 14px;
                min-width: 200px;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
            }
        """)
        
        # Создание layout
        layout = QHBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Создаем разделитель
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)  # Запрещаем полное схлопывание
        
        # Левая панель с формой создания задач
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setSpacing(20)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Выбор типа задачи
        task_type_group = QGroupBox("Создание задачи")
        task_type_layout = QVBoxLayout()
        task_type_layout.setContentsMargins(20, 25, 20, 20)
        task_type_layout.setSpacing(15)
        
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems(["Единоразовая задача", "Ежедневная задача"])
        self.task_type_combo.currentIndexChanged.connect(self._on_task_type_changed)
        
        task_type_layout.addWidget(self.task_type_combo)
        
        # Контейнер для форм
        self.form_container = QWidget()
        self.form_layout = QVBoxLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 10, 0, 0)
        task_type_layout.addWidget(self.form_container)
        
        task_type_group.setLayout(task_type_layout)
        left_panel_layout.addWidget(task_type_group)
        left_panel_layout.addStretch()
        
        # Правая панель со списком существующих задач
        task_list_group = QGroupBox("Существующие задачи")
        task_list_layout = QVBoxLayout()
        task_list_layout.setContentsMargins(20, 25, 20, 20)
        task_list_layout.setSpacing(0)
        
        # Заголовки колонок
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-radius: 6px;
            }
            QLabel {
                color: #6c757d;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)
        
        # Создаем заголовки
        headers = [("№", 1), ("Название", 3), ("Создана", 2),
                  ("Время", 2), ("Длительность", 2), ("", 2)]
        
        for title, stretch in headers:
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            header_layout.addWidget(label, stretch)
        
        task_list_layout.addWidget(header)
        
        # Контейнер для списка задач
        self.task_list = QScrollArea()
        self.task_list.setWidgetResizable(True)
        self.task_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.task_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.task_list_container = QWidget()
        self.task_list_container.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)
        self.task_list_layout = QVBoxLayout(self.task_list_container)
        self.task_list_layout.setContentsMargins(0, 10, 0, 10)
        self.task_list_layout.setSpacing(2)
        self.task_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.task_list.setWidget(self.task_list_container)
        
        task_list_layout.addWidget(self.task_list)
        task_list_group.setLayout(task_list_layout)
        
        # Добавляем виджеты в разделитель
        splitter.addWidget(left_panel)
        splitter.addWidget(task_list_group)
        
        # Устанавливаем начальные размеры
        splitter.setSizes([400, self.width() - 400])
        
        # Добавляем разделитель в главный layout
        layout.addWidget(splitter)
        
        # Создание форм
        self.single_form = SingleTaskForm(db)
        self.daily_form = DailyTaskForm(db)
        
        # Подключение сигналов
        self.single_form.task_created.connect(self._on_task_created)
        self.daily_form.task_created.connect(self._on_task_created)
        
        # Показ формы по умолчанию
        self._show_form(self.single_form)
        
        # Загрузка существующих задач
        self.update_task_list()
    
    def _show_form(self, form: QWidget):
        """Показ формы создания задачи."""
        # Очистка контейнера
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                self.form_layout.removeWidget(item.widget())
        
        # Добавление новой формы
        self.form_layout.addWidget(form)
        form.show()
    
    def _on_task_type_changed(self, index: int):
        """Обработка изменения типа задачи."""
        if index == 0:
            self._show_form(self.single_form)
        else:
            self._show_form(self.daily_form)
    
    def _on_task_created(self):
        """Обработка создания новой задачи."""
        self.update_task_list()
        self.task_added.emit()
    
    def update_task_list(self, scheduled_task: ScheduledTask = None):
        """Обновление списка существующих задач."""
        # Очистка списка
        for i in reversed(range(self.task_list_layout.count())):
            item = self.task_list_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Загрузка задач из БД
        tasks = self.db.get_all_tasks()
        
        # Добавление задач в список
        for i, task in enumerate(tasks, 1):
            task_widget = QWidget()
            task_widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-radius: 6px;
                }
                QWidget:hover {
                    background-color: #f8f9fa;
                }
                QLabel {
                    color: #212529;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 4px;
                    font-size: 16px;
                    color: #6c757d;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                    color: #007bff;
                }
            """)
            
            task_layout = QHBoxLayout(task_widget)
            task_layout.setContentsMargins(15, 10, 15, 10)
            task_layout.setSpacing(15)
            
            # Создаем ячейки с данными
            cells = [
                (f"{i}", 1),
                (task.title, 3),
                (task.created_at.strftime("%d.%m.%Y %H:%M"), 2),
                (task.scheduled_time.strftime("%H:%M") if task.scheduled_time else "-", 2),
                (f"{task.duration_minutes} мин" if not (isinstance(task, DailyTask) and task.is_unlimited) else "∞", 2)
            ]
            
            for text, stretch in cells:
                label = QLabel(text)
                label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                task_layout.addWidget(label, stretch)
            
            # Кнопки управления
            buttons_container = QWidget()
            buttons_container.setStyleSheet("background: transparent;")
            buttons_layout = QHBoxLayout(buttons_container)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(5)
            
            edit_button = QPushButton("✎")
            edit_button.setFixedSize(32, 32)
            edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_button.clicked.connect(lambda checked, t=task: self._edit_task(t))
            
            delete_button = QPushButton("✖")
            delete_button.setFixedSize(32, 32)
            delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
            delete_button.clicked.connect(lambda checked, t=task: self._delete_task(t))
            
            buttons_layout.addWidget(edit_button)
            buttons_layout.addWidget(delete_button)
            buttons_layout.addStretch()
            
            task_layout.addWidget(buttons_container, 2)
            
            # Добавляем задачу в список
            self.task_list_layout.addWidget(task_widget)
        
        # Вместо растягивающегося пространства добавляем пустой виджет с фиксированной высотой
        if not tasks:
            empty_label = QLabel("Нет задач")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_label.setStyleSheet("color: #6c757d; font-size: 16px; padding: 20px;")
            self.task_list_layout.addWidget(empty_label)
    
    def _edit_task(self, task):
        """Редактирование задачи."""
        dialog = EditTaskDialog(task, self.db, self)
        if dialog.exec():
            edited_task = dialog.get_edited_task()
            self.db.update_task(edited_task)
            self.update_task_list()
            self.task_added.emit()
    
    def _delete_task(self, task):
        """Удаление задачи."""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить задачу '{task.title}'?\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.remove_task(task.id)
            self.update_task_list()
            self.task_added.emit() 