from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.ai_agent import ai_agent_n8n
from bot.planfix import planfix_stock_balance_filter, planfix_all_production_filter
from bot.planfix import planfix_production_task_id
from bot.users.keyboards import inline_kb as kb
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO
import json
from loguru import logger


aiagent_router = Router()


################ AI AGENT #######################

class SearchModelState(StatesGroup):
    waiting_for_model = State()

@aiagent_router.message(F.text == '✨ Поиск с ИИ')
async def search_aiagent(message: Message, state: FSMContext):
    await message.answer('Вас приветствует ✨ Ассистент OLED ✨.\nУкажите интересующую вас модель бренда Samsung или Apple.')
    await state.set_state(SearchModelState.waiting_for_model)

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
        
        await message.answer(f'Вы выбрали модель: {model_name} и {json_string} 📱', reply_markup=in_kb.search_aiagent_keyboard())
        await state.update_data(model_name=model_name, model_id=model_id)
    else:
        await message.answer("Данная модель отсутствует в каталоге.\nПожалуйста, введите другую модель.")


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
    await callback.message.answer(
        f"Вы выбрали опцию 'Цена переклейки' для модели:\n{prices_text}", parse_mode="Markdown"
    )
    await callback.answer()


def extract_price_from_data(data_re_gluing):

    try:
        # Получаем список задач
        tasks = data_re_gluing.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Цена, RUB":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None


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
    await callback.message.answer(message)
    await callback.answer()


def extract_price_from_data(data):
    try:
        # Получаем список задач
        tasks = data.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Цена, RUB":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None


####################### ГОТОВАЯ ПРОДУКЦИЯ ###############################

@aiagent_router.callback_query(F.data == "search_aiagent_production")
async def handle_aiagent_production(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')
    operation = "4"
    
    data_production = await planfix_all_production_filter(model_id=model_id)
    
    if not data_production or "tasks" not in data_production:
        await callback.message.answer("Нет данных о продукции.")
        return
    
    for task in data_production["tasks"]:
        task_id = task["id"]
        model = "Неизвестно"
        price = "Не указана"
        description = "Описание отсутствует"
        
        for field in task.get("customFieldData", []):
            field_name = field["field"].get("name", "")
            if field_name == "Модель":
                model = field["value"].get("value", "Неизвестно")
            elif field_name == "Price":
                price = field.get("value", "Не указана")
            elif field_name == "Комментарии":
                description = field.get("value", "Описание отсутствует")
        
        message_text = (
            f"📌 Артикул: <b>{task_id}</b>\n"
            f"ℹ️ Модель: <b>{model}</b>\n"
            f"💰 Цена: <b>{price} руб.</b>\n"
            f"📝 Описание: {description}"
        )
        
        await callback.message.answer(message_text, reply_markup=in_kb.aiagent_cart_keyboard(
            model_id=model_id, model_name=model_name, operation=operation, task_id=task_id), parse_mode="HTML")
    
    await callback.answer()


def extract_price_from_data(data_production):

    try:
        # Получаем список задач
        tasks = data_production.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Цена, RUB":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None


def extract_balance_from_data(data_production):

    try:
        # Получаем список задач
        tasks = data_production.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Приход":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None


@aiagent_router.callback_query(F.data.startswith('aiagent-cart_'))
async def add_aiagent_cart(callback_query: types.CallbackQuery):
    try:
        model_id = int(callback_query.data.split('_')[1])
        model_name = callback_query.data.split('_')[2]
        operation = callback_query.data.split('_')[3]
        task_id = callback_query.data.split('_')[4]
        telegram_id = callback_query.from_user.id

        data_product = await planfix_production_task_id(task_id=task_id)
        custom_fields = data_product.get("task", {}).get("customFieldData", [])

        price = 0
        for field in custom_fields:
            field_id = field.get("field", {}).get("id")
            if field_id == 12126:  
                price = field.get("value") or 0

        await CartDAO.add(
            telegram_id=telegram_id,
            product_id=model_id,
            product_name=model_name,
            task_id=int(task_id),
            operation=operation,
            quantity=1,
            price=price
        )
        await callback_query.answer(f'Новый товар {model_name} добавлен в корзину.')
        await callback_query.message.delete()

    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину для telegram_id={telegram_id}: {e}")
        await callback_query.answer("Произошла ошибка при добавлении товара в корзину. Попробуйте снова.")


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
    await callback.message.answer(
        f"Вы выбрали опцию 'Запчасти'.\nМодели: {model_name}\n"
        f"{prices_balance}"
    )
    await callback.answer()


def extract_price_from_data(data_spare_parts):

    try:
        # Получаем список задач
        tasks = data_spare_parts.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Цена, RUB":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None


def extract_balance_from_data(data_spare_parts):

    try:
        # Получаем список задач
        tasks = data_spare_parts.get("tasks", [])
        for task in tasks:
            # Проверяем каждое поле customFieldData
            for field_data in task.get("customFieldData", []):
                field_name = field_data.get("field", {}).get("name", "")
                if field_name == "Приход":
                    # Возвращаем первое найденное значение цены
                    return field_data.get("stringValue") or str(field_data.get("value", ""))
    except Exception as e:
        # Логируем ошибки, если они возникают
        print(f"Ошибка при извлечении цены: {e}")
    return None