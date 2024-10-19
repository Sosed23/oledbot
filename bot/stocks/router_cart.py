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
async def get_cart(message: Message):
    telegram_id = message.from_user.id
    product_cart = await CartDAO.find_all(telegram_id=telegram_id)
    total_quantity = sum(product.quantity for product in product_cart)
    if product_cart:
        cart_text = f"Описание товаров в корзине:\nОбщее кол-во товаров: {total_quantity} шт.\n"
        for idx, product in enumerate(product_cart):
            product_id = product.product_id
            name = product.product_name
            quantity = product.quantity
            await message.answer(f'{idx + 1}. {name} | Кол-во: {quantity} шт.',
                                 reply_markup=kb.cart_product_keyboard(product_id=product_id))
        await message.answer(f'{cart_text}')
    else:
        await message.answer("Корзина пуста.")
