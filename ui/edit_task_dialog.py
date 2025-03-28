from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QSpinBox, QTextEdit, QDialogButtonBox, QTimeEdit,
                               QCheckBox, QGroupBox, QMessageBox, QWidget, QHBoxLayout)
from PyQt6.QtCore import Qt, QTime
from datetime import time
from models import SingleTask, DailyTask, TaskType
from database import Database
from .widgets import TimeInputWidget, DateTimeInputWidget

class EditTaskDialog(QDialog):
    """Диалог редактирования задачи."""
    
    def __init__(self, task, db: Database, parent=None):
        super().__init__(parent)
        self.task = task
        self.db = db
        self.setWindowTitle("Редактирование задачи")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Название задачи
        self.title_edit = QLineEdit(task.title)
        form_layout.addRow("Название:", self.title_edit)
        
        # Длительность
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 1440)
        self.duration_spin.setValue(task.duration_minutes)
        self.duration_spin.setSuffix(" мин")
        form_layout.addRow("Длительность:", self.duration_spin)
        
        # Описание
        self.description_edit = QTextEdit()
        if task.description:
            self.description_edit.setText(task.description)
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_edit)
        
        # Специфичные поля для ежедневных задач
        if isinstance(task, DailyTask):
            # Дни недели
            self.weekdays_group = QGroupBox("Дни недели")
            weekdays_layout = QVBoxLayout()
            self.weekday_checks = []
            weekday_names = ["Понедельник", "Вторник", "Среда", "Четверг",
                           "Пятница", "Суббота", "Воскресенье"]
            
            for i, name in enumerate(weekday_names):
                checkbox = QCheckBox(name)
                checkbox.setChecked(i in task.weekdays)
                self.weekday_checks.append(checkbox)
                weekdays_layout.addWidget(checkbox)
            
            self.weekdays_group.setLayout(weekdays_layout)
            form_layout.addRow(self.weekdays_group)
            
            # Контейнер для времени с чекбоксом
            time_container = QWidget()
            time_container.setStyleSheet("background: transparent; border: none;")
            time_layout = QHBoxLayout(time_container)
            time_layout.setContentsMargins(0, 0, 0, 0)
            time_layout.setSpacing(10)
            
            # Чекбокс для включения/выключения времени
            self.time_enabled_check = QCheckBox()
            self.time_enabled_check.setChecked(task.scheduled_time is not None)
            
            # Виджет времени
            self.time_edit = TimeInputWidget()
            if task.scheduled_time:
                self.time_edit.set_time(task.scheduled_time)
            else:
                self.time_edit.setEnabled(False)
            
            time_layout.addWidget(self.time_enabled_check)
            time_layout.addWidget(self.time_edit)
            time_layout.addStretch()
            
            # Подключаем обработчик изменения состояния чекбокса
            self.time_enabled_check.stateChanged.connect(
                lambda state: self.time_edit.setEnabled(bool(state))
            )
            
            form_layout.addRow("Время:", time_container)
            
            # Флаг неограниченной длительности
            self.unlimited_check = QCheckBox("Неограниченная длительность")
            self.unlimited_check.setChecked(task.is_unlimited)
            self.unlimited_check.stateChanged.connect(
                lambda state: self.duration_spin.setEnabled(not bool(state))
            )
            form_layout.addRow(self.unlimited_check)
        else:
            # Для единоразовой задачи используем DateTimeInputWidget
            self.datetime_widget = DateTimeInputWidget()
            if task.execution_date:
                self.datetime_widget.set_datetime(task.execution_date)
            form_layout.addRow("Дата и время:", self.datetime_widget)
        
        layout.addLayout(form_layout)
        
        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_edited_task(self):
        """Получение отредактированной задачи."""
        if isinstance(self.task, SingleTask):
            execution_date = self.datetime_widget.get_datetime()
            return SingleTask(
                title=self.title_edit.text().strip(),
                duration_minutes=self.duration_spin.value(),
                description=self.description_edit.toPlainText().strip() or None,
                scheduled_time=time(execution_date.hour, execution_date.minute),
                execution_date=execution_date,
                id=self.task.id,
                is_completed=self.task.is_completed,
                created_at=self.task.created_at
            )
        else:
            # Получаем время только если включен чекбокс
            scheduled_time = None
            if self.time_enabled_check.isChecked():
                scheduled_time = self.time_edit.get_time()
            
            return DailyTask(
                title=self.title_edit.text().strip(),
                duration_minutes=self.duration_spin.value(),
                description=self.description_edit.toPlainText().strip() or None,
                scheduled_time=scheduled_time,
                weekdays=[i for i, cb in enumerate(self.weekday_checks) if cb.isChecked()],
                id=self.task.id,
                is_completed=self.task.is_completed,
                is_unlimited=self.unlimited_check.isChecked(),
                created_at=self.task.created_at
            )
    
    def accept(self):
        """Проверка и сохранение изменений."""
        if not self.title_edit.text().strip():
            QMessageBox.critical(self, "Ошибка", "Введите название задачи")
            return
        
        if isinstance(self.task, DailyTask):
            weekdays = [i for i, cb in enumerate(self.weekday_checks) if cb.isChecked()]
            if not weekdays:
                QMessageBox.critical(self, "Ошибка", "Выберите хотя бы один день недели")
                return
        else:
            execution_date = self.datetime_widget.get_datetime()
            if not execution_date:
                QMessageBox.critical(self, "Ошибка", "Выберите корректную дату и время выполнения")
                return
        
        super().accept() 