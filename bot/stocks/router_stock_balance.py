from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance
from bot.users.keyboards import inline_kb as kb
from bot.stocks.dao import CartDAO

import urllib.parse

stock_router = Router()

# Количество результатов на одной странице
RESULTS_PER_PAGE = 50


################ PRODUCT CATALOG #######################

@stock_router.message(F.text == '📋 Каталог товара')
async def stockbalance(message: Message):
    await message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())


@stock_router.callback_query(F.data.startswith('device_select'))
async def handle_device_select(callback_query: CallbackQuery):
    await callback_query.message.answer('Пожалуйста, выберите тип устройства:', reply_markup=kb.device_keyboard())
    await callback_query.answer()


@stock_router.callback_query(F.data.startswith('device_back'))
async def handle_device_back(callback_query: CallbackQuery):
    await callback_query.message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())
    await callback_query.answer()


@stock_router.callback_query(F.data.startswith('device_'))
async def handle_device_choice(callback_query: types.CallbackQuery):

    choice = callback_query.data.split('device_')[1]

    product_data = await planfix_stock_balance()

    filtered_data = [item for item in product_data if item[4] == choice]

    if filtered_data:
        for item in filtered_data:

            message = f"✔️ {item[1]} | Остаток: {item[2]} шт. | Цена: {item[3]} руб.\n"
            await callback_query.message.answer(message, reply_markup=kb.product_keyboard(product_id=item[0]))
    else:
        await callback_query.message.answer(f"Товары для {choice} не найдены.")

    await callback_query.answer()


###################### КОРЗИНА ############################

@stock_router.callback_query(F.data.startswith('product-cart_'))
async def add_product_cart(callback_query: types.CallbackQuery):
    # Получаем product_id из callback_data
    product_id = callback_query.data.split('_')[1]

    user_id = callback_query.from_user.id

    # Получаем product_name из базы данных или другого источника
    product_data = await planfix_stock_balance()
    product_name = next((item[1] for item in product_data if item[0] == int(
        product_id)), "Неизвестный товар")

    # Добавляем товар в корзину
    await CartDAO.add(
        telegram_id=user_id,
        product_id=product_id,
        product_name=product_name,
        quantity=1,
    )

    # Подтверждение пользователю
    await callback_query.message.answer(f"Товар '{product_name}' (ID: {product_id}) добавлен в корзину.")
    await callback_query.answer()


###################### КАТАЛОГ: БРЕНД ############################

@stock_router.callback_query(F.data.startswith('brand_select'))
async def handle_brand_select(callback_query: CallbackQuery):
    await callback_query.message.answer('Пожалуйста, выберите бренд:', reply_markup=kb.brand_keyboard())
    await callback_query.answer(' ')


@stock_router.callback_query(F.data.startswith('brand_back'))
async def handle_brand_back(callback_query: CallbackQuery):
    await callback_query.message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())
    await callback_query.answer(' ')
