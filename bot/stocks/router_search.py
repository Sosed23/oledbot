from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.planfix import planfix_stock_balance_filter, planfix_all_production_filter
from bot.users.keyboards import inline_kb as kb
from bot.stocks.dao import CartDAO
import requests

from bot.config import pf_token, pf_url_rest

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

    # Если поиск пустой — загружаем постранично
    if query_text == "":
        models = await planfix_stock_balance_models(offset=offset, limit=RESULTS_PER_PAGE)
    else:
        # Если пользователь ищет модель — загружаем все модели без оффсета
        models = await planfix_stock_balance_models(search_query=query_text)

    print(f"🔍 Найдено моделей: {len(models)}")  # Логируем количество найденных моделей
    for m in models[:5]:  # Логируем первые 5 моделей для проверки
        print(m)

    results = []
    for index, (model_id, model_name) in enumerate(models):
        if not model_name:  # Проверяем, есть ли название
            print(f"⚠️ Пропущена модель с ID {model_id} из-за пустого названия!")
            continue

        results.append(
            InlineQueryResultArticle(
                id=str(offset + index),
                title=model_name,  # Telegram требует, чтобы title был НЕ пустым
                input_message_content=InputTextMessageContent(
                    message_text=f"Выберете нужную услугу для модели: {model_name}"
                )
            )
        )
        # Сохраняем model_id в состояние FSM
        await state.update_data({model_name: model_id})

    # Если поиск пустой, поддерживаем пагинацию
    next_offset = str(offset + RESULTS_PER_PAGE) if query_text == "" and len(models) == RESULTS_PER_PAGE else ""

    if not results:
        await inline_query.answer([], cache_time=1, switch_pm_text="Ничего не найдено", switch_pm_parameter="start")
        return

    await inline_query.answer(results, cache_time=1, next_offset=next_offset)



####################### STOCK BALANCE (MODELS) ####################################

async def planfix_stock_balance_models(search_query=None, offset=0, limit=RESULTS_PER_PAGE):
    url = f"{pf_url_rest}/task/list"

    payload = {
        "offset": offset,
        "pageSize": limit,
        "filterId": "49864",
        "fields": "id,5556,5542,6640,6282,12140"
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {pf_token}"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    all_models = data.get('tasks', [])
    result = []

    for task in all_models:
        for custom_field in task.get('customFieldData', []):
            if custom_field['field']['name'] == 'Модель':
                model_id = custom_field['value']['id']
                model_name = custom_field['value']['value']

                if search_query and search_query.lower() not in model_name.lower():
                    continue

                result.append((model_id, model_name))

    return result




@search_router.message(F.text.contains("Выберете нужную услугу для модели:"))
async def process_selected_product(message: Message, state: FSMContext):
    # Извлекаем model_name из сообщения
    model_name = message.text.split(": ")[1].strip()

    # Извлекаем model_id из состояния FSM
    state_data = await state.get_data()
    model_id = state_data.get(model_name)

    if model_id is None:
        await message.answer("Не удалось найти ID для выбранной модели.")
        return

    await message.answer(
        f"Выберете нужную опцию для модели: {model_name}",
        reply_markup=kb.search_keyboard()
    )

    await message.delete()

    # Сохраняем model_name и model_id в состояние FSM для дальнейшего использования
    await state.update_data(model_name=model_name, model_id=model_id)


####################### ЦЕНА ПЕРЕКЛЕЙКИ ###############################


@search_router.callback_query(F.data == "search_re-gluing")
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


@search_router.callback_query(F.data == "search_crash-display")
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


@search_router.callback_query(F.data == "search_production")
async def handle_production(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')
    operation = "4"
    
    data_production = await planfix_all_production_filter(model_id=model_id)
    
    if not data_production or "tasks" not in data_production:
        await callback.message.answer("Нет данных о продукции.")
        return
    
    for task in data_production["tasks"]:
        production_id = task["id"]
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
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_to_cart:{production_id}")]
            ]
        )
        
        message_text = (
            f"📌 <b>{model}</b>\n"
            f"💰 Цена: {price} руб.\n"
            f"ℹ️ {description}"
        )
        
        await callback.message.answer(message_text, reply_markup=keyboard, parse_mode="HTML")
    
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


####################### ЗАПЧАСТИ ###############################


@search_router.callback_query(F.data == "search_spare-parts")
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


############## ЗАМОРОЗКА ##################

# # Этот хэндлер срабатывает, когда пользователь выбирает товар из инлайн-запроса
# @search_router.message(F.text.contains("шт.") & F.text.contains("Доступно на складе:"))
# async def process_selected_product(message: Message, state: FSMContext):
#     # Извлекаем данные о товаре из сообщения
#     try:
#         product_info = message.text.split("\n")
#         product_name = product_info[0].split(": ")[1].strip()
#         product_id = "не указан"  # Убедитесь, что у вас есть информация о product_id

#         # Переходим к следующему шагу с помощью FSM
#         await message.answer(f"Вы выбрали {product_name}. Сколько единиц хотите заказать?")
#         await state.set_state(OrderState.waiting_for_quantity)
#         # Сохраняем ID товара в состоянии FSM для дальнейшего использования
#         await state.update_data(product_id=product_id)
#     except IndexError:
#         await message.answer("Не удалось обработать выбранный товар. Пожалуйста, попробуйте снова.")


# # Обработка ввода количества
# @search_router.message(OrderState.waiting_for_quantity)
# async def process_quantity(message: Message, state: FSMContext):
#     user_data = await state.get_data()
#     product_id = user_data['product_id']

#     # Проверяем, что пользователь ввел корректное число
#     if not message.text.isdigit():
#         await message.answer("Пожалуйста, введите корректное количество.")
#         return

#     quantity = int(message.text)

#     # Здесь можно выполнять действия с товаром, например, отправить заказ
#     await message.answer(f"Заказ на {quantity} единиц товара с ID {product_id} принят!")

#     # Сбрасываем состояние
#     await state.clear()
