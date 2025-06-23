from typing import Optional, List, Any
import os
import asyncpg
from dotenv import load_dotenv
load_dotenv()

class DataBase:
    def __init__(self, host: str, port: str, user: str, password: str, database: str):
        '''
        Инициализация подключения к PostgreSQL

        :param host: Хост базы данных
        :param port: Порт базы данных
        :param user: Имя пользователя
        :param password: Пароль пользователя
        :param database: Название базы данных
        '''
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection: Optional[asyncpg.Connection] = None

    async def connect(self) -> None:
        'Установка соединения с базой данных'
        dsn = (
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@db:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.connection = await asyncpg.connect(dsn)

    async def disconnect(self) -> None:
        'Закрытие соединения с базой данных'
        if self.connection:
            await self.connection.close()
            self.connection = None

    async def execute(self, query: str, *args) -> str:
        '''
        Выполнение SQL запроса без возврата результата

        :param query: SQL запрос
        :param args: Параметры запроса
        :return: Статус выполнения
        '''
        if not self.connection:
            await self.connect()

        return await self.connection.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        '''
        Выполнение SQL запроса с возвратом всех строк

        :param query: SQL запрос
        :param args: Параметры запроса
        :return: Список записей
        '''
        if not self.connection:
            await self.connect()

        return await self.connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        '''
        Выполнение SQL запроса с возвратом одной строки

        :param query: SQL запрос
        :param args: Параметры запроса
        :return: Одна запись или None
        '''
        if not self.connection:
            await self.connect()

        return await self.connection.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        '''
        Выполнение SQL запроса с возвратом одного значения

        :param query: SQL запрос
        :param args: Параметры запроса
        :return: Одно значение
        '''
        if not self.connection:
            await self.connect()

        return await self.connection.fetchval(query, *args)

    async def create_tables(self) -> None:
        '''Создание необходимых таблиц в базе данных'''
        if not self.connection:
            await self.connect()
