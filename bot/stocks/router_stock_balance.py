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


################ INLINE SEARCH PRODUCT #######################

@stock_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Получаем список товаров в зависимости от текста запроса
    if query_text == "":  # Если запрос пустой, показываем все товары
        products = await planfix_stock_balance()
    else:  # Если запрос содержит текст, ищем товары по имени
        products = await planfix_stock_balance(query_text)

    # Ограничиваем результаты текущей страницей
    page_products = products[offset:offset + RESULTS_PER_PAGE]

    # Преобразуем результаты в список InlineQueryResult
    results = [
        InlineQueryResultArticle(
            id=str(offset + index),
            title=f"{product_name} - {stock_balance}",
            input_message_content=InputTextMessageContent(
                message_text=f"{product_name}: {stock_balance} шт."
            ),
            description=f"Доступно на складе: {stock_balance} шт."
        )
        for index, (product_name, stock_balance) in enumerate(page_products)
    ]

    # Определяем, есть ли следующая страница
    next_offset = str(
        offset + RESULTS_PER_PAGE) if len(products) > offset + RESULTS_PER_PAGE else ""

    # Отправляем результаты в ответ на инлайн-запрос с учетом пагинации
    await inline_query.answer(results, cache_time=1, next_offset=next_offset)


######################### VERSION 1 ##############################

# Создаем кнопку, которая запускает инлайн-режим в текущем чате
inline_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Поиск товара",
                # Пустая строка запускает инлайн-режим в текущем чате
                switch_inline_query_current_chat=""
            )
        ]
    ]
)

# Отправляем сообщение с кнопкой


@stock_router.message(F.text == '📋 Поиск товара')
async def send_search_button(message: Message):
    await message.answer("Нажмите на кнопку для поиска товара:", reply_markup=inline_button)


######################### VERSION 2 ##############################

# Создаем FSM с состояниями
class OrderState(StatesGroup):
    waiting_for_quantity = State()


@stock_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    # Здесь вы получите список товаров (это упрощенный пример)
    products = await planfix_stock_balance(query_text)

    # Преобразуем результаты в список InlineQueryResult
    results = [
        InlineQueryResultArticle(
            id=str(index),
            title=f"{product_name} - {stock_balance}",
            input_message_content=InputTextMessageContent(
                message_text=f"Товар: {product_name}\nОстаток: {stock_balance} шт.\nID товара: {product_id}"
            ),
            description=f"Доступно: {stock_balance} шт."
        )
        for index, (product_name, stock_balance, product_id) in enumerate(products)
    ]

    await inline_query.answer(results, cache_time=1)


# Этот хэндлер срабатывает, когда пользователь выбирает товар из инлайн-запроса
@stock_router.message(F.text.contains("шт.") & F.text.contains(":"))
async def process_selected_product(message: Message, state: FSMContext):
    # Извлекаем данные о товаре из сообщения
    try:
        product_info = message.text.split("\n")
        product_name = product_info[0].split(": ")[1].strip()
        product_id = "не указан"  # Убедитесь, что у вас есть информация о product_id

        # Переходим к следующему шагу с помощью FSM
        await message.answer(f"Вы выбрали {product_name}. Сколько единиц хотите заказать?")
        await state.set_state(OrderState.waiting_for_quantity)
        # Сохраняем ID товара в состоянии FSM для дальнейшего использования
        await state.update_data(product_id=product_id)
    except IndexError:
        await message.answer("Не удалось обработать выбранный товар. Пожалуйста, попробуйте снова.")


# Обработка ввода количества
@stock_router.message(OrderState.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    user_data = await state.get_data()
    product_id = user_data['product_id']

    # Проверяем, что пользователь ввел корректное число
    if not message.text.isdigit():
        await message.answer("Пожалуйста, введите корректное количество.")
        return

    quantity = int(message.text)

    # Здесь можно выполнять действия с товаром, например, отправить заказ
    await message.answer(f"Заказ на {quantity} единиц товара с ID {product_id} принят!")

    # Сбрасываем состояние
    await state.clear()
