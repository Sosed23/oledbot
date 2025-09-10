import os
from typing import List
from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Settings(BaseSettings):
    BOT_TOKEN: str
    PLANFIX_TOKEN: str
    PLANFIX_URL_REST: str
    N8N_AIAGENT_WEBHOOK: str
    TARGET_CHAT_ID: int
    ADMIN_IDS: List[int]
    API_BASE: str
    FORMAT_LOG: str = "{time:YYYY-MM-DD at HH:mm:ss} | {level} | {message}"
    LOG_ROTATION: str = "10 MB"
    DB_HOST: str = os.environ.get("DB_HOST")
    DB_PORT: str = os.environ.get("DB_PORT")
    DB_NAME: str = os.environ.get("DB_NAME")
    DB_USER: str = os.environ.get("DB_USER")
    DB_PASS: str = os.environ.get("DB_PASS")
    
    DB_URL: str = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(
            os.path.abspath(__file__)), "..", ".env"),
        extra="allow"
    )

# Получаем параметры для загрузки переменных среды
settings = Settings()

# Инициализируем бота и диспетчер
bot = Bot(token=settings.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
admins = settings.ADMIN_IDS

log_file_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), "log.txt")
logger.add(log_file_path, format=settings.FORMAT_LOG,
           level="INFO", rotation=settings.LOG_ROTATION)
logger.add("stderr", format=settings.FORMAT_LOG, level="INFO")

database_url = settings.DB_URL
pf_token = settings.PLANFIX_TOKEN
pf_url_rest = settings.PLANFIX_URL_REST
n8n_aiagent_webhook = settings.N8N_AIAGENT_WEBHOOK
target_chat_id = settings.TARGET_CHAT_ID
db_host = settings.DB_HOST
api_base = settings.API_BASE
