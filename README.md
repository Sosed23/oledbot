# Telegram бот для заказа запасных частей для OLED дисплеев

Данный проект представляет собой Telegram бота для заказа запасных частей для OLED дисплеев, разработанного с использованием фреймворка **Aiogram 3**, **SQLAlchemy** для работы с базой данных и **Alembic** для управления миграциями.

Для логирования используется удобная библиотека loguru. Благодаря этому логи красиво подсвечиваются в консоли и фоном записываются в файл логов.

## Технологический стек

- **Telegram API**: Aiogram 3
- **ORM**: SQLAlchemy с asyncpg
- **База данных**: PostgreSQL
- **Система миграций**: Alembic

## Обзор архитектуры

Проект следует архитектуре, вдохновленной микросервисами и лучшими практиками FastAPI. Каждый функциональный компонент бота организован как мини-сервис, что обеспечивает модульность разработки и обслуживания.

### Структура проекта

```
├── bot/
│   ├── migration/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── README
│   ├── dao/
│   │   └── base.py
│   ├── users/
│   │   ├── keyboards/
│   │   ├── dao.py
│   │   ├── models.py
│   │   └── router.py
│   ├── stocks/
│   │   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── dao.py
│   │   ├── group_router.py
│   │   ├── handlers_back_cover.py
│   │   ├── handlers_crash_display.py
│   │   ├── handlers_production.py
│   │   ├── handlers_re_gluing.py
│   │   ├── handlers_spare_parts.py
│   │   ├── models_cart.py
│   │   ├── models_order.py
│   │   ├── router_aiagent.py
│   │   ├── router_cart.py
│   │   ├── router_order.py
│   │   ├── router_product.py
│   │   └── router_search.py
│   ├── utils/
│   ├── ai_agent.py
│   ├── config.py
│   ├── database.py
│   ├── log.txt
│   ├── main.py
│   ├── operations.py
│   ├── planfix.py
│   ├── planfix_order.py
│   └── webhook.py
├── alembic.ini
├── Dockerfile
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

### Компоненты мини-сервиса

Каждый мини-сервис имеет следующую структуру:

- **keyboards/**: Клавиатуры Telegram (текстовые и инлайн)
- **dao.py**: Объекты доступа к базе данных через SQLAlchemy
- **models.py**: Модели SQLAlchemy, специфичные для сервиса
- **router.py**: Обработчики Aiogram для сервиса

## Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=[12345,344334]
PLANFIX_TOKEN=your_planfix_token
PLANFIX_URL_REST=https://yourcompany.planfix.ru/rest/
N8N_AIAGENT_WEBHOOK=https://your-n8n-webhook-url
TARGET_CHAT_ID=your_target_chat_id
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASS=your_database_password
```

- `BOT_TOKEN`: Получите у [BotFather](https://t.me/BotFather)
- `ADMIN_IDS`: Список Telegram ID администраторов бота. Можно получить тут Получите у [IDBot Finder Pro](https://t.me/get_tg_ids_universeBOT)
- `PLANFIX_TOKEN`: Токен API для интеграции с Planfix
- `PLANFIX_URL_REST`: URL REST API Planfix
- `N8N_AIAGENT_WEBHOOK`: URL вебхука для интеграции с n8n AI Agent
- `TARGET_CHAT_ID`: ID чата для отправки уведомлений
- `DB_HOST`: Хост базы данных PostgreSQL
- `DB_PORT`: Порт базы данных PostgreSQL
- `DB_NAME`: Имя базы данных
- `DB_USER`: Пользователь базы данных
- `DB_PASS`: Пароль пользователя базы данных

### Зависимости

```
aiofiles==24.1.0
aiogram==3.19.0
aiohappyeyeballs==2.4.4
aiohttp==3.10.11
aiosignal==1.3.2
aiosqlite==0.20.0
alembic==1.13.3
annotated-types==0.7.0
anyio==4.9.0
asyncpg==0.30.0
attrs==25.1.0
beautifulsoup4==4.13.3
certifi==2024.12.14
charset-normalizer==3.4.1
click==8.1.8
colorama==0.4.6
fastapi==0.115.12
frozenlist==1.5.0
greenlet==3.1.1
h11==0.14.0
httpcore==1.0.7
httpx==0.28.1
idna==3.10
loguru==0.7.2
magic-filter==1.0.12
Mako==1.3.8
MarkupSafe==3.0.2
multidict==6.1.0
propcache==0.2.1
psycopg2-binary==2.9.10
pydantic==2.9.2
pydantic-settings==2.5.2
pydantic_core==2.23.4
python-dotenv==1.0.1
redis==5.2.1
requests==2.32.3
sniffio==1.3.1
soupsieve==2.6
SQLAlchemy==2.0.37
starlette==0.46.1
typing_extensions==4.12.2
urllib3==2.3.0
uvicorn==0.34.0
win32_setctime==1.2.0
yarl==1.18.3
```

## Управление базой данных

### Конфигурация базовой модели

В проекте используется базовая модель SQLAlchemy с общими полями:

```python
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  # Базовый класс будет абстрактным, чтобы не создавать отдельную таблицу для него

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    @classmethod
    @property
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + 's'

    def to_dict(self) -> dict:
        # Метод для преобразования объекта в словарь
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

В проекте используется базовая модель SQLAlchemy с общими полями:

```python
class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True  # Базовый класс будет абстрактным, чтобы не создавать отдельную таблицу для него

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now()
    )

    return cls.__name__.lower() + 's'

    def to_dict(self) -> dict:
        # Метод для преобразования объекта в словарь
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

### Объекты доступа к данным (DAO)
```

### Объекты доступа к данным (DAO)

Проект реализует базовый класс BaseDAO с общими операциями базы данных:

- `find_one_or_none_by_id` - поиск по ID
- `find_one_or_none` - поиск одной записи по фильтру
- `find_all` - поиск всех записей по фильтру
- `add` - добавление записи
- `add_many` - добавление нескольких записей
- `update` - обновление записей
- `delete` - удаление записей
- `count` - подсчет количества записей
- `paginate` - пагинация
- `find_by_ids` - поиск по нескольким ID
- `upsert` - создание или обновление записи
- `bulk_update` - массовое обновление

Сервис-специфичные DAO наследуются от BaseDAO:

```python
from bot.dao.base import BaseDAO
from bot.users.models import User

class UserDAO(BaseDAO):
    model = User
```

Пример использования:
```python
user_info = await UserDAO.find_one_or_none(telegram_id=user_id)

await UserDAO.add(
    telegram_id=user_id,
    username=message.from_user.username,
    first_name=message.from_user.first_name,
    last_name=message.from_user.last_name,
    referral_id=ref_id
)
```

В проекте также используются DAO для работы с другими сущностями:
- `Cart` - корзина пользователя
- `Order` - заказы пользователей
- `OrderItem` - элементы заказов
- `OrderStatusHistory` - история статусов заказов
- `Model` - модели устройств

## Миграции базы данных

1. Определите ваши модели
2. Импортируйте модели в `migration/env.py`
3. Сгенерируйте файл миграции:
```bash
alembic revision --autogenerate -m "Описание изменений"
```
4. Примените миграции:
```bash
alembic upgrade head
```

## Главный файл

В корне папки bot есть файл `main.py`. Это основной файл проекта через который происходит сборка и запуск телеграмм бота. В этот файл импортируются роутеры, прописываются функции запуска и завершения работы бота, прписываются логи и прочее. Также в этом файле реализованы middleware для интеграции с Planfix и пересылки сообщений в Telegram-группу.

```python
import asyncio
from contextlib import asynccontextmanager
import uvicorn
from aiogram import types
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from loguru import logger
import re

from bot.config import bot, admins, dp, target_chat_id
from bot.users.router import user_router
from bot.stocks.router_product import product_router
from bot.stocks.router_cart import cart_router
from bot.stocks.router_search import search_router
from bot.stocks.router_order import order_router
from bot.stocks.router_aiagent import aiagent_router
from bot.stocks.group_router import group_router
from bot.webhook import app as fastapi_app  # Импортируем FastAPI-приложение
from bot.planfix import add_incoming_comment_to_chat, add_outgoing_comment_to_chat
from bot.users.dao import UserDAO

# Middleware для пересылки входящих сообщений (от пользователя к боту)
class ForwardIncomingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        # Реализация middleware для пересылки входящих сообщений
        # ...

# Middleware для пересылки исходящих сообщений (от бота к пользователю) в Planfix и Telegram-группу
class ForwardOutgoingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        # Реализация middleware для пересылки исходящих сообщений
        # ...

# Функция, которая настроит командное меню
async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

# Функция, которая выполнится когда бот запустится
async def start_bot():
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except:
            pass
    logger.info("Бот успешно запущен.")

# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
    logger.error("Бот остановлен!")

# Функция для запуска бота и FastAPI
async def run_all():
    # Запускаем polling для бота
    logger.info("Starting bot polling...")
    bot_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

    # Запускаем FastAPI-сервер
    logger.info("Starting FastAPI server...")
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    fastapi_task = asyncio.create_task(server.serve())

    # Ожидаем завершения обеих задач
    await asyncio.gather(bot_task, fastapi_task)

# Функция для регистрации роутеров и middleware
def setup_bot():
    dp.message.middleware(ForwardIncomingMessageMiddleware())
    dp.message.outer_middleware(ForwardOutgoingMessageMiddleware())
    dp.callback_query.outer_middleware(ForwardOutgoingMessageMiddleware())

    dp.include_router(user_router)
    dp.include_router(product_router)
    dp.include_router(cart_router)
    dp.include_router(search_router)
    dp.include_router(order_router)
    dp.include_router(aiagent_router)
    dp.include_router(group_router)

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

if __name__ == "__main__":
    setup_bot()
    asyncio.run(run_all())
```

Основные особенности реализации:
1. Использование middleware для интеграции с Planfix и пересылки сообщений в Telegram-группу
2. Поддержка FastAPI для вебхуков от внешних сервисов (n8n AI Agent)
3. Регистрация множества роутеров для различных функций бота

## Начало работы

1. Клонируйте репозиторий:
```bash
git clone <url-to-your-repository> .
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Создайте файл `.env` с необходимыми переменными окружения (см. раздел "Конфигурация")

4. Примените миграции базы данных:
```bash
alembic upgrade head
```

5. Запустите бота:
```bash
python -m bot.main
```

## Лучшие практики

- Поддерживайте модульность сервисов, фокусируясь на конкретной функциональности
- Используйте BaseDAO для согласованных операций с базой данных
- Следуйте установленной структуре проекта для новых функций
- Используйте Alembic для всех изменений схемы базы данных
- Используйте переменные окружения для конфигурации

---

