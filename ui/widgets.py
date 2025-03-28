from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSpinBox,
                               QLabel)
from PyQt6.QtCore import Qt
from datetime import datetime, time, timedelta

class TimeInputWidget(QWidget):
    """Виджет для ввода времени с отдельными полями для часов и минут."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Спинбокс для часов
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(6, 23)  # Ограничиваем диапазон с 6:00 до 23:45
        self.hour_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.hour_spin.setMinimumWidth(60)
        self.hour_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px 5px 5px 5px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                border-radius: 4px;
                background-color: #e9ecef;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #dee2e6;
            }
        """)
        
        hour_label = QLabel("ч")
        hour_label.setStyleSheet("color: #6c757d; padding-right: 15px;")
        
        # Спинбокс для минут
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 45)
        self.minute_spin.setSingleStep(15)
        self.minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.minute_spin.setMinimumWidth(60)
        self.minute_spin.setStyleSheet(self.hour_spin.styleSheet())
        
        minute_label = QLabel("м")
        minute_label.setStyleSheet("color: #6c757d;")
        
        layout.addWidget(self.hour_spin)
        layout.addWidget(hour_label)
        layout.addWidget(self.minute_spin)
        layout.addWidget(minute_label)
        layout.addStretch()
        
        # Ограничиваем время до 23:45
        self.hour_spin.valueChanged.connect(self._check_time_limit)
        
    def _check_time_limit(self):
        """Проверка и корректировка времени в пределах допустимого диапазона."""
        if self.hour_spin.value() == 23:
            self.minute_spin.setRange(0, 45)  # В 23 часа минуты только до 45
        else:
            self.minute_spin.setRange(0, 45)
    
    def get_time(self) -> time:
        """Получение выбранного времени."""
        return time(self.hour_spin.value(), self.minute_spin.value())
    
    def set_time(self, t: time):
        """Установка времени."""
        if t:
            # Проверяем, что время в допустимом диапазоне
            hour = max(6, min(23, t.hour))
            # Округляем минуты до ближайших 15
            minutes = ((t.minute + 7) // 15) * 15
            if hour == 23:
                minutes = min(45, minutes)
            
            self.hour_spin.setValue(hour)
            self.minute_spin.setValue(minutes)
        else:
            self.hour_spin.setValue(6)
            self.minute_spin.setValue(0)
    
    def setEnabled(self, enabled: bool):
        """Переопределяем метод включения/выключения виджета."""
        super().setEnabled(enabled)
        self.hour_spin.setEnabled(enabled)
        self.minute_spin.setEnabled(enabled)

class DateTimeInputWidget(QWidget):
    """Виджет для ввода даты и времени с отдельными полями."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Первая строка: день и месяц
        date_row1 = QWidget()
        date_row1_layout = QHBoxLayout(date_row1)
        date_row1_layout.setContentsMargins(0, 0, 0, 0)
        date_row1_layout.setSpacing(5)
        
        # Спинбоксы для дня и месяца
        self.day_spin = QSpinBox()
        self.day_spin.setRange(1, 31)
        self.day_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.day_spin.setMinimumWidth(60)
        self.day_spin.setStyleSheet("""
            QSpinBox {
                padding: 5px 5px 5px 5px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                border: none;
                border-radius: 4px;
                background-color: #e9ecef;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #dee2e6;
            }
        """)
        
        day_label = QLabel("д")
        day_label.setStyleSheet("color: #6c757d; padding-right: 15px;")
        
        self.month_spin = QSpinBox()
        self.month_spin.setRange(1, 12)
        self.month_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.month_spin.setMinimumWidth(60)
        self.month_spin.setStyleSheet(self.day_spin.styleSheet())
        
        month_label = QLabel("м")
        month_label.setStyleSheet("color: #6c757d;")
        
        date_row1_layout.addWidget(self.day_spin)
        date_row1_layout.addWidget(day_label)
        date_row1_layout.addWidget(self.month_spin)
        date_row1_layout.addWidget(month_label)
        date_row1_layout.addStretch()
        
        # Вторая строка: год
        date_row2 = QWidget()
        date_row2_layout = QHBoxLayout(date_row2)
        date_row2_layout.setContentsMargins(0, 0, 0, 0)
        date_row2_layout.setSpacing(5)
        
        self.year_spin = QSpinBox()
        current_year = datetime.now().year
        self.year_spin.setRange(current_year, current_year + 10)
        self.year_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.year_spin.setMinimumWidth(80)
        self.year_spin.setStyleSheet(self.day_spin.styleSheet())
        
        year_label = QLabel("г")
        year_label.setStyleSheet("color: #6c757d;")
        
        date_row2_layout.addWidget(self.year_spin)
        date_row2_layout.addWidget(year_label)
        date_row2_layout.addStretch()
        
        # Третья строка: часы и минуты
        time_row = QWidget()
        time_layout = QHBoxLayout(time_row)
        time_layout.setContentsMargins(0, 0, 0, 0)
        time_layout.setSpacing(5)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(6, 23)  # Ограничиваем диапазон с 6:00 до 23:45
        self.hour_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.hour_spin.setMinimumWidth(60)
        self.hour_spin.setStyleSheet(self.day_spin.styleSheet())
        
        hour_label = QLabel("ч")
        hour_label.setStyleSheet("color: #6c757d; padding-right: 15px;")
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 45)
        self.minute_spin.setSingleStep(15)
        self.minute_spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        self.minute_spin.setMinimumWidth(60)
        self.minute_spin.setStyleSheet(self.day_spin.styleSheet())
        
        minute_label = QLabel("м")
        minute_label.setStyleSheet("color: #6c757d;")
        
        time_layout.addWidget(self.hour_spin)
        time_layout.addWidget(hour_label)
        time_layout.addWidget(self.minute_spin)
        time_layout.addWidget(minute_label)
        time_layout.addStretch()
        
        # Добавляем все строки в основной layout
        layout.addWidget(date_row1)
        layout.addWidget(date_row2)
        layout.addWidget(time_row)
        
        # Подключаем обработчики изменения месяца и года
        self.month_spin.valueChanged.connect(self._update_days_in_month)
        self.year_spin.valueChanged.connect(self._update_days_in_month)
        self.hour_spin.valueChanged.connect(self._check_time_limit)
        
        # Устанавливаем текущую дату
        current_date = datetime.now()
        self.set_datetime(current_date)
    
    def _update_days_in_month(self):
        """Обновление количества дней в зависимости от выбранного месяца."""
        year = self.year_spin.value()
        month = self.month_spin.value()
        
        # Получаем последний день месяца
        if month == 2:
            # Проверка на високосный год
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                max_day = 29
            else:
                max_day = 28
        elif month in [4, 6, 9, 11]:
            max_day = 30
        else:
            max_day = 31
        
        # Сохраняем текущий день
        current_day = min(self.day_spin.value(), max_day)
        
        # Обновляем диапазон и значение
        self.day_spin.setRange(1, max_day)
        self.day_spin.setValue(current_day)
    
    def _check_time_limit(self):
        """Проверка и корректировка времени в пределах допустимого диапазона."""
        if self.hour_spin.value() == 23:
            self.minute_spin.setRange(0, 45)  # В 23 часа минуты только до 45
        else:
            self.minute_spin.setRange(0, 45)
    
    def get_datetime(self) -> datetime:
        """Получение выбранных даты и времени."""
        try:
            hour = max(6, min(23, self.hour_spin.value()))
            minutes = self.minute_spin.value()
            if hour == 23:
                minutes = min(45, minutes)
                
            return datetime(
                year=self.year_spin.value(),
                month=self.month_spin.value(),
                day=self.day_spin.value(),
                hour=hour,
                minute=minutes
            )
        except ValueError:
            return None
    
    def set_datetime(self, dt: datetime):
        """Установка даты и времени."""
        if dt:
            self.year_spin.setValue(dt.year)
            self.month_spin.setValue(dt.month)
            self.day_spin.setValue(dt.day)
            
            # Проверяем, что время в допустимом диапазоне
            hour = max(6, min(23, dt.hour))
            # Округляем минуты до ближайших 15
            minutes = ((dt.minute + 7) // 15) * 15
            if hour == 23:
                minutes = min(45, minutes)
            
            self.hour_spin.setValue(hour)
            self.minute_spin.setValue(minutes)
        else:
            current = datetime.now()
            # Если текущее время меньше 6:00, устанавливаем 6:00
            if current.hour < 6:
                current = current.replace(hour=6, minute=0)
            # Если текущее время больше 23:45, устанавливаем на следующий день 6:00
            elif current.hour == 23 and current.minute > 45:
                current = current + timedelta(days=1)
                current = current.replace(hour=6, minute=0)
            self.set_datetime(current) 