from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QCalendarWidget,
                               QScrollArea, QFrame, QLabel, QMenu, QPushButton,
                               QMessageBox, QGroupBox, QSplitter)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint, QTime
from PyQt6.QtGui import QPainter, QPen, QColor, QDragEnterEvent, QDropEvent, QDrag, QTextCharFormat
from datetime import datetime, time, timedelta
from models import SingleTask, DailyTask, ScheduledTask
from database import Database
from .edit_task_dialog import EditTaskDialog

class TimelineWidget(QFrame):
    """
    Виджет временной шкалы для отображения распорядка дня.
    Поддерживает drag & drop задач.
    """
    
    task_scheduled = pyqtSignal(ScheduledTask)
    task_removed = pyqtSignal(int)  # ID задачи
    
    def __init__(self, calendar_tab, parent=None):
        super().__init__(parent)
        self.calendar_tab = calendar_tab  # Сохраняем ссылку на родительский виджет
        self.setMinimumWidth(400)
        self.setMinimumHeight(800)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet("""
            TimelineWidget {
                background-color: white;
                border-radius: 6px;
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
        self.setAcceptDrops(True)
        
        # Настройка временной шкалы
        self.start_hour = 6  # 6:00
        self.end_hour = 24   # 00:00
        self.hour_height = 60  # пикселей на час
        
        # Список запланированных задач
        self.scheduled_tasks = []
        
        # Текущая дата (будет установлена позже)
        self.current_date = None
        
        # Включение отслеживания мыши для подсказок
        self.setMouseTracking(True)
        
        # Контекстное меню
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Текущая задача под курсором
        self.hovered_task = None
        
        # Данные для предварительного просмотра при перетаскивании
        self.preview_task = None
        self.preview_time = None
        self.preview_duration = None
        
        # Кнопки управления
        self.edit_button = QPushButton("✎", self)
        self.edit_button.setFixedSize(32, 32)
        self.edit_button.clicked.connect(self._edit_hovered_task)
        self.edit_button.hide()
        self.edit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.delete_button = QPushButton("✖", self)
        self.delete_button.setFixedSize(32, 32)
        self.delete_button.clicked.connect(self._delete_hovered_task)
        self.delete_button.hide()
        self.delete_button.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mouseMoveEvent(self, event):
        """Обработка движения мыши для отображения подсказок."""
        pos = event.position()
        x, y = int(pos.x()), int(pos.y())
        
        # Поиск задачи под курсором
        prev_hovered = self.hovered_task
        self.hovered_task = None
        for task in self.scheduled_tasks:
            task_y = self._hour_to_y(task.start_time.hour)
            task_y += (task.start_time.minute / 60) * self.hour_height
            task_height = (task.duration_minutes / 60) * self.hour_height
            
            if (40 <= x <= self.width() - 10 and
                task_y <= y <= task_y + task_height):
                self.hovered_task = task
                # Показываем кнопки управления
                if prev_hovered != self.hovered_task:
                    self._update_buttons_position(task_y)
                    self.edit_button.show()
                    self.delete_button.show()
                break
        
        # Скрываем кнопки, если курсор не над задачей
        if not self.hovered_task:
            self.edit_button.hide()
            self.delete_button.hide()
        
        self.update()  # Перерисовка для отображения подсказки
    
    def paintEvent(self, event):
        """Отрисовка временной шкалы и задач."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)  # Включаем сглаживание
        
        # Отрисовка часовых линий и меток времени
        pen = QPen(QColor("#dee2e6"))  # Светло-серый цвет для линий
        painter.setPen(pen)
        
        # Отрисовка основных часовых линий
        for hour in range(self.start_hour, self.end_hour + 1):
            y = self._hour_to_y(hour)
            painter.drawLine(30, y, self.width() - 10, y)
            
            # Отрисовка времени
            painter.setPen(QColor("#495057"))  # Цвет текста
            time_text = f"{hour:02d}:00"
            painter.drawText(5, y - 5, time_text)
            
            # Отрисовка 15-минутных делений
            if hour < self.end_hour:
                pen.setWidth(1)
                pen.setStyle(Qt.PenStyle.DotLine)
                pen.setColor(QColor("#e9ecef"))  # Более светлый цвет для делений
                painter.setPen(pen)
                for i in range(1, 4):
                    y_quarter = y + (self.hour_height * i) // 4
                    painter.drawLine(35, y_quarter, self.width() - 15, y_quarter)
        
        # Отрисовка запланированных задач
        for task in self.scheduled_tasks:
            self._draw_task(painter, task)
        
        # Отрисовка подсказки
        if self.hovered_task and self.hovered_task.description:
            self._draw_tooltip(painter, self.hovered_task)
        
        # Отрисовка предварительного просмотра при перетаскивании
        if self.preview_time and self.preview_duration:
            preview_color = QColor("#007bff")
            preview_color.setAlpha(128)  # Полупрозрачный
            y = self._hour_to_y(self.preview_time.hour)
            y += int((self.preview_time.minute / 60) * self.hour_height)
            height = int((self.preview_duration / 60) * self.hour_height)
            
            painter.fillRect(40, int(y), self.width() - 50, height, preview_color)
            painter.setPen(QPen(preview_color.darker(120)))
            painter.drawRect(40, int(y), self.width() - 50, height)
    
    def _draw_tooltip(self, painter: QPainter, task: ScheduledTask):
        """Отрисовка подсказки с описанием задачи."""
        if not task.description:
            return
        
        # Настройка шрифта и цвета
        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(QColor(255, 255, 220))  # Светло-желтый фон
        
        # Расчет позиции и размеров подсказки
        text = task.description
        font_metrics = painter.fontMetrics()
        text_width = font_metrics.horizontalAdvance(text)
        text_height = font_metrics.height()
        
        # Отрисовка фона подсказки
        margin = 5
        rect_x = self.width() - text_width - margin * 4
        rect_y = 10
        painter.drawRect(rect_x, rect_y,
                        text_width + margin * 2,
                        text_height + margin * 2)
        
        # Отрисовка текста
        painter.drawText(rect_x + margin, rect_y + margin + text_height,
                        task.description)
    
    def _show_context_menu(self, position):
        """Отображение контекстного меню."""
        # Поиск задачи под курсором
        y = position.y()
        task = None
        for t in self.scheduled_tasks:
            task_y = self._hour_to_y(t.start_time.hour)
            task_y += (t.start_time.minute / 60) * self.hour_height
            task_height = (t.duration_minutes / 60) * self.hour_height
            
            if task_y <= y <= task_y + task_height:
                task = t
                break
        
        if task:
            menu = QMenu(self)
            remove_action = menu.addAction("Убрать из расписания")
            action = menu.exec(self.mapToGlobal(position))
            
            if action == remove_action:
                # Удаляем все запланированные экземпляры задачи
                self.calendar_tab.db.remove_all_scheduled_instances(task.task_id)
                # Удаляем из текущего списка отображаемых задач
                self.scheduled_tasks = [t for t in self.scheduled_tasks if t.task_id != task.task_id]
                # Обновляем список доступных задач
                self.calendar_tab.update_available_tasks()
                # Обновляем отображение
                self.update()
    
    def _hour_to_y(self, hour: int) -> int:
        """Преобразование часа в координату Y на виджете."""
        return (hour - self.start_hour) * self.hour_height
    
    def _y_to_time(self, y: int) -> time:
        """Преобразование координаты Y в время."""
        total_minutes = (y / self.hour_height * 60) + (self.start_hour * 60)
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return time(hour=min(23, max(0, hours)), minute=minutes)
    
    def _draw_task(self, painter: QPainter, task: ScheduledTask):
        """Отрисовка блока задачи на временной шкале."""
        task_height = int((task.duration_minutes / 60) * self.hour_height)
        y = self._hour_to_y(task.start_time.hour)
        y += int((task.start_time.minute / 60) * self.hour_height)
        
        # Определение цвета в зависимости от статуса выполнения
        if task.is_completed:
            color = QColor("#6c757d")  # Серый для выполненных
        else:
            color = QColor("#007bff")  # Синий для активных
        
        # Подсветка при наведении
        if task == self.hovered_task:
            color = color.lighter(110)
        
        # Отрисовка с закругленными углами
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(40, int(y), self.width() - 50, task_height, 6, 6)
        
        # Отрисовка текста
        painter.setPen(QColor("white"))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        
        # Создаем прямоугольник для текста с отступами
        text_rect = painter.boundingRect(
            45, int(y), self.width() - 60, task_height,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            task.title
        )
        
        # Отрисовываем текст с правильными флагами
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            task.title
        )
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка начала перетаскивания."""
        if event.mimeData().hasText():
            # Получаем данные о перетаскиваемой задаче
            task_data = event.mimeData().text().split('|')
            self.preview_duration = int(task_data[1])
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event):
        """Обработка перемещения при перетаскивании."""
        if event.mimeData().hasText():
            # Получаем время с привязкой к 15-минутным интервалам
            y = int(event.position().y())
            self.preview_time = self._snap_to_grid(self._y_to_time(y))
            self.update()  # Перерисовка для отображения предпросмотра
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        """Обработка выхода перетаскивания за пределы виджета."""
        self.preview_time = None
        self.preview_duration = None
        self.update()

    def _snap_to_grid(self, t: time) -> time:
        """Привязка времени к 15-минутной сетке."""
        total_minutes = t.hour * 60 + t.minute
        # Округляем до ближайших 15 минут
        snapped_minutes = ((total_minutes + 7) // 15) * 15
        return time(snapped_minutes // 60, snapped_minutes % 60)

    def dropEvent(self, event: QDropEvent):
        """Обработка сброса перетаскиваемой задачи."""
        pos = event.position()
        # Используем привязку к сетке при определении времени
        drop_time = self._snap_to_grid(self._y_to_time(int(pos.y())))
        task_data = event.mimeData().text().split('|')
        task_id = int(task_data[0])
        duration = int(task_data[1])
        title = task_data[2]
        description = task_data[3] if len(task_data) > 3 else None
        
        # Проверяем, есть ли уже эта задача в расписании
        is_task_scheduled = self.calendar_tab.db.is_task_scheduled(task_id)
        is_daily = self.calendar_tab.db.is_daily_task(task_id)
        
        if is_task_scheduled:
            # Обновляем время существующей задачи
            if is_daily:
                # Для ежедневной задачи обновляем время для всех экземпляров
                self.calendar_tab.db.update_scheduled_task_time(task_id, drop_time)
            else:
                # Для единоразовой задачи обновляем время только для текущей даты
                self.calendar_tab.db.update_scheduled_task_time(task_id, drop_time, self.current_date)
        else:
            # Создаем новую задачу в расписании
            new_task = ScheduledTask(
                task_id=task_id,
                date=self.current_date,
                start_time=drop_time,
                title=title,
                duration_minutes=duration,
                description=description,
                is_completed=False
            )
            
            # Если это ежедневная задача, добавляем её на все выбранные дни
            if is_daily:
                # Получаем информацию о днях недели для задачи
                task = next((t for t in self.calendar_tab.db.get_all_tasks() if t.id == task_id), None)
                if task and isinstance(task, DailyTask):
                    current_date = datetime.now().date()
                    end_date = current_date + timedelta(days=30)
                    while current_date <= end_date:
                        if current_date.weekday() in task.weekdays:
                            scheduled_task = ScheduledTask(
                                task_id=task_id,
                                date=datetime.combine(current_date, time()),
                                start_time=drop_time,
                                title=title,
                                duration_minutes=duration,
                                description=description,
                                is_completed=False
                            )
                            self.calendar_tab.db.add_scheduled_task(scheduled_task)
                        current_date += timedelta(days=1)
            else:
                # Для единоразовой задачи просто добавляем её в расписание
                self.calendar_tab.db.add_scheduled_task(new_task)
            
            self.task_scheduled.emit(new_task)
        
        # Обновляем отображение
        self.scheduled_tasks = self.calendar_tab.db.get_scheduled_tasks_for_date(self.current_date)
        self.update()
        
        # Обновляем список доступных задач
        self.calendar_tab.update_available_tasks()
        
        # Очищаем предпросмотр
        self.preview_time = None
        self.preview_duration = None
        
        event.acceptProposedAction()

    def mousePressEvent(self, event):
        """Обработка нажатия кнопки мыши для начала перетаскивания."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Поиск задачи под курсором
            y = int(event.position().y())
            for task in self.scheduled_tasks:
                task_y = self._hour_to_y(task.start_time.hour)
                task_y += (task.start_time.minute / 60) * self.hour_height
                task_height = (task.duration_minutes / 60) * self.hour_height
                
                if task_y <= y <= task_y + task_height:
                    # Начинаем перетаскивание
                    mime_data = QMimeData()
                    description = task.description if task.description else ""
                    mime_data.setText(f"{task.task_id}|{task.duration_minutes}|{task.title}|{description}")
                    
                    drag = QDrag(self)
                    drag.setMimeData(mime_data)
                    
                    # Временно скрываем задачу
                    self.scheduled_tasks = [t for t in self.scheduled_tasks if t.task_id != task.task_id]
                    self.update()
                    
                    # Выполняем перетаскивание
                    result = drag.exec()
                    
                    # Если перетаскивание отменено
                    if result == Qt.DropAction.IgnoreAction:
                        # Возвращаем задачу на место
                        self.scheduled_tasks.append(task)
                        self.update()
                    
                    break
        else:
            super().mousePressEvent(event)

    def _update_buttons_position(self, task_y: int):
        """Обновление позиции кнопок управления."""
        margin = 5
        self.edit_button.move(self.width() - 58, int(task_y) + margin)
        self.delete_button.move(self.width() - 29, int(task_y) + margin)
    
    def _edit_hovered_task(self):
        """Редактирование задачи под курсором."""
        if self.hovered_task:
            # Получаем оригинальную задачу из БД
            task = next((t for t in self.calendar_tab.db.get_all_tasks() 
                        if t.id == self.hovered_task.task_id), None)
            if task:
                dialog = EditTaskDialog(task, self.calendar_tab.db, self)
                if dialog.exec():
                    edited_task = dialog.get_edited_task()
                    self.calendar_tab.db.update_task(edited_task)
                    # Обновляем отображение
                    self.scheduled_tasks = self.calendar_tab.db.get_scheduled_tasks_for_date(self.current_date)
                    self.update()
                    # Обновляем список доступных задач
                    self.calendar_tab.update_available_tasks()
    
    def _delete_hovered_task(self):
        """Удаление задачи под курсором."""
        if self.hovered_task:
            reply = QMessageBox.question(
                self,
                "Подтверждение удаления",
                f"Вы действительно хотите удалить задачу '{self.hovered_task.title}'?\n"
                "Это действие нельзя отменить.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Удаляем задачу из БД
                self.calendar_tab.db.remove_task(self.hovered_task.task_id)
                # Обновляем отображение
                self.scheduled_tasks = self.calendar_tab.db.get_scheduled_tasks_for_date(self.current_date)
                self.hovered_task = None
                self.edit_button.hide()
                self.delete_button.hide()
                self.update()
                # Обновляем список доступных задач
                self.calendar_tab.update_available_tasks()

class TaskWidget(QLabel):
    """Виджет для отображения задачи."""
    
    def __init__(self, task, calendar_tab, parent=None):
        super().__init__(task.title, parent)
        self.task = task
        self.calendar_tab = calendar_tab
        self.setFrameStyle(QFrame.Shape.Box)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(40)
        self.setProperty('task_id', task.id)
        self.setProperty('duration', task.duration_minutes)
        self.setMouseTracking(True)
        
        # Состояние выделения
        self.is_selected = False
        
        # Кнопки управления
        self.edit_button = QPushButton("✎", self)
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.clicked.connect(self.edit_task)
        self.edit_button.hide()
        
        self.delete_button = QPushButton("✖", self)
        self.delete_button.setFixedSize(24, 24)
        self.delete_button.clicked.connect(self.delete_task)
        self.delete_button.hide()
        
        # Позиционирование кнопок
        self.update_buttons_position()
    
    def update_buttons_position(self):
        """Обновление позиции кнопок."""
        margin = 5
        self.edit_button.move(self.width() - 58, margin)
        self.delete_button.move(self.width() - 29, margin)
    
    def resizeEvent(self, event):
        """Обработка изменения размера виджета."""
        super().resizeEvent(event)
        self.update_buttons_position()
    
    def enterEvent(self, event):
        """Обработка наведения мыши."""
        self.is_selected = True
        self.edit_button.show()
        self.delete_button.show()
        self.update()
    
    def leaveEvent(self, event):
        """Обработка ухода мыши."""
        self.is_selected = False
        self.edit_button.hide()
        self.delete_button.hide()
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка виджета."""
        super().paintEvent(event)
        if self.is_selected:
            painter = QPainter(self)
            pen = QPen(QColor(70, 130, 180))  # Steel Blue
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRect(1, 1, self.width() - 2, self.height() - 2)
    
    def edit_task(self):
        """Редактирование задачи."""
        dialog = EditTaskDialog(self.task, self.calendar_tab.db, self)
        if dialog.exec():
            edited_task = dialog.get_edited_task()
            self.calendar_tab.db.update_task(edited_task)
            self.calendar_tab.update_available_tasks()
    
    def delete_task(self):
        """Удаление задачи."""
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить задачу '{self.task.title}'?\n"
            "Это действие нельзя отменить.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.calendar_tab.db.remove_task(self.task.id)
            self.calendar_tab.update_available_tasks()

class TaskListWidget(QScrollArea):
    """Виджет для отображения доступных задач."""
    
    def __init__(self, calendar_tab, parent=None):
        super().__init__(parent)
        self.calendar_tab = calendar_tab
        self.setWidgetResizable(True)
        self.setMinimumWidth(200)
        self.setMaximumHeight(300)
        self.setAcceptDrops(True)
        
        # Контейнер для задач
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(self.container)
        
        self.tasks = []
    
    def update_tasks(self, tasks: list[SingleTask | DailyTask]):
        """Обновление списка доступных задач."""
        # Очистка старых задач
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().deleteLater()
        
        # Фильтруем только незапланированные задачи
        self.tasks = [task for task in tasks if not self.calendar_tab.db.is_task_scheduled(task.id)]
        
        # Добавление новых задач
        for task in self.tasks:
            task_widget = TaskWidget(task, self.calendar_tab, self)
            task_widget.mousePressEvent = lambda e, w=task_widget: self._start_drag(e, w)
            self.layout.addWidget(task_widget)
    
    def _start_drag(self, event, widget):
        """Начало операции перетаскивания задачи."""
        if event.button() == Qt.MouseButton.LeftButton:
            mime_data = QMimeData()
            task_id = widget.property('task_id')
            duration = widget.property('duration')
            description = widget.task.description if widget.task.description else ""
            mime_data.setText(f"{task_id}|{duration}|{widget.task.title}|{description}")
            
            drag = QDrag(widget)
            drag.setMimeData(mime_data)
            
            # Временно скрываем задачу из списка
            widget.hide()
            
            # Выполняем перетаскивание
            result = drag.exec()
            
            # Если перетаскивание отменено, возвращаем задачу в список
            if result == Qt.DropAction.IgnoreAction:
                widget.show()
            else:
                # Обновляем список задач после успешного перетаскивания
                self.update_tasks(self.calendar_tab.db.get_all_tasks())

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка начала перетаскивания над виджетом."""
        if event.mimeData().hasText():
            event.setDropAction(Qt.DropAction.MoveAction)
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Обработка сброса задачи в список доступных."""
        if event.mimeData().hasText():
            task_data = event.mimeData().text().split('|')
            task_id = int(task_data[0])
            
            # Удаляем все экземпляры задачи из расписания
            self.calendar_tab.db.remove_all_scheduled_instances(task_id)
            
            # Обновляем список задач
            self.update_tasks(self.calendar_tab.db.get_all_tasks())
            
            event.acceptProposedAction()
        
        self.update()

class CalendarTab(QWidget):
    """Вкладка с календарем и распорядком дня."""
    
    task_scheduled = pyqtSignal(ScheduledTask)
    task_removed = pyqtSignal(int)
    
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
                border: 1px solid #dee2e6;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                padding-top: 20px;
            }
            QGroupBox::title {
                color: #212529;
                padding: 0 15px;
            }
            QCalendarWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 10px;
            }
            QCalendarWidget QWidget {
                alternate-background-color: #f8f9fa;
            }
            QCalendarWidget QToolButton {
                color: #212529;
                padding: 6px;
                border: none;
                border-radius: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background-color: #e9ecef;
            }
            QCalendarWidget QMenu {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QCalendarWidget QSpinBox {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 3px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QLabel {
                color: #495057;
                font-size: 14px;
                font-weight: bold;
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
        
        # Левая панель с календарем и списком задач
        left_panel = QWidget()
        left_panel_layout = QVBoxLayout(left_panel)
        left_panel_layout.setSpacing(20)
        left_panel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Календарь
        calendar_group = QGroupBox("Календарь")
        calendar_layout = QVBoxLayout()
        calendar_layout.setContentsMargins(15, 25, 15, 15)
        
        self.calendar = QCalendarWidget()
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setGridVisible(True)
        
        # Устанавливаем минимальную дату как начало текущего года
        current_date = datetime.now()
        min_date = datetime(current_date.year, 1, 1)
        self.calendar.setMinimumDate(min_date)
        
        self.calendar.selectionChanged.connect(self._on_date_selected)
        
        # Настройка отображения прошедших дней
        self._update_calendar_format()
        
        calendar_layout.addWidget(self.calendar)
        calendar_group.setLayout(calendar_layout)
        
        # Список доступных задач
        tasks_group = QGroupBox("Доступные задачи")
        tasks_layout = QVBoxLayout()
        tasks_layout.setContentsMargins(15, 25, 15, 15)
        
        self.task_list = TaskListWidget(self)
        tasks_layout.addWidget(self.task_list)
        tasks_group.setLayout(tasks_layout)
        
        left_panel_layout.addWidget(calendar_group)
        left_panel_layout.addWidget(tasks_group)
        
        # Временная шкала
        timeline_group = QGroupBox("Распорядок дня")
        timeline_layout = QVBoxLayout()
        timeline_layout.setContentsMargins(15, 25, 15, 15)
        
        self.timeline = TimelineWidget(self)
        self.timeline.task_scheduled.connect(self._on_task_scheduled)
        self.timeline.task_removed.connect(self._on_task_removed)
        timeline_layout.addWidget(self.timeline)
        timeline_group.setLayout(timeline_layout)
        
        # Добавляем виджеты в разделитель
        splitter.addWidget(left_panel)
        splitter.addWidget(timeline_group)
        
        # Устанавливаем начальные размеры
        splitter.setSizes([400, self.width() - 400])
        
        # Добавляем разделитель в главный layout
        layout.addWidget(splitter)
        
        # Загрузка начальных данных
        self.update_available_tasks()
        self._on_date_selected()
    
    def _update_calendar_format(self):
        """Обновление форматирования календаря для отображения прошедших дней."""
        current_date = datetime.now().date()
        text_format = self.calendar.dateTextFormat(current_date)
        
        # Устанавливаем серый цвет для прошедших дней
        past_format = QTextCharFormat()
        past_format.setForeground(QColor("#6c757d"))  # Серый цвет
        past_format.setBackground(QColor("#f8f9fa"))  # Светло-серый фон
        
        # Применяем формат к прошедшим дням
        date = self.calendar.minimumDate().toPyDate()
        while date < current_date:
            self.calendar.setDateTextFormat(date, past_format)
            date += timedelta(days=1)
    
    def showEvent(self, event):
        """Обработчик события показа виджета."""
        super().showEvent(event)
        self._update_calendar_format()  # Обновляем форматирование при показе
    
    def _on_date_selected(self):
        """Обработка выбора даты в календаре."""
        selected_date = self.calendar.selectedDate().toPyDate()
        self.timeline.current_date = datetime.combine(selected_date, time())
        
        # Загрузка задач для выбранной даты
        scheduled_tasks = self.db.get_scheduled_tasks_for_date(self.timeline.current_date)
        self.timeline.scheduled_tasks = scheduled_tasks
        self.timeline.update()
    
    def update_available_tasks(self):
        """Обновление списка доступных задач."""
        tasks = self.db.get_all_tasks()
        self.task_list.update_tasks(tasks)
    
    def _on_task_scheduled(self, scheduled_task: ScheduledTask):
        """Обработка добавления задачи в расписание."""
        self.db.add_scheduled_task(scheduled_task)
        self.task_scheduled.emit(scheduled_task)
    
    def _on_task_removed(self, task_id: int):
        """Обработка удаления задачи из расписания."""
        # Сначала удаляем из БД
        self.db.remove_scheduled_task(task_id)
        # Затем обновляем список доступных задач
        self.update_available_tasks()
        # И отправляем сигнал
        self.task_removed.emit(task_id) 