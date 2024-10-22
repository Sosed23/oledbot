from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.stocks.dao import CartDAO

cart_router = Router()


async def get_cart_content(telegram_id: int, page: int, page_size: int):
    product_cart = await CartDAO.paginate(page=page, page_size=page_size, telegram_id=telegram_id)
    total_quantity = sum(product.quantity for product in await CartDAO.find_all(telegram_id=telegram_id))
    return product_cart, total_quantity


async def send_cart_page(message: Message, telegram_id: int, page: int, page_size: int):
    product_cart, total_quantity = await get_cart_content(telegram_id, page, page_size)

    if product_cart:

        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            name = product.product_name
            quantity = product.quantity
            await message.answer(
                f'{(page - 1) * page_size + idx + 1}. {name} | Кол-во: {quantity} шт.',
                reply_markup=kb.cart_product_keyboard(
                    product_id=product_id, prod_cart_id=prod_cart_id, quantity=quantity)
            )

        # Создаем список кнопок для пагинации
        pagination_buttons = []

        # Кнопка "Назад", если это не первая страница
        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"cart_page:{page - 1}"
            ))

        # Кнопка "Вперед", если есть больше товаров
        if len(product_cart) == page_size:
            pagination_buttons.append(InlineKeyboardButton(
                text="Вперед ➡️",
                callback_data=f"cart_page:{page + 1}"
            ))

        # Создаем InlineKeyboardMarkup с кнопками
        pagination_markup = InlineKeyboardMarkup(
            inline_keyboard=[pagination_buttons])

        # Отправляем клавиатуру пагинации
        if pagination_buttons:
            cart_text = f"Описание товаров в корзине:\nОбщее кол-во товаров: {total_quantity} шт."
            await message.answer(f"{cart_text}", reply_markup=pagination_markup)
    else:
        await message.answer("Корзина пуста.")


@cart_router.message(F.text == '🛒 Корзина')
async def get_cart(message: Message):
    telegram_id = message.from_user.id
    page_size = 3
    await send_cart_page(message, telegram_id, page=1, page_size=page_size)


@cart_router.callback_query(F.data.startswith('cart_page:'))
async def paginate_cart(callback_query: CallbackQuery):
    page = int(callback_query.data.split(':')[1])
    telegram_id = callback_query.from_user.id
    page_size = 3

    # Удаляем предыдущие сообщения
    await callback_query.message.delete()

    # Отправляем новую страницу корзины
    await send_cart_page(callback_query.message, telegram_id, page, page_size)

    await callback_query.answer()


@cart_router.callback_query(F.data.startswith('cart-product-delete'))
async def delete_product_cart(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    prod_cart_id = callback_query.data.split('_')[2]
    await callback_query.answer(f'product_id: {product_id}; prod_cart_id: {prod_cart_id}')
    await callback_query.message.delete()
    await CartDAO.delete(id=prod_cart_id)


@cart_router.callback_query(F.data.startswith('cart-product_[+]'))
async def plus_product_cart(callback_query: types.CallbackQuery):
    prod_cart_id = callback_query.data.split('_')[2]
    quantity = callback_query.data.split('_')[3]
    await CartDAO.update(filter_by={'id': prod_cart_id}, quantity=int(quantity) + 1)
