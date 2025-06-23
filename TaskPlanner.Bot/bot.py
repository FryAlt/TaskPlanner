import logging
import os
import asyncio
from datetime import datetime, timedelta

import asyncpg

from handlers import router
from database import DataBase
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv


load_dotenv()


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

db = DataBase(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)


# Инициализация бота
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()


async def check_notifications():
    intervals = [
        ('1 день', timedelta(days=1)),
        ('6 часов', timedelta(hours=6)),
        ('1 час', timedelta(hours=1)),
    ]

    while True:
        try:
            now = datetime.now()

            for label, delta in intervals:
                target_time = now + delta
                try:
                    tasks = await db.fetch(
                        '''SELECT t.id, t.title, t.duedate, u.telegramid 
                           FROM tasks t
                           JOIN tasksasignments ta ON t.id = ta.taskid
                           JOIN users u ON ta.userid = u.id
                           WHERE t.duedate BETWEEN $1 AND $2 
                           AND t.statusid = 1''',
                        target_time - timedelta(minutes=1),
                        target_time
                    )
                except (asyncpg.exceptions.InterfaceError,
                       asyncpg.exceptions.PostgresConnectionError) as e:
                    logger.error(f"Ошибка соединения с БД: {e}. Пробуем переподключиться...")
                    await db.disconnect()
                    await db.connect()
                    continue

                for task in tasks:
                    await bot.send_message(
                        task['telegramid'],
                        f"⏰ Напоминание: задача '{task['title']}' должна быть выполнена через {label}!\n"
                        f'Срок выполнения: {task['duedate'].strftime('%Y-%m-%d %H:%M')}'
                    )

            # Просроченные задачи
            try:
                overdue_tasks = await db.fetch(
                    '''SELECT t.id, t.title, t.duedate, u.telegramid 
                       FROM tasks t
                       JOIN tasksasignments ta ON t.id = ta.taskid
                       JOIN users u ON ta.userid = u.id
                       WHERE t.duedate < $1 
                       AND t.statusid = 1''',
                    now
                )
            except (asyncpg.exceptions.InterfaceError,
                    asyncpg.exceptions.PostgresConnectionError) as e:
                logger.error(f"Ошибка соединения с БД: {e}. Пробуем переподключиться...")
                await db.disconnect()
                await db.connect()
                continue

            for task in overdue_tasks:
                try:
                    await db.execute(
                        'UPDATE tasks SET statusid = 3 WHERE id = $1',
                        task['id']
                    )
                except (asyncpg.exceptions.InterfaceError,
                        asyncpg.exceptions.PostgresConnectionError) as e:
                    logger.error(f"Ошибка соединения с БД: {e}. Пробуем переподключиться...")
                    await db.disconnect()
                    await db.connect()
                    continue

                await bot.send_message(
                    task['telegramid'],
                    f"❗ Задача '{task['title']}' просрочена!\n"
                    f'Срок выполнения был: {task['duedate'].strftime('%Y-%m-%d %H:%M')}'
                )

            await asyncio.sleep(60)

        except Exception as e:
            logger.error(f'Ошибка в check_notifications: {e}', exc_info=True)
            await asyncio.sleep(60)


@dp.shutdown()
async def on_shutdown():
    await db.disconnect()


async def main():
    logger.info('Подключение к базе данных...')
    await db.connect()
    logger.info('База данных подключена.')

    logger.info('Запуск фоновой задачи уведомлений...')
    asyncio.create_task(check_notifications())   # Запускаем фоновую задачу для проверки уведомлений

    # Инициализация роутеров
    dp.include_router(router)

    # Запуск бота
    try:
        logger.info('Starting bot...')
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f'Bot stopped with error: {e}', exc_info=True)
    finally:
        logger.info('Отключение от базы данных...')
        await on_shutdown()
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
