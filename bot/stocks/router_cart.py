from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_production_task_id
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.stocks.dao import CartDAO

cart_router = Router()


@cart_router.message(F.text == '🛒 Корзина')
async def send_product_cart(message: Message):
    telegram_id = message.from_user.id

    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)
    total_price = 0

    if product_cart:
        messages_to_delete = []  # Список для хранения ID сообщений, которые нужно удалить позже
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

            total_price += price * quantity  # Учитываем количество товара
            formatted_price = f"{price:,.0f}".replace(',', ' ')

            message_text = (
                f"🔹 <b>{idx + 1}. Готовая продукция:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                f"📝 Описание: {comment or 'нет описания'}"
            )

            sent_message = await message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )
            messages_to_delete.append(sent_message.message_id)

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"Описание товаров в корзине:\n"
            f"Общее кол-во товаров: {total_quantity} шт.\n"
            f"Общая сумма заказа: {formatted_total_price} руб."
        )
        total_message = await message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
        messages_to_delete.append(total_message.message_id)

        # Можно сохранить messages_to_delete в контексте, если нужно удалять сообщения позже
    else:
        await message.answer("Корзина пуста.")


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

    # Удаляем старые сообщения (если есть способ их отслеживать) или просто отправляем новые
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

            await callback_query.message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"Описание товаров в корзине:\n"
            f"Общее кол-во товаров: {total_quantity} шт.\n"
            f"Общая сумма заказа: {formatted_total_price} руб."
        )
        await callback_query.message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
    else:
        await callback_query.message.answer("Корзина пуста.")
        

###############################################################################


@cart_router.callback_query(F.data.startswith('cart-product-delete'))
async def delete_product_cart(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    prod_cart_id = int(callback_query.data.split('_')[2])
    await callback_query.answer(f'product_id: {product_id}; prod_cart_id: {prod_cart_id}')
    await callback_query.message.delete()
    await CartDAO.delete(id=prod_cart_id)


@cart_router.callback_query(F.data.startswith('cart-product_[+]'))
async def plus_product_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    prod_cart_id = int(callback_query.data.split('_')[2])
    product_id = callback_query.data.split('_')[1]

    product = await CartDAO.find_one_or_none(id=prod_cart_id, telegram_id=telegram_id)
    if not product:
        await callback_query.answer("Товар не найден!", show_alert=True)
        return

    new_quantity = product.quantity + 1
    await CartDAO.update(filter_by={'id': prod_cart_id, 'telegram_id': telegram_id}, quantity=new_quantity)

    await callback_query.message.edit_text(
        f"{product.product_name} | Кол-во: {new_quantity} шт.",
        reply_markup=kb.cart_product_keyboard(
            product_id=product_id, prod_cart_id=product.id, quantity=new_quantity
        )
    )
    await callback_query.answer("Количество увеличено ✅")


@cart_router.callback_query(F.data.startswith('cart-product_[-]'))
async def minus_product_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    prod_cart_id = int(callback_query.data.split('_')[2])
    product_id = callback_query.data.split('_')[1]

    product = await CartDAO.find_one_or_none(id=prod_cart_id, telegram_id=telegram_id)
    if not product or product.quantity <= 1:
        await callback_query.answer("Нельзя уменьшить ниже 1!", show_alert=True)
        return

    new_quantity = product.quantity - 1
    await CartDAO.update(filter_by={'id': prod_cart_id, 'telegram_id': telegram_id}, quantity=new_quantity)

    await callback_query.message.edit_text(
        f"{product.product_name} | Кол-во: {new_quantity} шт.",
        reply_markup=kb.cart_product_keyboard(
            product_id=product_id, prod_cart_id=product.id, quantity=new_quantity
        )
    )
    await callback_query.answer("Количество уменьшено ✅")


