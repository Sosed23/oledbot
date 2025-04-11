import json
from typing import List, Tuple
import redis.asyncio as redis
from loguru import logger
from bot.config import db_host

redis_client = redis.Redis(
    host=db_host, port=6379, db=0, decode_responses=True
)

async def cache_search_results(query: str, results: List[Tuple[int, str, str, str]], ttl: int = 3600):
    """
    Кэшировать результаты поиска в Redis.
    """
    cache_key = f"search:{query.lower()}"
    try:
        await redis_client.setex(cache_key, ttl, json.dumps(results))
        logger.info(f"Результаты поиска для '{query}' закэшированы")
    except Exception as e:
        logger.error(f"Ошибка при кэшировании результатов для '{query}': {e}")

async def get_cached_search_results(query: str) -> List[Tuple[int, str, str, str]] | None:
    """
    Получить результаты поиска из кэша.
    """
    cache_key = f"search:{query.lower()}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Результаты поиска для '{query}' найдены в кэше")
            return json.loads(cached)
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении кэша для '{query}': {e}")
        return None

async def clear_cache():
    """
    Очистить кэш поиска.
    """
    try:
        keys = await redis_client.keys("search:*")
        if keys:
            await redis_client.delete(*keys)
            logger.info(f"Очищено {len(keys)} ключей кэша поиска")
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {e}")