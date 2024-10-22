from bot.dao.base import BaseDAO
from bot.stocks.models import Cart
from bot.database import async_session_maker

from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class CartDAO(BaseDAO):
    model = Cart  # Предполагается, что у вас есть модель Cart

    @classmethod
    async def increment_quantity(cls, telegram_id: int, product_id: int):
        logger.info(
            f"Увеличение количества товара {product_id} в корзине пользователя {telegram_id}")
        async with async_session_maker() as session:
            async with session.begin():
                try:
                    stmt = (
                        sqlalchemy_update(cls.model)
                        .where((cls.model.telegram_id == telegram_id) & (cls.model.product_id == product_id))
                        .values(quantity=cls.model.quantity + 1)
                    )
                    result = await session.execute(stmt)
                    await session.commit()
                    logger.info(
                        f"Количество товара {product_id} увеличено для пользователя {telegram_id}")
                    return result.rowcount
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(
                        f"Ошибка при увеличении количества товара: {e}")
                    raise

    @classmethod
    async def decrement_quantity(cls, telegram_id: int, product_id: int):
        logger.info(
            f"Уменьшение количества товара {product_id} в корзине пользователя {telegram_id}")
        async with async_session_maker() as session:
            async with session.begin():
                try:
                    # Сначала получаем текущее количество
                    query = select(cls.model.quantity).where(
                        (cls.model.telegram_id == telegram_id) & (
                            cls.model.product_id == product_id)
                    )
                    result = await session.execute(query)
                    current_quantity = result.scalar_one_or_none()

                    if current_quantity is None or current_quantity <= 1:
                        # Если количество 1 или меньше, удаляем товар из корзины
                        return await cls.remove_from_cart(telegram_id, product_id)
                    else:
                        # Иначе уменьшаем количество на 1
                        stmt = (
                            sqlalchemy_update(cls.model)
                            .where((cls.model.telegram_id == telegram_id) & (cls.model.product_id == product_id))
                            .values(quantity=cls.model.quantity - 1)
                        )
                        result = await session.execute(stmt)
                        await session.commit()
                        logger.info(
                            f"Количество товара {product_id} уменьшено для пользователя {telegram_id}")
                        return result.rowcount
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(
                        f"Ошибка при уменьшении количества товара: {e}")
                    raise

    @classmethod
    async def remove_from_cart(cls, telegram_id: int, product_id: int):
        logger.info(
            f"Удаление товара {product_id} из корзины пользователя {telegram_id}")
        async with async_session_maker() as session:
            async with session.begin():
                try:
                    stmt = (
                        sqlalchemy_update(cls.model)
                        .where((cls.model.telegram_id == telegram_id) & (cls.model.product_id == product_id))
                    )
                    result = await session.execute(stmt)
                    await session.commit()
                    logger.info(
                        f"Товар {product_id} удален из корзины пользователя {telegram_id}")
                    return result.rowcount
                except SQLAlchemyError as e:
                    await session.rollback()
                    logger.error(f"Ошибка при удалении товара из корзины: {e}")
                    raise
