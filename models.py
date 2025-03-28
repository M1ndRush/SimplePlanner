from dataclasses import dataclass, field
from datetime import datetime, time
from enum import Enum
from typing import List, Optional

class TaskType(Enum):
    """Тип задачи: единоразовая или ежедневная"""
    SINGLE = "single"
    DAILY = "daily"

@dataclass
class Task:
    """
    Базовый класс для задач.
    
    Attributes:
        title: Название задачи
        duration_minutes: Длительность задачи в минутах
        task_type: Тип задачи (единоразовая/ежедневная)
        description: Описание задачи (опционально)
        scheduled_time: Запланированное время (опционально)
        id: Уникальный идентификатор задачи
        is_completed: Статус выполнения задачи
        created_at: Время создания задачи в системе
    """
    title: str
    duration_minutes: int
    task_type: TaskType
    description: Optional[str] = None
    scheduled_time: Optional[time] = None
    id: Optional[int] = None
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class SingleTask:
    """
    Единоразовая задача.
    
    Attributes:
        title: Название задачи
        duration_minutes: Длительность задачи в минутах
        description: Описание задачи (опционально)
        scheduled_time: Запланированное время (опционально)
        execution_date: Дата выполнения задачи (опционально)
        id: Уникальный идентификатор задачи
        is_completed: Статус выполнения задачи
        created_at: Время создания задачи в системе
    """
    title: str
    duration_minutes: int
    description: Optional[str] = None
    scheduled_time: Optional[time] = None
    execution_date: Optional[datetime] = None
    id: Optional[int] = None
    is_completed: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    task_type: TaskType = field(default=TaskType.SINGLE, init=False)

@dataclass
class DailyTask:
    """
    Ежедневная задача.
    
    Attributes:
        title: Название задачи
        duration_minutes: Длительность задачи в минутах
        weekdays: Список дней недели для выполнения (0 = понедельник, 6 = воскресенье)
        description: Описание задачи (опционально)
        scheduled_time: Запланированное время (опционально)
        id: Уникальный идентификатор задачи
        is_completed: Статус выполнения задачи
        is_unlimited: Флаг неограниченной длительности
        created_at: Время создания задачи в системе
    """
    title: str
    duration_minutes: int
    weekdays: List[int]
    description: Optional[str] = None
    scheduled_time: Optional[time] = None
    id: Optional[int] = None
    is_completed: bool = False
    is_unlimited: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    task_type: TaskType = field(default=TaskType.DAILY, init=False)

@dataclass
class ScheduledTask:
    """
    Задача, размещенная в распорядке дня.
    
    Attributes:
        task_id: ID связанной задачи
        date: Дата выполнения
        start_time: Время начала
        title: Название задачи
        duration_minutes: Длительность в минутах
        description: Описание задачи
        is_completed: Статус выполнения
    """
    task_id: int
    date: datetime
    start_time: time
    title: str
    duration_minutes: int
    description: Optional[str] = None
    is_completed: bool = False 