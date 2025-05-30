# Simple Planner

Простой органайзер задач с возможностью планирования распорядка дня.

## Возможности

- Создание единоразовых и ежедневных задач
- Планирование распорядка дня с помощью drag & drop
- Календарь для навигации по датам
- Отслеживание выполнения задач
- Локальное хранение данных

## Требования

- Python 3.8 или выше
- PyQt6
- SQLite3

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/simple-planner.git
cd simple-planner
```

2. Создайте виртуальное окружение (рекомендуется):
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Использование

### Создание задач

1. Перейдите на вкладку "Управление задачами"
2. Выберите тип задачи (единоразовая или ежедневная)
3. Заполните необходимые поля:
   - Название задачи
   - Длительность
   - Для единоразовой задачи: дата выполнения
   - Для ежедневной задачи: дни недели и флаг неограниченной длительности
4. Нажмите "Создать задачу"

### Планирование распорядка

1. Перейдите на вкладку "Календарь и распорядок"
2. Выберите дату в календаре
3. Перетащите задачу из списка доступных задач на временную шкалу
4. Отпустите кнопку мыши, чтобы зафиксировать задачу в расписании

### Управление задачами в распорядке

- Для отметки выполнения задачи используйте соответствующую кнопку
- Для удаления задачи из распорядка используйте кнопку удаления

## Сборка в EXE

Для создания исполняемого файла используйте PyInstaller:

1. Установите PyInstaller:
```bash
pip install pyinstaller
```

2. Создайте EXE:
```bash
pyinstaller --onefile --windowed main.py
```

Исполняемый файл будет создан в папке `dist`. 