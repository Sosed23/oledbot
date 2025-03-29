from bot.dao.base import BaseDAO
from bot.stocks.models_cart import Cart
from bot.stocks.models_order import Order, OrderItem, OrderStatusHistory, OrderStatus
from bot.database import async_session_maker

from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class CartDAO(BaseDAO):
    model = Cart


class OrderDAO(BaseDAO):
    model = Order

    @classmethod
    async def find_all(cls, **filter_by):
        logger.info(f"Поиск всех заказов пользователя по фильтру: {filter_by}")
        async with async_session_maker() as session:
            try:
                # Используем selectinload для предзагрузки связанных товаров
                query = select(cls.model).options(
                    selectinload(cls.model.items)).filter_by(**filter_by)
                result = await session.execute(query)
                records = result.scalars().all()
                logger.info(f"Найдено {len(records)} заказов.")
                return records
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при поиске заказов: {e}")
                raise


class OrderItemDAO(BaseDAO):
    model = OrderItem


class OrderStatusHistoryDAO(BaseDAO):
    model = OrderStatusHistory

    @classmethod
    async def add(cls, **values):
        logger.info(f"Добавление новой записи в {cls.model.__name__}: {values}")
        async with async_session_maker() as session:
            async with session.begin():
                new_instance = cls.model(**values)
                session.add(new_instance)
                await session.flush()  # Убедимся, что status доступен после flush
                instance_status = new_instance.status  # Теперь status — это строка
                await session.commit()
                logger.info(f"Запись {cls.model.__name__} успешно добавлена.")
                return {"status": instance_status}

    @classmethod
    async def find_all(cls, **filter_by):
        logger.info(f"Поиск всех записей {cls.model.__name__} по фильтрам: {filter_by}")
        async with async_session_maker() as session:
            try:
                query = select(cls.model).filter_by(**filter_by)
                result = await session.execute(query)
                records = result.scalars().all()
                logger.info(f"Найдено {len(records)} записей.")
                return records
            except SQLAlchemyError as e:
                logger.error(f"Ошибка при поиске всех записей по фильтрам {filter_by}: {e}")
                raise