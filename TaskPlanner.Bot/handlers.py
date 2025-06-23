import logging
import os
from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ErrorEvent

from database import DataBase

from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

# Инициализация базы данных
db = DataBase(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)


#   Commands
@router.message(Command('start'))
async def cmd_start(message: Message):
    # Check if user exists, if not - add to database
    user = await db.fetchrow(
        'SELECT id FROM users WHERE telegramid = $1',
        str(message.from_user.id)
    )
    if not user:
        await db.execute(
            'INSERT INTO users (telegramid) VALUES ($1)',
            str(message.from_user.id)
        )

    await message.answer(
        '📝 Бот для управления задачами\n'
        'Используй команду /add чтобы создать задачу\n'
        'Или /help чтобы просмотреть список всех команд\n'
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Доступные команды:\n'
                         '/add - Добавить задачу\n'
                         '/edit - Изменить задачу\n'
                         '/delete - Удалить задачу\n'
                         '/list - Список задач\n'
                         '/enable - Включить уведомления\n'
                         '/disable - Выключить уведомления\n'
                         )


#   Tasks
@router.message(Command('add'))
async def cmd_add_task(message: Message):
    try:
        # Extract task details from message (assuming format: /add title; description; priority; duedate)
        parts = message.text.split(maxsplit=1)[1].split('; ')
        if len(parts) < 4:
            raise ValueError(
                'Неверный формат. Используйте: /add Заголовок; Описание; Приоритет(низкий, средний, высокий); 1Срок('
                'ГГГГ-ММ-ДД ЧЧ:ММ)')

        title = parts[0].strip()
        description = parts[1].strip()
        priority = parts[2].strip().lower()
        duedate_str = parts[3].strip()

        # Convert priority to ID
        priority_map = {'низкий': 1, 'средний': 2, 'высокий': 3}
        if priority not in priority_map:
            raise ValueError('Приоритет должен быть: низкий, средний или высокий')

        priority_id = priority_map[priority]

        # Parse due date
        try:
            duedate = datetime.strptime(duedate_str, '%Y-%m-%d %H:%M')
        except ValueError:
            raise ValueError('Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ')

        # Get user ID
        user = await db.fetchrow(
            'SELECT id FROM users WHERE telegramid = $1',
            str(message.from_user.id)
        )
        if not user:
            raise ValueError('Пользователь не найден')

        # Create task
        task_id = await db.fetchval(
            '''INSERT INTO tasks (statusid, priorityid, title, description, duedate)
                VALUES (1, $1, $2, $3, $4) RETURNING id''',
            priority_id, title, description, duedate
        )

        # Assign task to user
        await db.execute(
            'INSERT INTO tasksasignments (taskid, userid) VALUES ($1, $2)',
            task_id, user['id']
        )

        await message.answer('✅ Задача успешно добавлена')
    except (IndexError, ValueError) as e:
        await message.answer(
            f'❌ Ошибка: {str(e)}\nИспользуйте: /add Заголовок; Описание; Приоритет(низкий, средний, высокий); Срок('
            f'ГГГГ-ММ-ДД ЧЧ:ММ)')
    except Exception as e:
        await message.answer(f'❌ Неизвестная ошибка: {str(e)}')


@router.message(Command('edit'))
async def cmd_edit_task(message: Message):
    try:
        # Extract edit details (format: /edit task_id;field;new_value)
        parts = message.text.split(maxsplit=1)[1].split('; ')
        if len(parts) < 3:
            raise ValueError('Неверный формат. Используйте: /edit id Задачи; Поле; Новое значение')

        task_id = int(parts[0].strip())
        field = parts[1].strip().lower()
        new_value = parts[2].strip()

        # Validate field
        valid_fields = {'title', 'description', 'priority', 'status', 'duedate'}
        if field not in valid_fields:
            raise ValueError(f'Неверное поле. Допустимые значения: {', '.join(valid_fields)}')

        # Check if task belongs to user
        user_task = await db.fetchrow(
            '''SELECT t.id FROM tasks t
                JOIN tasksasignments ta ON t.id = ta.taskid
                JOIN users u ON ta.userid = u.id
                WHERE u.telegramid = $1 AND t.id = $2''',
            str(message.from_user.id), task_id
        )
        if not user_task:
            raise ValueError('Задача не найдена или у вас нет прав на её редактирование')

        # Prepare update based on field
        if field == 'priority':
            priority_map = {'низкий': 1, 'средний': 2, 'высокий': 3}
            if new_value.lower() not in priority_map:
                raise ValueError('Приоритет должен быть: низкий, средний или высокий')
            await db.execute(
                'UPDATE tasks SET priorityid = $1, updatedat = NOW() WHERE id = $2',
                priority_map[new_value.lower()], task_id
            )
        elif field == 'status':
            status_map = {'в работе': 1, 'завершена': 2, 'просрочена': 3}
            if new_value.lower() not in status_map:
                raise ValueError('Статус должен быть: в работе, завершена или просрочена')
            await db.execute(
                'UPDATE tasks SET statusid = $1, updatedat = NOW() WHERE id = $2',
                status_map[new_value.lower()], task_id
            )
        elif field == 'duedate':
            try:
                duedate = datetime.strptime(new_value, '%Y-%m-%d %H:%M')
            except ValueError:
                raise ValueError('Неверный формат даты. Используйте ГГГГ-ММ-ДД ЧЧ:ММ')
            await db.execute(
                'UPDATE tasks SET duedate = $1, updatedat = NOW() WHERE id = $2',
                duedate, task_id
            )
        else:  # title or description
            await db.execute(
                f'UPDATE tasks SET {field} = $1, updatedat = NOW() WHERE id = $2',
                new_value, task_id
            )

        await message.answer('✅ Задача обновлена')
    except (IndexError, ValueError) as e:
        await message.answer(f'❌ Ошибка: {str(e)}\nИспользуйте: /edit id Задачи; Поле; Новое значение')
    except Exception as e:
        await message.answer(f'❌ Неизвестная ошибка: {str(e)}')


@router.message(Command('delete'))
async def cmd_delete_task(message: Message):
    try:
        task_id = int(message.text.split(maxsplit=1)[1])

        # Check if task belongs to user
        user_task = await db.fetchrow(
            '''SELECT t.id FROM tasks t
                JOIN tasksasignments ta ON t.id = ta.taskid
                JOIN users u ON ta.userid = u.id
                WHERE u.telegramid = $1 AND t.id = $2''',
            str(message.from_user.id), task_id
        )
        if not user_task:
            raise ValueError('Задача не найдена или у вас нет прав на её удаление')

        # Delete task (cascade will handle assignments)
        await db.execute('DELETE FROM tasks WHERE id = $1', task_id)

        await message.answer('✅ Задача удалена')
    except (IndexError, ValueError):
        await message.answer('Использование: /delete <id>')
    except Exception as e:
        await message.answer(f'❌ Ошибка удаления: {str(e)}')


@router.message(Command('list'))
async def list_tasks(message: Message):
    try:
        # Get all tasks for user with status and priority names
        tasks = await db.fetch(
            '''SELECT t.id, t.title, t.description, s.statusname, p.priorityname, t.duedate
                FROM tasks t
                JOIN statuses s ON t.statusid = s.id
                JOIN priorities p ON t.priorityid = p.id
                JOIN tasksasignments ta ON t.id = ta.taskid
                JOIN users u ON ta.userid = u.id
                WHERE u.telegramid = $1
                ORDER BY t.duedate ASC''',
            str(message.from_user.id)
        )

        if not tasks:
            await message.answer('Нет активных задач')
            return

        response = ['Ваши задачи:\n']
        for task in tasks:
            response.append(
                f'id: {task['id']}\n'
                f'Заголовок(title): {task['title']}\n'
                f'Описание(description): {task['description']}\n'
                f'Статус(status): {task['statusname']}\n'
                f'Приоритет(priority): {task['priorityname']}\n'
                f'Срок(duedate): {task['duedate'].strftime('%Y-%m-%d %H:%M')}\n'
                '────────────'
            )

        # Split long messages to avoid Telegram limits
        full_message = '\n'.join(response)
        for i in range(0, len(full_message), 4096):
            await message.answer(full_message[i:i + 4096])

    except Exception as e:
        await message.answer(f'❌ Ошибка при получении списка задач: {str(e)}')


#   Notifications
@router.message(Command('enable'))
async def enable_notifications(message: Message):
    try:
        # Обновляем настройки уведомлений пользователя
        await db.execute(
            'UPDATE users SET notifications_enabled = TRUE WHERE telegramid = $1',
            str(message.from_user.id)
        )
        await message.answer('🔔 Уведомления включены')
    except Exception as e:
        logger.error(f'Ошибка при включении уведомлений: {e}')
        await message.answer('❌ Произошла ошибка при включении уведомлений')


@router.message(Command('disable'))
async def disable_notifications(message: Message):
    try:
        # Обновляем настройки уведомлений пользователя
        await db.execute(
            'UPDATE users SET notifications_enabled = FALSE WHERE telegramid = $1',
            str(message.from_user.id)
        )
        await message.answer('🔕 Уведомления отключены')
    except Exception as e:
        logger.error(f'Ошибка при отключении уведомлений: {e}')
        await message.answer('❌ Произошла ошибка при отключении уведомлений')


#   Errors
@router.error()
async def error_handler(event: ErrorEvent):
    logger.error(
        'Ошибка в обработчике',
        exc_info=event.exception,
        extra={'update': event.update.dict()}
    )
    await event.update.message.answer('⚠️ Произошла ошибка. Попробуйте позже.')
