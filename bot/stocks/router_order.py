from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO, OrderDAO, OrderItemDAO, OrderStatusHistoryDAO
from bot.stocks.models_order import OrderStatus

from bot.database import async_session_maker


order_router = Router()


@order_router.callback_query(F.data.startswith('place_order'))
async def create_order_from_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id

    async with async_session_maker() as session:

        # Получаем items корзины
        cart_items = await CartDAO.find_all(telegram_id=telegram_id)
        if not cart_items:
            await callback_query.message.answer("Ваша корзина пуста!")
            return

        # Создаем заказ
        order = await OrderDAO.add(
            session=session,
            telegram_id=telegram_id,
            total_amount=0  # Обновим позже
        )

        # Добавляем items заказа
        total_amount = 0
        for cart_item in cart_items:
            order_item = await OrderItemDAO.add(
                session=session,
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.product_name,
                quantity=cart_item.quantity,
                price=cart_item.price
            )
            total_amount += cart_item.price * cart_item.quantity

        # Обновляем общую сумму заказа
        order.total_amount = total_amount

        # Добавляем начальный статус
        status_record = await OrderStatusHistoryDAO.add(
            session=session,
            order_id=order.id,  # Добавляем order_id
            status=OrderStatus.PENDING.value,
            comment="Order created"
        )

        # # Сохраняем все изменения (commit транзакции)
        # await session.commit()

        await callback_query.answer('Заказ сформирован')

        # Формируем сообщение о создании заказа
        message_text = (
            f"Заказ #{order.id} успешно создан!\n"
            f"Сумма заказа: {order.total_amount} руб.\n"
            f"Статус: {status_record.status}"
        )
        await callback_query.message.answer(message_text)

        # Сохраняем все изменения (commit транзакции)
        await session.commit()

    # Очищаем корзину
    await CartDAO.delete(telegram_id=telegram_id, delete_all=True)


@order_router.callback_query(F.data.startswith('clear_cart'))
async def clear_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    await CartDAO.delete(telegram_id=telegram_id, delete_all=True)
    await callback_query.answer('Корзина очищена.')
