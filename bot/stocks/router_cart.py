from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.stocks.dao import CartDAO

cart_router = Router()


@cart_router.message(F.text == '🛒 Корзина')
async def send_product_cart(message: Message):
    telegram_id = message.from_user.id

    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)

    if product_cart:

        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            name = product.product_name
            quantity = product.quantity

            await message.answer(
                f'{idx + 1}. {name} | Кол-во: {quantity} шт.',
                reply_markup=kb.cart_product_keyboard(
                    product_id=product_id, prod_cart_id=prod_cart_id, quantity=quantity)
            )

        cart_text = f"Описание товаров в корзине:\nОбщее кол-во товаров: {total_quantity} шт."
        await message.answer(f"{cart_text}", reply_markup=kb.cart_order_keyboard())
    else:
        await message.answer("Корзина пуста.")


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