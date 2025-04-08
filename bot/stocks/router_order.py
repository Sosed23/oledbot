from aiogram import Router, F, types

from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance, planfix_create_order, planfix_create_prodaction
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.users.keyboards import markup_kb
from bot.stocks.dao import CartDAO, OrderDAO, OrderItemDAO, OrderStatusHistoryDAO
from bot.users.dao import UserDAO
from bot.stocks.models_order import OrderStatus
import re
from loguru import logger
from sqlalchemy import inspect
from bot.database import async_session_maker
from bot.operations import OPERATION_NAMES

order_router = Router()


@order_router.message(F.text == '🗂 Мои заказы')
async def send_orders(message: Message):
    telegram_id = message.from_user.id

    try:
        my_orders = await OrderDAO.find_all(telegram_id=telegram_id)
 
        if not my_orders:
            await message.answer("У вас нет заказов.")
            return

        logger.info(f"Получено {len(my_orders)} заказов для telegram_id={telegram_id}")

        for order in my_orders:
            status_history = await OrderStatusHistoryDAO.find_all(order_id=order.id)
            if status_history:
                last_status = sorted(status_history, key=lambda x: x.timestamp, reverse=True)[0].status
            else:
                last_status = "Неизвестно"

            order_total_amount = order.total_amount
            order_items = order.items

            grouped_items = {}
            for item in order_items:
                operation_id = int(item.operation) if isinstance(item.operation, (int, str)) and str(item.operation).isdigit() else item.operation
                operation_name = OPERATION_NAMES.get(operation_id, f"Операция {operation_id}")
                if operation_name not in grouped_items:
                    grouped_items[operation_name] = []
                grouped_items[operation_name].append(f"   🔹 {item.product_name} 💰 Цена: {item.price} руб.")

            items_text = "\n".join([
                f"📌 <b>{operation}:</b>\n" + "\n".join(items)
                for operation, items in grouped_items.items()
            ]) if order_items else "Товары отсутствуют."

            message_text = (
                f"🏷️ Заказ #{order.id}\n"
                f"ℹ️ Статус: {last_status}\n"
                f"💵 Общая сумма: {order_total_amount} руб.\n"
                f"📝 Состав заказа:\n{items_text}"
            )

            await message.answer(message_text)

    except Exception as e:
        logger.error(f"Ошибка при получении заказов для telegram_id={telegram_id}: {e}")
        await message.answer("Произошла ошибка при получении заказов. Попробуйте снова.")


############################# ОФОРМИТЬ ЗАКАЗ (NEW) #################################


# Определяем состояния FSM
class OrderStates(StatesGroup):
    waiting_for_phone = State()  # Состояние ожидания номера телефона
    confirm_phone = State()      # Состояние подтверждения номера телефона

# Вспомогательная функция для создания заказа и синхронизации с Планфиксом
async def create_order_and_sync_with_planfix(telegram_id: int, phone_number: str, message_obj, state: FSMContext):
    try:
        # Получаем items корзины
        cart_items = await CartDAO.find_all(telegram_id=telegram_id)
        if not cart_items:
            await message_obj.answer(
                "Ваша корзина пуста!",
                reply_markup=markup_kb.back_keyboard()
            )
            await state.clear()
            return

        # Создаем заказ и получаем только его id
        order_id = await OrderDAO.add(
            telegram_id=telegram_id,
            total_amount=0
        )

        # Добавляем items заказа и сохраняем их идентификаторы
        total_amount = 0
        order_item_ids = []  # Список для хранения id добавленных OrderItem
        for cart_item in cart_items:
            order_item_id = await OrderItemDAO.add(
                order_id=order_id,
                product_id=cart_item.product_id,
                product_name=cart_item.product_name,
                quantity=cart_item.quantity,
                price=cart_item.price,
                task_id=cart_item.task_id,
                operation=cart_item.operation
            )
            order_item_ids.append(order_item_id)  # Сохраняем уникальный id элемента
            total_amount += cart_item.price * cart_item.quantity

        # Обновляем общую сумму заказа
        await OrderDAO.update(
            {"id": order_id},
            total_amount=total_amount
        )

        # Добавляем начальный статус
        status_record = await OrderStatusHistoryDAO.add(
            order_id=order_id,
            status=OrderStatus.PENDING.value,
            comment="Order created"
        )
        status = status_record["status"]

        # Получаем данные о заказе и его элементах
        order = await OrderDAO.find_one_or_none(id=order_id)
        order_items = await OrderItemDAO.find_all(order_id=order_id)

        # Очищаем корзину
        await CartDAO.delete(telegram_id=telegram_id, delete_all=True)
        logger.info("Корзина очищена")

        # Группируем элементы заказа по операциям
        grouped_items = {}
        for item in order_items:
            operation_id = int(item.operation) if isinstance(item.operation, (int, str)) and str(item.operation).isdigit() else item.operation
            operation_name = OPERATION_NAMES.get(operation_id, f"Операция {operation_id}")
            if operation_name not in grouped_items:
                grouped_items[operation_name] = []
            grouped_items[operation_name].append(f"   🔹 {item.product_name} 💰 Цена: {item.price} руб.")

        # Формируем текст элементов заказа
        items_text = "\n".join([
            f"📌 <b>{operation}:</b>\n" + "\n".join(items)
            for operation, items in grouped_items.items()
        ]) if order_items else "Товары отсутствуют."

        # Формируем description для Планфикса
        description = (
            f"🏷️ Заказ #{order_id}\n"
            f"ℹ️ Статус: {status}\n"
            f"💵 Общая сумма: {total_amount} руб.\n"
            f"📝 Состав заказа:\n{items_text}\n"
            f"📞 Номер телефона: {phone_number}"
        )

        # Формируем сообщение для пользователя с составом заказа
        message_text = (
            f"🏷️ Заказ #{order_id} успешно создан!\n"
            f"ℹ️ Статус: {status}\n"
            f"💵 Сумма заказа: {total_amount} руб.\n"
            f"📞 Номер телефона: {phone_number}\n"
            f"📝 Состав заказа:\n{items_text}"
        )
        logger.info(f"Отправка сообщения пользователю: {message_text}")
        await message_obj.answer(
            message_text,
            reply_markup=markup_kb.back_keyboard()
        )
        logger.info("Сообщение успешно отправлено пользователю")

        # Интеграция с Планфиксом
        logger.info("Начало интеграции с Планфиксом")

        data_order = await planfix_create_order(description=description, order_id=order_id)
        order_pf_id = data_order['id']
        logger.info(f"Создан заказ в Планфиксе: {order_pf_id}")
        await message_obj.answer(f"Заказ в Планфиксе создан: {order_pf_id}")

        await OrderDAO.update(
            {"id": order_id},
            order_pf_id=order_pf_id
        )
        logger.info(f"Заказ #{order_id} обновлён с order_pf_id={order_pf_id}")

        # Добавляем продукцию в Планфикс с уникальным prodaction_id
        for idx, cart_item in enumerate(cart_items):
            prodaction_pf_id = cart_item.task_id
            prodaction_id = order_item_ids[idx]  # Уникальный id из OrderItem
            price = cart_item.price
            data_prodaction = await planfix_create_prodaction(
                order_pf_id=order_pf_id,
                prodaction_pf_id=prodaction_pf_id,
                price=price,
                prodaction_id=prodaction_id
            )
            logger.info(f"Продукция добавлена в Планфикс: {data_prodaction}")
            await message_obj.answer(f"Продукция добавлена в Планфикс: {data_prodaction}")

    except Exception as e:
        logger.error(f"Ошибка при создании заказа или интеграции с Планфиксом для telegram_id={telegram_id}: {e}")
        await message_obj.answer(
            "Произошла ошибка при создании заказа или синхронизации с Планфиксом. Пожалуйста, попробуйте снова.",
            reply_markup=markup_kb.back_keyboard()
        )
        await state.clear()
        return

    # Сбрасываем состояние после успешной обработки
    logger.info("Сброс состояния FSM")
    await state.clear()


# Обработчик нажатия на "Оформить заказ"
@order_router.callback_query(F.data.startswith('place_order'))
async def request_phone_before_order(callback_query: types.CallbackQuery, state: FSMContext):
    telegram_id = callback_query.from_user.id

    # Проверяем, есть ли товары в корзине
    cart_items = await CartDAO.find_all(telegram_id=telegram_id)
    if not cart_items:
        await callback_query.message.answer(
            "Ваша корзина пуста!",
            reply_markup=markup_kb.back_keyboard()
        )
        return

    # Проверяем, есть ли номер телефона в базе данных
    user_info = await UserDAO.find_one_or_none(telegram_id=telegram_id)
    if user_info and user_info.phone_number:
        # Если номер телефона есть, спрашиваем пользователя, подтверждает ли он его использование
        phone_number = user_info.phone_number
        await state.update_data(phone_number=phone_number)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="confirm_phone_yes"),
                InlineKeyboardButton(text="Нет", callback_data="confirm_phone_no")
            ]
        ])
        await callback_query.message.answer(
            f"Мы нашли ваш номер телефона: {phone_number}. Использовать его для оформления заказа?",
            reply_markup=keyboard
        )
        logger.info(f"Установлено состояние OrderStates.confirm_phone для telegram_id={telegram_id}")
        await state.set_state(OrderStates.confirm_phone)
    else:
        # Если номера телефона нет, просим ввести его вручную
        await callback_query.message.answer(
            "Для оформления заказа нам нужен ваш номер телефона. Пожалуйста, введите его в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
        )
        logger.info(f"Установлено состояние OrderStates.waiting_for_phone для telegram_id={telegram_id}")
        await state.set_state(OrderStates.waiting_for_phone)

    await callback_query.answer()

# Обработчик подтверждения номера телефона
@order_router.callback_query(F.data.startswith('confirm_phone'), OrderStates.confirm_phone)
async def process_phone_confirmation(callback_query: types.CallbackQuery, state: FSMContext):
    logger.info(f"Вызван process_phone_confirmation для callback_data={callback_query.data}")
    confirmation = callback_query.data.split('_')[-1]  # "yes" или "no"

    if confirmation == "yes":
        # Если пользователь подтвердил номер, продолжаем оформление заказа
        data = await state.get_data()
        phone_number = data.get("phone_number")
        telegram_id = callback_query.from_user.id

        # Вызываем общую функцию для создания заказа и интеграции с Планфиксом
        await create_order_and_sync_with_planfix(
            telegram_id=telegram_id,
            phone_number=phone_number,
            message_obj=callback_query.message,
            state=state
        )

    elif confirmation == "no":
        # Если пользователь отказался от номера, просим ввести новый
        await callback_query.message.answer(
            "Пожалуйста, введите новый номер телефона в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
        )
        await state.set_state(OrderStates.waiting_for_phone)

    await callback_query.answer()

# Обработчик получения текстового сообщения с номером телефона
@order_router.message(OrderStates.waiting_for_phone)
async def process_manual_phone_input(message: types.Message, state: FSMContext):
    phone_number = message.text.strip()

    # Проверяем формат номера телефона с помощью регулярного выражения
    phone_pattern = r'^(\+7|8)\d{10}$'  # Формат: +7XXXXXXXXXX или 8XXXXXXXXXX
    if not re.match(phone_pattern, phone_number):
        await message.answer(
            "Некорректный формат номера телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX:"
        )
        return

    telegram_id = message.from_user.id

    try:
        # Проверяем, есть ли пользователь в базе
        user_info = await UserDAO.find_one_or_none(telegram_id=telegram_id)

        if user_info:
            await UserDAO.update(
                {"telegram_id": telegram_id},
                phone_number=phone_number
            )
        else:
            await UserDAO.add(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                phone_number=phone_number
            )

        # Вызываем общую функцию для создания заказа и интеграции с Планфиксом
        await create_order_and_sync_with_planfix(
            telegram_id=telegram_id,
            phone_number=phone_number,
            message_obj=message,
            state=state
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке номера телефона для telegram_id={telegram_id}: {e}")
        await message.answer(
            "Произошла ошибка при обработке номера телефона. Пожалуйста, попробуйте снова.",
            reply_markup=markup_kb.back_keyboard()
        )
        await state.clear()


############################# ОФОРМИТЬ ЗАКАЗ (OLD) #################################


# @order_router.callback_query(F.data.startswith('place_order'))

# async def create_order_from_cart(callback_query: CallbackQuery):
#     telegram_id = callback_query.from_user.id

#     async with async_session_maker() as session:

#         # Получаем items корзины
#         cart_items = await CartDAO.find_all(telegram_id=telegram_id)
#         if not cart_items:
#             await callback_query.message.answer("Ваша корзина пуста!")
#             return

#         # Создаем заказ
#         order = await OrderDAO.add(
#             session=session,
#             telegram_id=telegram_id,
#             total_amount=0  # Обновим позже
#         )

#         # Добавляем items заказа
#         total_amount = 0
#         for cart_item in cart_items:
#             order_item = await OrderItemDAO.add(
#                 session=session,
#                 order_id=order.id,
#                 product_id=cart_item.product_id,
#                 product_name=cart_item.product_name,
#                 quantity=cart_item.quantity,
#                 price=cart_item.price
#             )
#             total_amount += cart_item.price * cart_item.quantity

#         # Обновляем общую сумму заказа
#         order.total_amount = total_amount

#         # Добавляем начальный статус
#         status_record = await OrderStatusHistoryDAO.add(
#             session=session,
#             order_id=order.id,  # Добавляем order_id
#             status=OrderStatus.PENDING.value,
#             comment="Order created"
#         )

#         # # Сохраняем все изменения (commit транзакции)
#         # await session.commit()

#         await callback_query.answer('Заказ сформирован')

#         # Формируем сообщение о создании заказа
#         message_text = (
#             f"Заказ #{order.id} успешно создан!\n"
#             f"Сумма заказа: {order.total_amount} руб.\n"
#             f"Статус: {status_record.status}"
#         )
#         await callback_query.message.answer(message_text)

#         # Сохраняем все изменения (commit транзакции)
#         await session.commit()

#     # Очищаем корзину
#     await CartDAO.delete(telegram_id=telegram_id, delete_all=True)


# ############################# ОЧИСТИТЬ КОРЗИНУ #################################


# @order_router.callback_query(F.data.startswith('clear_cart'))
# async def clear_cart(callback_query: CallbackQuery):
#     telegram_id = callback_query.from_user.id
#     await CartDAO.delete(telegram_id=telegram_id, delete_all=True)
#     await callback_query.answer('Корзина очищена.')
