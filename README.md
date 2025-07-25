# TaskPlanner - Telegram Bot
TaskPlanner - это Telegram-бот для управления задачами и планирования дел. Бот позволяет пользователям создавать, редактировать, удалять и отслеживать выполнение задач, а также получать напоминания.
## Основной функционал:
- Создание задач с указанием названия, описания, даты выполнения, статуса и приоритета

- Управление задачами (редактирование, удаление, отметка о выполнении)

- Напоминания о предстоящих задачах

## Технологический стек:
Язык программирования: Python 3.13+

Фреймворк: aiogram 3.20 (для Telegram бота)

База данных: PostgreSQL 14

Асинхронная работа: asyncio

Контейнеризация: Docker + Docker Compose

Логирование: logging

Конфигурация: dotenv (для валидации .env)

## Требования для запуска
### Переменные окружения:
Создайте файл `.env` в корне проекта со следующими переменными:
```ini
# Telegram
BOT_TOKEN=your_telegram_bot_token

# Database
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=taskplanner_db
DB_USER=username
DB_PASSWORD=password

# pgAdmin
PGADMIN_EMAIL=your_email
PGADMIN_PASSWORD=password
```
### Доступ к сервисам после запуска:
Telegram бот: доступен по токену, указанному в `.env`

pgAdmin: доступен внутри по адресу вашего сервера `host:8080`

## Описание структуры проекта
- `sql/` - Cодержит SQL-скрипты, связанные с работой базы данных
- `sql/create_table.sql` - SQL-скрипт для создания всех сущностей необходиммых для работы Telegram Бота
- `.env` - Файл для хранения переменных окружения
- `bot.py` - Основной модуль бота, содержащий логику инициализации и запуска
- `database.py` - Модуль для работы с базой данных (подключение, запросы).
- `docker-compose.yaml` - Файл для настройки и управления мультиконтейнерными приложениями Docker
- `Dockerfile` - Инструкции для сборки Docker-образа приложения.
- `handlers.py` - Модуль с обработчиками команд и событий бота.
- `requirements.txt`- Список зависимостей Python

## База данных
Используемая СУБД - `PostgreSQL`

ER Diagram представленна в файле `ERD.png`

### Список сущностей:

**Priorities (Приоритеты)**

    id - уникальный идентификатор приоритета (первичный ключ)

    priorityname - название приоритета (например, "Высокий", "Средний", "Низкий")

**Statuses (Статусы)**

    id - уникальный идентификатор статуса (первичный ключ)

    statusname - название статуса (например, "В работе", "Завершена", "Просрочена")

**Users (Пользователи)**

    id - уникальный идентификатор пользователя (первичный ключ)

    telegramid - идентификатор пользователя в Telegram

    notifications_enabled - флаг, указывающий включены ли уведомления для пользователя

**Tasks (Задачи)**

    id - уникальный идентификатор задачи (первичный ключ)

    statusid - идентификатор статуса задачи (внешний ключ к таблице Statuses)

    priorityid - идентификатор приоритета задачи (внешний ключ к таблице Priorities)

    title - заголовок задачи

    description - подробное описание задачи

    createdat - дата и время создания задачи

    updatedat - дата и время последнего обновления задачи

    duedate - Крайний срок выполнения задачи

**TasksAssignments (Назначения задач)**

    id - уникальный идентификатор назначения (первичный ключ)

    taskid - идентификатор задачи (внешний ключ к таблице Tasks)

    userid - идентификатор пользователя (внешний ключ к таблице Users)

    assigndate - дата и время назначения задачи пользователю