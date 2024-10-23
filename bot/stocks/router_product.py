from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO


product_router = Router()


################ PRODUCT CATALOG #######################

@product_router.message(F.text == '📋 Каталог товара')
async def stockbalance(message: Message):
    await message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())


@product_router.callback_query(F.data.startswith('device_select'))
async def handle_device_select(callback_query: CallbackQuery):
    await callback_query.message.answer('Пожалуйста, выберите тип устройства:', reply_markup=kb.device_keyboard())
    await callback_query.answer()


@product_router.callback_query(F.data.startswith('device_back'))
async def handle_device_back(callback_query: CallbackQuery):
    await callback_query.message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())
    await callback_query.answer()


@product_router.callback_query(F.data.startswith('device_'))
async def handle_device_choice(callback_query: types.CallbackQuery):
    # Извлекаем устройство из callback_data
    choice = callback_query.data.split('device_')[1]

    # Получаем данные о товарах
    product_data = await planfix_stock_balance()

    # Фильтрация данных по выбранному устройству
    filtered_data = [item for item in product_data if item[4] == choice]

    # Параметры для пагинации
    page = 1  # Начинаем с первой страницы
    page_size = 5  # Количество товаров на одной странице

    # Получаем данные для текущей страницы
    paginated_data = filtered_data[(page - 1) * page_size: page * page_size]

    if paginated_data:
        for idx, item in enumerate(paginated_data):
            message = f"{(page - 1) * page_size + idx + 1}. {item[1]} | Остаток: {item[2]} шт. | Цена: {item[3]} руб.\n"
            product_id = item[0]
            await callback_query.message.answer(
                message, reply_markup=kb.product_keyboard(product_id)
            )

        # Если есть больше товаров, добавляем кнопку "Ещё"
        if len(filtered_data) > page * page_size:
            total_idx = len(filtered_data)
            await callback_query.message.answer(
                f"Общее кол-во товаров: {total_idx} шт. Нажмите 'Ещё' для просмотра следующих.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Ещё", callback_data=f"paginate_{page + 1}_{choice}")]
                ])
            )
    else:
        await callback_query.message.answer(f"Товары для {choice} не найдены.")

    await callback_query.answer()


# Обработка кнопки "Ещё"
@product_router.callback_query(F.data.startswith('paginate_'))
async def handle_pagination(callback_query: types.CallbackQuery):
    # Извлекаем номер страницы и устройство из callback_data
    _, page, choice = callback_query.data.split('_')
    page = int(page)

    # Получаем данные о товарах
    product_data = await planfix_stock_balance()

    # Фильтрация данных по устройству
    filtered_data = [item for item in product_data if item[4] == choice]

    # Параметры для пагинации
    page_size = 5  # Количество товаров на одной странице

    # Получаем данные для текущей страницы
    paginated_data = filtered_data[(page - 1) * page_size: page * page_size]

    if paginated_data:
        for idx, item in enumerate(paginated_data):
            message = f"{(page - 1) * page_size + idx + 1}. {item[1]} | Остаток: {item[2]} шт. | Цена: {item[3]} руб.\n"
            product_id = item[0]

            await callback_query.message.answer(
                message, reply_markup=kb.product_keyboard(product_id)
            )

        # Если есть ещё товары, добавляем кнопку "Ещё"
        if len(filtered_data) > page * page_size:
            total_idx = len(filtered_data)
            await callback_query.message.answer(
                f"Общее кол-во товаров: {total_idx} шт. Нажмите 'Ещё' для просмотра следующих.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Ещё", callback_data=f"paginate_{page + 1}_{choice}")]
                ])
            )
    else:
        await callback_query.message.answer("Товары закончились.")

    await callback_query.answer()


###################### КОРЗИНА ############################

@product_router.callback_query(F.data.startswith('product-cart_'))
async def add_product_cart(callback_query: types.CallbackQuery):

    product_id = callback_query.data.split('_')[1]
    telegram_id = callback_query.from_user.id

    product_cart = await CartDAO.find_one_or_none(product_id=product_id, telegram_id=telegram_id)

    if not product_cart:

        product_data = await planfix_stock_balance()
        product_name = next((item[1] for item in product_data if item[0] == int(
            product_id)), "Неизвестный товар")

        await CartDAO.add(
            telegram_id=telegram_id,
            product_id=product_id,
            product_name=product_name,
            quantity=1,
            price=1000
        )
        await callback_query.answer(f'Новый товар {product_name} добавлен в корзину.')
    else:
        prod_cart_id = product_cart.id
        prod_cart_name = product_cart.product_name
        prod_cart_quantity = int(product_cart.quantity)
        await CartDAO.update(filter_by={'id': prod_cart_id}, quantity=prod_cart_quantity + 1)
        await callback_query.answer(f'Количество товара {prod_cart_name} обновлено: {prod_cart_quantity + 1} шт.')
    await callback_query.answer()


###################### КАТАЛОГ: БРЕНД ############################

@product_router.callback_query(F.data.startswith('brand_select'))
async def handle_brand_select(callback_query: CallbackQuery):
    await callback_query.message.answer('Пожалуйста, выберите бренд:', reply_markup=kb.brand_keyboard())
    await callback_query.answer(' ')


@product_router.callback_query(F.data.startswith('brand_back'))
async def handle_brand_back(callback_query: CallbackQuery):
    await callback_query.message.answer('Необходимо выбрать группировку товара', reply_markup=kb.device_brand_keyboard())
    await callback_query.answer(' ')
