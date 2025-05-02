from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from loguru import logger

from bot.planfix import planfix_stock_balance_filter, planfix_price_re_gluing, planfix_stock_balance, planfix_basic_nomenclature_re_gluing
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO, ModelDAO
from bot.utils.cache import get_cached_search_results, cache_search_results

from bot.operations import RE_GLUING_NAMES
from bot.config import pf_token, pf_url_rest

from bot.stocks.handlers_re_gluing import handle_re_gluing_common, add_re_gluing_cart
from bot.stocks.handlers_back_cover import handle_back_cover_common
from bot.stocks.handlers_production import handle_production_common, add_to_cart
from bot.stocks.handlers_crash_display import (
    handle_crash_display_common, 
    add_crash_display_search_ai_cart,
    CrashDisplayOrder,  # Импортируем класс состояний
    process_quantity,   # Импортируем обработчик количества
    process_photo       # Импортируем обработчик фото
)

from bot.utils.planfix_utils import extract_price_from_data, extract_balance_from_data

search_router = Router()

RESULTS_PER_PAGE = 50

################ INLINE SEARCH PRODUCT #######################

# Создаем кнопку, которая запускает инлайн-режим в текущем чате
inline_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Поиск модели",
                # Пустая строка запускает инлайн-режим в текущем чате
                switch_inline_query_current_chat=""
            )
        ]
    ]
)

@search_router.message(F.text == '🔍 Поиск модели')
async def send_search_button(message: Message):
    await message.answer("Нажмите на кнопку для поиска модели:", reply_markup=inline_button)
    await message.delete()

###################################################################

@search_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery, state: FSMContext):
    query_text = inline_query.query.strip()
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Поиск через ModelDAO
    if query_text == "":
        # Подгрузка всех моделей постранично
        models = await ModelDAO.search_models(query="", offset=offset, limit=RESULTS_PER_PAGE)
        logger.info(f"ModelDAO (пустой запрос): Найдено моделей: {len(models)}")
    else:
        # Полнотекстовый поиск с кэшированием
        models = await get_cached_search_results(query_text)
        if models is None:
            models = await ModelDAO.search_models(query=query_text, offset=offset, limit=RESULTS_PER_PAGE)
            if models:
                await cache_search_results(query_text, models)
        logger.info(f"ModelDAO (поиск): Найдено моделей: {len(models)}")

    if not models:
        await inline_query.answer(
            [], cache_time=1, switch_pm_text="Ничего не найдено", switch_pm_parameter="start"
        )
        return

    # Формат для ModelDAO (model_id_int, model_name, model_engineer, model_id)
    results = [
        InlineQueryResultArticle(
            id=str(offset + index),
            title=model_name or model_id or "Без названия",
            description=f"Инженер: {model_engineer or 'не указан'} | ID: {model_id or 'не указан'}",
            input_message_content=InputTextMessageContent(
                message_text=f"Модель: {model_name or 'не указана'}\n"
                             f"Инженер: {model_engineer or 'не указан'}\n"
                             f"ID: {model_id or 'не указан'}"
            )
        )
        for index, (model_id_int, model_name, model_engineer, model_id) in enumerate(models)
    ]

    # Сохраняем model_id в состояние FSM
    for _, model_name, _, model_id in models:
        if model_id:  # Сохраняем только если model_id не None
            await state.update_data({model_name or model_id: model_id})

    # Поддерживаем пагинацию
    next_offset = str(offset + RESULTS_PER_PAGE) if len(models) == RESULTS_PER_PAGE else ""

    await inline_query.answer(results, cache_time=1, next_offset=next_offset)

@search_router.message(F.text.contains("Модель:") & F.text.contains("Инженер:") & F.text.contains("ID:"))
async def process_selected_product(message: Message, state: FSMContext):
    # Извлекаем model_name, model_engineer и model_id из сообщения
    try:
        lines = message.text.split("\n")
        model_name = lines[0].split(": ")[1].strip()
        model_engineer = lines[1].split(": ")[1].strip()
        model_id = lines[2].split(": ")[1].strip()

        # Проверяем, что значения не "не указана"
        model_name = None if model_name == "не указана" else model_name
        model_engineer = None if model_engineer == "не указан" else model_engineer
        model_id = None if model_id == "не указан" else model_id

        if not model_id:
            await message.answer("Не удалось найти ID для выбранной модели.")
            return

        await message.answer(
            f"Выберете нужную опцию для модели: {model_name or model_id}",
            reply_markup=kb.search_keyboard()
        )

        await message.delete()

        # Сохраняем model_name и model_id в состояние FSM для дальнейшего использования
        await state.update_data(model_name=model_name, model_id=model_id)
    except IndexError:
        await message.answer("Не удалось обработать выбранную модель. Пожалуйста, попробуйте снова.")


####################### ЦЕНА ПЕРЕКЛЕЙКИ ###############################

@search_router.callback_query(F.data == "search_re-gluing")
async def handle_re_gluing(callback: CallbackQuery, state: FSMContext):
    return await handle_re_gluing_common(callback, state)

# ДОБАВЛЕНИЕ В КОРЗИНУ ПЕРЕКЛЕЙКУ

@search_router.callback_query(F.data.startswith('re-gluing-cart_'))
async def add_re_gluing_search_cart(callback_query: types.CallbackQuery):
    return await add_re_gluing_cart(callback_query, prefix='re-gluing-cart')


####################### ЗАМЕНА ЗАДНЕЙ КРЫШКИ ###############################

@search_router.callback_query(F.data == "search_back_cover")
async def handle_back_cover(callback: CallbackQuery, state: FSMContext):
    return await handle_back_cover_common(callback, state)


####################### ПРОДАТЬ БИТИК ###############################

@search_router.callback_query(F.data == "search_crash-display")
async def handle_crash_display(callback: CallbackQuery, state: FSMContext):
    return await handle_crash_display_common(callback, state)

# Оформление заказа: Продать битик

@search_router.callback_query(F.data.startswith('crash-display-cart_'))
async def add_crash_display_cart(callback_query: types.CallbackQuery, state: FSMContext):
    return await add_crash_display_search_ai_cart(callback_query, prefix='crash-display-cart', state=state)

# Обработчики для количества и фото
@search_router.message(CrashDisplayOrder.waiting_for_quantity)
async def process_quantity_handler(message: types.Message, state: FSMContext):
    return await process_quantity(message, state)

@search_router.message(CrashDisplayOrder.waiting_for_photo, F.photo)
async def process_photo_handler(message: types.Message, state: FSMContext):
    return await process_photo(message, state)

####################### ГОТОВАЯ ПРОДУКЦИЯ ###############################

@search_router.callback_query(F.data == "search_production")
async def handle_production(callback: CallbackQuery, state: FSMContext):
    return await handle_production_common(callback, state, operation="4")

# ДОБАВЛЕНИЕ В КОРЗИНУ ГОТОВОЙ ПРОДУКЦИИ

@search_router.callback_query(F.data.startswith('search-cart_'))
async def add_search_cart(callback_query: types.CallbackQuery):
    return await add_to_cart(callback_query, prefix='search-cart')

####################### ЗАПЧАСТИ ###############################

@search_router.callback_query(F.data == "search_spare-parts")
async def handle_spare_parts(callback: CallbackQuery, state: FSMContext):
    # Получаем сохраненные данные о состоянии
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')

    # Запрашиваем данные о запчастях
    data_spare_parts = await planfix_stock_balance_filter(model_id=model_id, operation="5")

    # Извлекаем единственную цену
    price = extract_price_from_data(data_spare_parts)
    balance = extract_balance_from_data(data_spare_parts)

    # Формируем текст для вывода
    if price:
        prices_balance = f"Цена: {price} RUB Остаток: {balance} шт."
    else:
        prices_balance = f"{model_name}  Цена не найдена."

    # Отправляем сообщение
    await callback.message.answer(
        f"Вы выбрали опцию 'Запчасти'.\nМодели: {model_name}\n"
        f"{prices_balance}"
    )
    await callback.answer()