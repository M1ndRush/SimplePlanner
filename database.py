import sqlite3
from datetime import datetime, time
from typing import List, Optional, Union
from models import Task, SingleTask, DailyTask, ScheduledTask, TaskType

class Database:
    """
    Класс для работы с SQLite базой данных.
    Обеспечивает хранение задач и их расписания.
    """
    
    def __init__(self, db_name: str = "planner.db"):
        """
        Инициализация подключения к БД и создание необходимых таблиц.
        
        Args:
            db_name: Имя файла базы данных
        """
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()
    
    def _create_tables(self):
        """Создание необходимых таблиц в базе данных."""
        # Таблица для базовой информации о задачах
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                description TEXT,
                scheduled_time TEXT,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                task_type TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Таблица для единоразовых задач
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS single_tasks (
                task_id INTEGER PRIMARY KEY,
                execution_date TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # Таблица для ежедневных задач
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_tasks (
                task_id INTEGER PRIMARY KEY,
                weekdays TEXT NOT NULL,
                is_unlimited BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        # Таблица для размещенных в распорядке задач
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES tasks (id)
            )
        ''')
        
        self.conn.commit()
    
    def add_single_task(self, task: SingleTask) -> int:
        """
        Добавление единоразовой задачи в БД.
        
        Args:
            task: Объект единоразовой задачи
            
        Returns:
            ID добавленной задачи
        """
        self.cursor.execute(
            '''INSERT INTO tasks (
                title, duration_minutes, description, scheduled_time,
                task_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)''',
            (task.title, task.duration_minutes, task.description,
             task.scheduled_time.isoformat() if task.scheduled_time else None,
             TaskType.SINGLE.value,
             task.created_at.isoformat())
        )
        task_id = self.cursor.lastrowid
        
        self.cursor.execute(
            'INSERT INTO single_tasks (task_id, execution_date) VALUES (?, ?)',
            (task_id, task.execution_date.isoformat() if task.execution_date else None)
        )
        self.conn.commit()
        return task_id
    
    def add_daily_task(self, task: DailyTask) -> int:
        """
        Добавление ежедневной задачи в БД.
        
        Args:
            task: Объект ежедневной задачи
            
        Returns:
            ID добавленной задачи
        """
        self.cursor.execute(
            '''INSERT INTO tasks (
                title, duration_minutes, description, scheduled_time,
                task_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)''',
            (task.title, task.duration_minutes, task.description,
             task.scheduled_time.isoformat() if task.scheduled_time else None,
             TaskType.DAILY.value,
             task.created_at.isoformat())
        )
        task_id = self.cursor.lastrowid
        
        self.cursor.execute(
            'INSERT INTO daily_tasks (task_id, weekdays, is_unlimited) VALUES (?, ?, ?)',
            (task_id, ','.join(map(str, task.weekdays)), task.is_unlimited)
        )
        self.conn.commit()
        return task_id
    
    def add_scheduled_task(self, scheduled_task: ScheduledTask) -> int:
        """
        Добавление задачи в распорядок дня.
        
        Args:
            scheduled_task: Объект размещенной задачи
            
        Returns:
            ID добавленной записи в расписании
        """
        self.cursor.execute(
            '''INSERT INTO scheduled_tasks 
               (task_id, date, start_time, is_completed) 
               VALUES (?, ?, ?, ?)''',
            (scheduled_task.task_id,
             scheduled_task.date.date().isoformat(),
             scheduled_task.start_time.isoformat(),
             scheduled_task.is_completed)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_all_tasks(self) -> List[Union[SingleTask, DailyTask]]:
        """
        Получение всех задач из БД.
        
        Returns:
            Список всех задач
        """
        tasks = []
        self.cursor.execute('SELECT * FROM tasks')
        for task_row in self.cursor.fetchall():
            task_id, title, duration, description, scheduled_time, is_completed, task_type, created_at = task_row
            
            if task_type == TaskType.SINGLE.value:
                self.cursor.execute(
                    'SELECT execution_date FROM single_tasks WHERE task_id = ?',
                    (task_id,)
                )
                execution_date = self.cursor.fetchone()[0]
                tasks.append(SingleTask(
                    title=title,
                    duration_minutes=duration,
                    description=description,
                    scheduled_time=time.fromisoformat(scheduled_time) if scheduled_time else None,
                    execution_date=datetime.fromisoformat(execution_date) if execution_date else None,
                    id=task_id,
                    is_completed=bool(is_completed),
                    created_at=datetime.fromisoformat(created_at)
                ))
            else:
                self.cursor.execute(
                    'SELECT weekdays, is_unlimited FROM daily_tasks WHERE task_id = ?',
                    (task_id,)
                )
                weekdays_str, is_unlimited = self.cursor.fetchone()
                weekdays = [int(day) for day in weekdays_str.split(',')]
                tasks.append(DailyTask(
                    title=title,
                    duration_minutes=duration,
                    description=description,
                    scheduled_time=time.fromisoformat(scheduled_time) if scheduled_time else None,
                    weekdays=weekdays,
                    id=task_id,
                    is_completed=bool(is_completed),
                    is_unlimited=bool(is_unlimited),
                    created_at=datetime.fromisoformat(created_at)
                ))
        
        return tasks
    
    def get_scheduled_tasks_for_date(self, date: datetime) -> List[ScheduledTask]:
        """
        Получение всех задач, запланированных на определенную дату.
        
        Args:
            date: Дата, для которой нужно получить задачи
            
        Returns:
            Список запланированных задач
        """
        self.cursor.execute('''
            SELECT st.*, t.title, t.duration_minutes, t.description
            FROM scheduled_tasks st
            JOIN tasks t ON st.task_id = t.id
            WHERE st.date = ?
        ''', (date.date().isoformat(),))
        
        scheduled_tasks = []
        for row in self.cursor.fetchall():
            scheduled_id, task_id, date_str, start_time_str, is_completed, title, duration, description = row
            scheduled_tasks.append(ScheduledTask(
                task_id=task_id,
                date=datetime.fromisoformat(date_str),
                start_time=datetime.strptime(start_time_str, '%H:%M:%S').time(),
                title=title,
                duration_minutes=duration,
                description=description,
                is_completed=bool(is_completed)
            ))
        return scheduled_tasks
    
    def mark_task_completed(self, task_id: int, completed: bool = True):
        """
        Отметить задачу как выполненную/невыполненную.
        
        Args:
            task_id: ID задачи
            completed: Статус выполнения
        """
        self.cursor.execute(
            'UPDATE tasks SET is_completed = ? WHERE id = ?',
            (completed, task_id)
        )
        self.conn.commit()
    
    def mark_scheduled_task_completed(self, scheduled_id: int, completed: bool = True):
        """
        Отметить запланированную задачу как выполненную/невыполненную.
        
        Args:
            scheduled_id: ID записи в расписании
            completed: Статус выполнения
        """
        self.cursor.execute(
            'UPDATE scheduled_tasks SET is_completed = ? WHERE id = ?',
            (completed, scheduled_id)
        )
        self.conn.commit()
    
    def remove_scheduled_task(self, scheduled_id: int):
        """Удалить задачу из расписания."""
        self.cursor.execute('DELETE FROM scheduled_tasks WHERE id = ?', (scheduled_id,))
        self.conn.commit()
    
    def remove_task(self, task_id: int):
        """
        Удаление задачи и всех её запланированных экземпляров.
        
        Args:
            task_id: ID задачи для удаления
        """
        # Удаляем запланированные экземпляры
        self.cursor.execute('DELETE FROM scheduled_tasks WHERE task_id = ?', (task_id,))
        
        # Удаляем из таблицы single_tasks
        self.cursor.execute('DELETE FROM single_tasks WHERE task_id = ?', (task_id,))
        
        # Удаляем из таблицы daily_tasks
        self.cursor.execute('DELETE FROM daily_tasks WHERE task_id = ?', (task_id,))
        
        # Удаляем саму задачу
        self.cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        
        self.conn.commit()
    
    def is_task_scheduled(self, task_id: int) -> bool:
        """
        Проверяет, есть ли задача в расписании.
        
        Args:
            task_id: ID задачи
            
        Returns:
            True если задача есть в расписании, False иначе
        """
        self.cursor.execute(
            'SELECT COUNT(*) FROM scheduled_tasks WHERE task_id = ?',
            (task_id,)
        )
        count = self.cursor.fetchone()[0]
        return count > 0
    
    def remove_all_scheduled_instances(self, task_id: int):
        """
        Удаляет все запланированные экземпляры задачи из расписания.
        
        Args:
            task_id: ID задачи
        """
        self.cursor.execute('DELETE FROM scheduled_tasks WHERE task_id = ?', (task_id,))
        self.conn.commit()
    
    def update_scheduled_task_time(self, task_id: int, new_time: time, date: datetime = None):
        """
        Обновляет время запланированной задачи.
        Если задача ежедневная и date не указан, обновляет время для всех экземпляров.
        
        Args:
            task_id: ID задачи
            new_time: Новое время
            date: Дата конкретного экземпляра (для единоразовых задач)
        """
        if date:
            # Обновляем время только для конкретной даты
            self.cursor.execute(
                '''UPDATE scheduled_tasks 
                   SET start_time = ? 
                   WHERE task_id = ? AND date = ?''',
                (new_time.isoformat(), task_id, date.date().isoformat())
            )
        else:
            # Обновляем время для всех экземпляров задачи
            self.cursor.execute(
                'UPDATE scheduled_tasks SET start_time = ? WHERE task_id = ?',
                (new_time.isoformat(), task_id)
            )
        self.conn.commit()

    def is_daily_task(self, task_id: int) -> bool:
        """
        Проверяет, является ли задача ежедневной.
        
        Args:
            task_id: ID задачи
            
        Returns:
            True если задача ежедневная, False иначе
        """
        self.cursor.execute(
            'SELECT task_type FROM tasks WHERE id = ?',
            (task_id,)
        )
        result = self.cursor.fetchone()
        return result[0] == TaskType.DAILY.value if result else False
    
    def update_task(self, task: Union[SingleTask, DailyTask]):
        """
        Обновление существующей задачи.
        
        Args:
            task: Обновленная задача
        """
        # Обновляем базовую информацию
        self.cursor.execute(
            '''UPDATE tasks 
               SET title = ?, duration_minutes = ?, description = ?, 
                   scheduled_time = ?, is_completed = ?
               WHERE id = ?''',
            (task.title, task.duration_minutes, task.description,
             task.scheduled_time.isoformat() if task.scheduled_time else None,
             task.is_completed, task.id)
        )
        
        # Обновляем специфичные данные
        if isinstance(task, SingleTask):
            self.cursor.execute(
                'UPDATE single_tasks SET execution_date = ? WHERE task_id = ?',
                (task.execution_date.isoformat() if task.execution_date else None,
                 task.id)
            )
        else:
            self.cursor.execute(
                'UPDATE daily_tasks SET weekdays = ?, is_unlimited = ? WHERE task_id = ?',
                (','.join(map(str, task.weekdays)), task.is_unlimited, task.id)
            )
        
        self.conn.commit()
        
        # Обновляем время в запланированных экземплярах, если оно изменилось
        if task.scheduled_time:
            self.update_scheduled_task_time(task.id, task.scheduled_time)
    
    def __del__(self):
        """Закрытие соединения с БД при уничтожении объекта."""
        self.conn.close() 