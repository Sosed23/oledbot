from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.ai_agent import ai_agent_n8n
from bot.planfix import planfix_stock_balance_filter, planfix_all_production_filter
# from bot.planfix import planfix_production_task_id, planfix_create_order, planfix_create_order_prodaction_4
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO, OrderDAO
import json
from loguru import logger

from bot.stocks.handlers_production import handle_production_common, add_to_cart
from bot.utils.planfix_utils import extract_price_from_data, extract_balance_from_data

aiagent_router = Router()

##################### AI AGENT #######################

class SearchModelState(StatesGroup):
    waiting_for_model = State()

@aiagent_router.message(F.text == '✨ Поиск с ИИ')
async def search_aiagent(message: Message, state: FSMContext):
    result = await message.answer('Вас приветствует ✨ Ассистент OLED ✨.\nУкажите интересующую вас модель бренда Samsung или Apple.')
    await state.set_state(SearchModelState.waiting_for_model)
    return result

@aiagent_router.message(SearchModelState.waiting_for_model)
async def receive_model(message: Message, state: FSMContext):
    model = message.text  # Сохраняем введённую модель
    await state.update_data(model=model)
    
    # Показываем, что бот печатает
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # Отправляем сообщение о начале поиска
    search_message = await message.answer("🔍 Идёт поиск...")
    
    # Здесь можно передать model в нужную функцию
    result = await ai_agent_n8n(query=model)
    # Шаг 1: Получить значение ключа 'output', которое является строкой JSON
    json_string = result['output']

    # Шаг 2: Преобразовать строку JSON в словарь
    parsed_data = json.loads(json_string)
    status = parsed_data['status']

    # Удаляем сообщение о поиске
    await search_message.delete()

    if status == "successfully":
        model_name = parsed_data['model_name']
        model_id = parsed_data['model_id']
        
        result = await message.answer(
            f'Вы выбрали модель: {model_name} и {json_string} 📱',
            reply_markup=in_kb.search_aiagent_keyboard()
        )
        await state.update_data(model_name=model_name, model_id=model_id)
        return result
    else:
        result = await message.answer("Данная модель отсутствует в каталоге.\nПожалуйста, введите другую модель.")
        return result

####################### ЦЕНА ПЕРЕКЛЕЙКИ ###############################

@aiagent_router.callback_query(F.data == "search_aiagent_re-gluing")
async def handle_re_gluing(callback: CallbackQuery, state: FSMContext):
    # Получаем сохраненные данные о состоянии
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')

    # Запрашиваем данные о переклейке
    data_re_gluing = await planfix_stock_balance_filter(model_id=model_id, operation="1")

    # Извлекаем единственную цену
    price = extract_price_from_data(data_re_gluing)

    # Формируем текст для вывода
    if price:
        prices_text = f"**{model_name}  Цена: {price} RUB**"
    else:
        prices_text = f"**{model_name}  Цена не найдена.**"

    # Отправляем сообщение
    result = await callback.message.answer(
        f"Вы выбрали опцию 'Цена переклейки' для модели:\n{prices_text}",
        parse_mode="Markdown"
    )
    await callback.answer()
    return result

####################### ПРОДАТЬ БИТИК ###############################

@aiagent_router.callback_query(F.data == "search_aiagent_crash-display")
async def handle_crash_display(callback: CallbackQuery, state: FSMContext):
    # Получаем сохраненные данные о состоянии
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')

    # Запрашиваем данные о переклейке
    data_crash_display_plus = await planfix_stock_balance_filter(model_id=model_id, operation="2")
    data_crash_display_minus = await planfix_stock_balance_filter(model_id=model_id, operation="3")

    # Извлекаем единственную цену
    price_plus = extract_price_from_data(data_crash_display_plus)
    price_minus = extract_price_from_data(data_crash_display_minus)

    # Формируем текст сообщения
    message = f"Вы выбрали опцию 'Продать битик' для модели: {model_name}\n"
    if price_plus and float(price_plus) > 0:
        message += f"Цена битика с оригинальной подсветкой/тачом: {price_plus} RUB\n"
    if price_minus and float(price_minus) > 0:
        message += f"Цена битика с поврежденной подсветкой/тачом: {price_minus} RUB\n"

    # Отправляем сообщение
    result = await callback.message.answer(message)
    await callback.answer()
    return result

####################### ГОТОВАЯ ПРОДУКЦИЯ ###############################

@aiagent_router.callback_query(F.data == "search_aiagent_production")
async def handle_aiagent_production(callback: CallbackQuery, state: FSMContext):
    return await handle_production_common(callback, state, operation="4")

####################### ДОБАВЛЕНИЕ В КОРЗИНУ ###############################

@aiagent_router.callback_query(F.data.startswith('aiagent-cart_'))
async def add_aiagent_cart(callback_query: types.CallbackQuery):
    return await add_to_cart(callback_query, prefix='aiagent-cart')

####################### ЗАПЧАСТИ ###############################

@aiagent_router.callback_query(F.data == "search_aiagent_spare-parts")
async def handle_spare_parts(callback: CallbackQuery, state: FSMContext):
    # Получаем сохраненные данные о состоянии
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')

    # Запрашиваем данные о переклейке
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
    result = await callback.message.answer(
        f"Вы выбрали опцию 'Запчасти'.\nМодели: {model_name}\n"
        f"{prices_balance}"
    )
    await callback.answer()
    return result