from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_production_task_id
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.stocks.dao import CartDAO
from bot.operations import OPERATION_NAMES

cart_router = Router()

@cart_router.message(F.text == '🛒 Корзина')
async def send_product_cart(message: Message):
    telegram_id = message.from_user.id

    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)
    total_price = 0
    messages = []  # Список для хранения всех отправленных сообщений

    if product_cart:
        messages_to_delete = []  # Список для хранения ID сообщений, которые нужно удалить позже
        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            task_id = product.task_id
            name = product.product_name
            quantity = product.quantity
            operation = product.operation

            # Приводим operation к целому числу, если это строка
            try:
                operation = int(operation)
            except (ValueError, TypeError):
                operation = 0  # Если не удалось преобразовать, задаём значение по умолчанию

            product_cart_data = await planfix_production_task_id(task_id=task_id)
            custom_fields = product_cart_data.get("task", {}).get("customFieldData", [])

            price = 0
            comment = ""
            for field in custom_fields:
                field_id = field.get("field", {}).get("id")
                if field_id == 12126:  # ID поля Price
                    price = field.get("value") or 0
                elif field_id == 5498:  # ID поля Комментарии
                    comment = field.get("value", "")

            total_price += price * quantity  # Учитываем количество товара
            formatted_price = f"{price:,.0f}".replace(',', ' ')

            await CartDAO.update(filter_by={"id": prod_cart_id}, price=price)

            name_operation = OPERATION_NAMES.get(operation, "Неизвестная операция")

            message_text = (
                f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                f"📝 Описание: {comment or 'нет описания'}"
            )

            sent_message = await message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )
            messages.append(sent_message)  # Добавляем сообщение о товаре в список
            messages_to_delete.append(sent_message.message_id)

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"📝 Описание товаров в корзине:\n"
            f"🔢 Общее кол-во товаров: {total_quantity} шт.\n"
            f"💵 Общая сумма заказа: {formatted_total_price} руб."
        )
        total_message = await message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
        messages.append(total_message)  # Добавляем итоговое сообщение в список
        messages_to_delete.append(total_message.message_id)

        # Возвращаем список всех сообщений
        return messages

    else:
        result = await message.answer("Корзина пуста.")
        return [result]

@cart_router.callback_query(F.data.startswith('cart-aiagent-product-delete'))
async def delete_product_aiagent_cart(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    prod_cart_id = int(callback_query.data.split('_')[2])

    # Удаляем товар из корзины
    await CartDAO.delete(id=prod_cart_id)

    # Подтверждаем удаление
    await callback_query.answer("Товар удалён из корзины.")

    # Пересчитываем и обновляем корзину
    telegram_id = callback_query.from_user.id
    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)
    total_price = 0
    messages = []  # Список для хранения отправленных сообщений

    if product_cart:
        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            task_id = product.task_id
            name = product.product_name
            quantity = product.quantity

            product_cart_data = await planfix_production_task_id(task_id=task_id)
            custom_fields = product_cart_data.get("task", {}).get("customFieldData", [])

            price = 0
            comment = ""
            for field in custom_fields:
                field_id = field.get("field", {}).get("id")
                if field_id == 12126:  # ID поля Price
                    price = field.get("value") or 0
                elif field_id == 5498:  # ID поля Комментарии
                    comment = field.get("value", "")

            total_price += price * quantity
            formatted_price = f"{price:,.0f}".replace(',', ' ')

            message_text = (
                f"🔹 <b>{idx + 1}. Готовая продукция:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                f"📝 Описание: {comment or 'нет описания'}"
            )

            sent_message = await callback_query.message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )
            messages.append(sent_message)

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"Описание товаров в корзине:\n"
            f"Общее кол-во товаров: {total_quantity} шт.\n"
            f"Общая сумма заказа: {formatted_total_price} руб."
        )
        total_message = await callback_query.message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
        messages.append(total_message)

        # Возвращаем список сообщений
        return messages
    else:
        result = await callback_query.message.answer("Корзина пуста.")
        return [result]

@cart_router.callback_query(F.data.startswith('clear_cart'))
async def clear_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    await CartDAO.delete(telegram_id=telegram_id, delete_all=True)
    await callback_query.answer('Корзина очищена.')
    # Отправляем сообщение пользователю
    result = await callback_query.message.answer("Корзина очищена.")
    return [result]