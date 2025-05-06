from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.planfix import (
    planfix_production_task_id, 
    planfix_basic_back_cover_cart, 
    planfix_price_basic_back_cover, 
    planfix_price_assembly_basic_back_cover,
    planfix_price_basic_nomenclature_re_gluing, 
    planfix_basic_nomenclature_re_gluing
)
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.users.keyboards import inline_kb as user_kb
from bot.stocks.dao import CartDAO
from bot.operations import OPERATION_NAMES, PLANFIX_TO_OPERATION_ID
import logging
import asyncio

from bot.stocks.handlers_back_cover import handle_back_cover_common
from bot.stocks.handlers_production import handle_production_common

cart_router = Router()


# Настройка логирования
logger = logging.getLogger(__name__)

# Определяем состояние для ожидания подтверждения
class CartStates(StatesGroup):
    waiting_for_confirmation = State()

# Функция для создания клавиатуры с вопросом "Да/Нет"
def get_confirmation_keyboard(prod_cart_id: str) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data=f"cart_confirm_yes_{prod_cart_id}"),
            InlineKeyboardButton(text="Нет", callback_data=f"cart_confirm_no_{prod_cart_id}")
        ]
    ])
    return keyboard

##### ОБРАБОТЧИК ДЛЯ ОТОБРАЖЕНИЯ ПОВТОРНО КНОПКИ -> УСЛУГИ: ПЕРЕКЛЕЙКА ДИСПЛЕЯ - 1, 2

@cart_router.callback_query(F.data.startswith("cart_search_re-gluing_"))
async def handle_re_gluing_common(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Вызван handle_re_gluing_common с callback_data: {callback.data}")
    try:
        # Извлекаем model_id и model_name из callback_data
        data = callback.data.split("_")
        model_id = data[3] if len(data) > 3 else None
        model_name = data[4] if len(data) > 4 else "не указана"

        if not model_id:
            await callback.message.answer("Не удалось определить ID модели. Пожалуйста, выберите модель заново.")
            await callback.answer()
            return

        # Сохраняем model_id и model_name в состоянии
        await state.update_data(model_id=model_id, model_name=model_name)

        data_basic_nomenclature_re_gluing = await planfix_basic_nomenclature_re_gluing(model_id=model_id, filter_id=104412)

        messages = []
        
        for entry in data_basic_nomenclature_re_gluing['directoryEntries']:
            pricelist_key = None
            name_model = None
            basic_key = entry.get('key')
            
            for field_data in entry['customFieldData']:
                if field_data['field']['id'] == 3884 and field_data['field']['name'] == 'Название':
                    name_model = field_data['value']
                if field_data['field']['id'] == 3902 and field_data['field']['name'] == 'Прайс-лист':
                    pricelist_key = field_data['value'].get('id')
            
            if pricelist_key is not None and pricelist_key != 0 and name_model:
                messages.append(f"ID: {pricelist_key}, name_model: {name_model}")
                data_pricelist = await planfix_price_basic_nomenclature_re_gluing(model_id=model_id, pricelist_key=pricelist_key)

                if data_pricelist.get('result') == 'success' and 'entry' in data_pricelist:
                    for field_data in data_pricelist['entry']['customFieldData']:
                        if 'value' not in field_data or field_data['value'] is None:
                            logger.warning(f"Отсутствует или пустое 'value' в field_data: {field_data}")
                            continue
                        
                        value = field_data['value']
                        if value != 0:
                            planfix_field_id = field_data['field']['id']
                            operation_id = PLANFIX_TO_OPERATION_ID.get(planfix_field_id)
                            if operation_id is None:
                                logger.warning(f"Неизвестный Planfix field_id: {planfix_field_id}, field_data: {field_data}")
                                continue
                            
                            name_operation = OPERATION_NAMES.get(operation_id, "Неизвестная операция")
                            pricelist_formatted = f"{int(value):,}".replace(",", " ")
                            value_re_gluing = (
                                f"🔹 <b>{name_operation}</b>\n"
                                f"📌 Артикул: <b>{basic_key}</b>\n"
                                f"ℹ️ Модель: <b>{model_name}</b>\n"
                                f"💰 Цена: <b>{pricelist_formatted} руб.</b>"
                            )
                            
                            # Ограничиваем длину только для callback_data
                            callback_model_id = str(model_id)[:10]
                            callback_model_name = model_name[:15]
                            callback_data = f"re-gluing-cart_{callback_model_id}_{callback_model_name}_{operation_id}_{basic_key}_{pricelist_formatted}"
                            logger.debug(f"Callback data: {callback_data} (length: {len(callback_data.encode('utf-8'))} bytes)")
                            
                            await callback.message.answer(
                                f"{value_re_gluing}",
                                reply_markup=kb.re_gluing_cart_keyboard(
                                    model_id=callback_model_id,
                                    model_name=callback_model_name,
                                    operation=operation_id,
                                    task_id=basic_key,
                                    price=value
                                )
                            )
                            await asyncio.sleep(0.1)
                else:
                    logger.warning(f"Некорректный ответ от planfix_price_basic_nomenclature_re_gluing: {data_pricelist}")
            else:
                logger.debug(f"Пропущен вызов planfix_price_basic_nomenclature_re_gluing: basic_key={basic_key}, pricelist_key={pricelist_key}, name_model={name_model}")
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_re_gluing_common: {e}")
#pragma: no cover
        result = await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()
        return result


##### ОБРАБОТЧИК ДЛЯ ОТОБРАЖЕНИЯ ПОВТОРНО КНОПКИ -> УСЛУГИ: ЗАМЕНА ЗАДНЕЙ КРЫШКИ - 6

@cart_router.callback_query(F.data.startswith("cart_search_back_cover_"))
async def handle_back_cover_cart(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Вызван handle_back_cover_cart с callback_data: {callback.data}")
    try:
        # Извлекаем model_id и model_name из callback_data
        data = callback.data.split("_")
        logger.debug(f"Разделенные данные callback.data: {data}")
        
        if len(data) < 6:  # Ожидаем минимум 6 частей: "cart_search_back_cover_MODELID_MODELNAME"
            logger.error(f"Неверный формат callback_data: {callback.data}")
            await callback.message.answer("Ошибка: неверный формат данных. Пожалуйста, выберите модель заново.")
            await callback.answer()
            return

        model_id = data[4]  # Правильный индекс для model_id
        model_name = "_".join(data[5:])  # Объединяем оставшиеся части, так как model_name может содержать пробелы (например, "Samsung S9")

        # Проверяем, что model_id является числом
        try:
            model_id = int(model_id)
        except ValueError:
            logger.error(f"model_id не является числом: {model_id}")
            await callback.message.answer("Ошибка: некорректный ID модели. Пожалуйста, выберите модель заново.")
            await callback.answer()
            return

        logger.debug(f"Извлеченный model_id: {model_id}, model_name: {model_name}")

        # Сохраняем model_id и model_name в состояние
        await state.update_data(model_id=model_id, model_name=model_name)

        # Вызываем обработку замены крышки
        await handle_back_cover_common(callback, state)

        # # После вывода всех вариантов добавляем клавиатуру для возврата к выбору опций
        # await callback.message.answer(
        #     f"Выберите другую опцию для модели: {model_name}",
        #     reply_markup=user_kb.search_keyboard_with_model(model_id=model_id, model_name=model_name)
        # )

    except Exception as e:
        logger.error(f"Ошибка в handle_back_cover_cart: {e}")
        await callback.message.answer("Произошла ошибка при обработке замены крышки.")
        await callback.answer()


##### ОБРАБОТЧИК ДЛЯ ОТОБРАЖЕНИЯ ПОВТОРНО КНОПКИ -> ТОВАРА: ДИСПЛЕЙ (ВОССТАНОВЛЕННЫЙ) - 4

@cart_router.callback_query(F.data.startswith("cart_ready_products_"))
async def handle_ready_products_cart(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Вызван handle_ready_products_cart с callback_data: {callback.data}")
    try:
        # Извлекаем model_id и model_name из callback_data
        data = callback.data.split("_")
        logger.debug(f"Разделенные данные callback.data: {data}")
        
        if len(data) < 5:  # Ожидаем минимум 5 частей: "cart_ready_products_MODELID_MODELNAME"
            logger.error(f"Неверный формат callback_data: {callback.data}")
            result = await callback.message.answer("Ошибка: неверный формат данных. Пожалуйста, выберите модель заново.")
            await callback.answer()
            return result

        model_id = data[3]  # Правильный индекс для model_id
        model_name = "_".join(data[4:])  # Объединяем оставшиеся части, так как model_name может содержать пробелы

        # Проверяем, что model_id является числом
        try:
            model_id = int(model_id)
        except ValueError:
            logger.error(f"model_id не является числом: {model_id}")
            result = await callback.message.answer("Ошибка: некорректный ID модели. Пожалуйста, выберите модель заново.")
            await callback.answer()
            return result

        logger.debug(f"Извлеченный model_id: {model_id}, model_name: {model_name}")

        # Сохраняем model_id и model_name в состояние
        await state.update_data(model_id=model_id, model_name=model_name)

        # Вызываем обработку готовой продукции и возвращаем результат
        result = await handle_production_common(callback, state, operation="4")
        return result

    except Exception as e:
        logger.error(f"Ошибка в handle_ready_products_cart: {e}")
        result = await callback.message.answer("Произошла ошибка при обработке готовой продукции.")
        await callback.answer()
        return result


# ОБРАБОТЧИК НАЖАТИЯ КНОПКИ "В КОРЗИНУ"

@cart_router.callback_query(F.data.startswith("re-gluing-cart_"))
async def add_to_cart(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Вызван add_to_cart с callback_data: {callback.data}")
    telegram_id = callback.from_user.id
    data = callback.data.split("_")
    if len(data) != 6:
        logger.error(f"Неверный формат callback_data: {callback.data}")
        await callback.answer("Ошибка при добавлении в корзину.", show_alert=True)
        return

    try:
        product_id = int(data[1])
        product_name = data[2]
        operation = int(data[3])
        task_id = int(data[4])
        price = int(float(data[5]))
    except ValueError as e:
        logger.error(f"Ошибка преобразования данных callback_data: {e}")
        await callback.answer("Ошибка при обработке данных.", show_alert=True)
        return

    logger.debug(f"Извлеченные данные: product_id={product_id}, product_name={product_name}, operation={operation}, task_id={task_id}, price={price}")

    # Сохраняем данные модели в состоянии (если они ещё не сохранены)
    state_data = await state.get_data()
    model_id = state_data.get('model_id', product_id)
    model_name = state_data.get('model_name', product_name)
    await state.update_data(model_id=model_id, model_name=model_name)

    # Устанавливаем touch_or_backlight=True для операции 2
    touch_or_backlight = True if operation == 2 else False

    # Добавляем услугу в корзину
    cart_item_id = await CartDAO.add(
        telegram_id=telegram_id,
        product_id=product_id,
        task_id=task_id,
        product_name=product_name,
        operation=str(operation),
        price=price,
        quantity=1,
        assembly_required=False,
        touch_or_backlight=touch_or_backlight
    )

    if not isinstance(cart_item_id, int):
        logger.error(f"CartDAO.add вернул неожиданный тип: {type(cart_item_id)}")
        await callback.answer("Ошибка при добавлении в корзину.", show_alert=True)
        return

    if operation in (1, 2, 6):  # Операции с подтверждением разборки/сборки
        # Для операций 1, 2 и 6 задаем вопрос о подтверждении
        formatted_price = f"{price:,.0f}".replace(',', ' ')

        # Получаем цену разборки/сборки
        data_price_assembly = await planfix_price_assembly_basic_back_cover(model_id=product_id)

        # Извлекаем цену разборки/сборки
        price_assembly = None
        try:
            if data_price_assembly.get("result") == "success":
                entries = data_price_assembly.get("directoryEntries", [])
                if entries and "customFieldData" in entries[0]:
                    custom_fields = entries[0]["customFieldData"]
                    for field in custom_fields:
                        if field.get("field", {}).get("id") == 3780:  # Поле "Цена разборки/сборки"
                            price_assembly = field.get("value")
                            break
            if price_assembly is None:
                logger.warning(f"Цена разборки/сборки не найдена в ответе: {data_price_assembly}")
                price_assembly = 0  # Значение по умолчанию, если цена не найдена
            formatted_assembly_price = f"{int(price_assembly):,.0f}".replace(',', ' ') + " руб."
        except Exception as e:
            logger.error(f"Ошибка извлечения цены разборки/сборки: {e}, данные: {data_price_assembly}")
            await callback.message.answer("Ошибка получения цены разборки/сборки.")
            await callback.answer("Ошибка при добавлении услуги.", show_alert=True)
            return

        message_text = (
            f"🔹 <b>{OPERATION_NAMES.get(operation, 'Неизвестная операция')}</b>\n"
            f"📌 Артикул: <b>{task_id}</b>\n"
            f"ℹ️ Модель: <b>{product_name}</b>\n"
            f"💰 Цена: <b>{formatted_price} руб.</b>\n\n"
            f"✅ <b>Добавить Разбор/Сбор в корзину?</b>\n"
            f"💰 Цена Разбор/Сбор: <b>{formatted_assembly_price}</b>\n"
        )
        try:
            await callback.message.answer(
                message_text,
                reply_markup=get_confirmation_keyboard(str(cart_item_id))
            )
            logger.debug("Сообщение с вопросом отправлено.")
            # Сохраняем price_assembly в состоянии
            await state.update_data(
                prod_cart_id=cart_item_id,
                product_id=product_id,
                product_name=product_name,
                task_id=task_id,
                price=price,
                price_assembly=price_assembly,
                operation=operation
            )
            await state.set_state(CartStates.waiting_for_confirmation)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения с вопросом: {e}")
            await callback.answer("Ошибка при добавлении услуги.", show_alert=True)
    else:
        # Для других операций подтверждаем добавление
        await CartDAO.update(
            filter_by={"id": cart_item_id},
            assembly_required=True
        )
        logger.debug("Услуга подтверждена для не-1, не-2 и не-6 операции.")
        # Отправляем сообщение об успешном добавлении без клавиатуры
        await callback.message.answer("✅ Услуга успешно добавлена в корзину!")
        # Отправляем отдельное сообщение с клавиатурой
        await callback.message.answer(
            f"Выберете нужную опцию для модели: {model_name}",
            reply_markup=user_kb.search_keyboard_with_model(model_id=model_id, model_name=model_name)
        )

    await callback.answer()

# Обработчик для кнопок "Да" и "Нет"
@cart_router.callback_query(F.data.startswith("cart_confirm_"), CartStates.waiting_for_confirmation)
async def process_cart_confirmation(callback: CallbackQuery, state: FSMContext):
    logger.debug(f"Вызван process_cart_confirmation с callback_data: {callback.data}")
    action, prod_cart_id = callback.data.split("_")[2], callback.data.split("_")[3]

    # Преобразуем prod_cart_id в int
    try:
        prod_cart_id = int(prod_cart_id)
    except ValueError:
        logger.error(f"Неверный формат prod_cart_id: {prod_cart_id}")
        await callback.answer("Ошибка при обработке подтверждения.", show_alert=True)
        return

    # Получаем данные из состояния
    state_data = await state.get_data()
    product_id = state_data.get('product_id')
    product_name = state_data.get('product_name')
    task_id = state_data.get('task_id')
    price = state_data.get('price')
    price_assembly = state_data.get('price_assembly', 0)
    operation = state_data.get('operation')
    model_id = state_data.get('model_id')
    model_name = state_data.get('model_name')

    # Получаем данные для формирования сообщения
    color = "не указан"
    if operation == 6:
        data_back_cover = await planfix_basic_back_cover_cart(task_id=task_id, filter_id=104414)
        custom_fields = data_back_cover.get("directoryEntries", [{}])[0].get("customFieldData", [])
        for field in custom_fields:
            field_id = field.get("field", {}).get("id")
            if field_id == 3892:  # ID поля Цвет
                color = field.get("value", {}).get("value", "не указан")
            elif field_id == 3902:  # ID поля Прайс-лист
                pricelist_key = field.get("value", {}).get("id", "не указан")
                data_pricelist = await planfix_price_basic_back_cover(model_id=int(product_id), pricelist_key=pricelist_key)
                if data_pricelist.get('result') == 'success' and 'entry' in data_pricelist:
                    for field_data in data_pricelist['entry']['customFieldData']:
                        price = int(field_data['value'])  # Обновляем цену

    formatted_price = f"{price:,.0f}".replace(',', ' ')
    confirmation_status = "Подтвержден"
    formatted_assembly_price = f"{int(price_assembly):,.0f}".replace(',', ' ') + " руб."
    name_operation = OPERATION_NAMES.get(operation, "Неизвестная операция")

    if action == "yes":
        # Подтверждение: обновляем assembly_required=True
        await CartDAO.update(
            filter_by={"id": prod_cart_id},
            assembly_required=True
        )
        logger.info(f"Услуга подтверждена: prod_cart_id={prod_cart_id}")

        if operation == 6:
            message_text = (
                f"✅ Услуга успешно добавлена в корзину!\n\n"
                f"🔹 <b>{name_operation}:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{product_name}</b>\n"
                f"🎨 Цвет: <b>{color}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n\n"
                f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
                f"💰 Цена разбора/сборки: <b>{formatted_assembly_price}</b>\n"
            )
        else:  # operation == 1 или operation == 2
            message_text = (
                f"✅ Услуга успешно добавлена в корзину!\n\n"
                f"🔹 <b>{name_operation}:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{product_name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n\n"
                f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
                f"💰 Цена разбора/сборки: <b>{formatted_assembly_price}</b>\n"
            )

        await callback.message.delete()
        # Отправляем сообщение об успешном добавлении
        await callback.message.answer(message_text)
        # Отправляем отдельное сообщение с клавиатурой
        await callback.message.answer(
            f"Выберете нужную опцию для модели: {model_name}",
            reply_markup=user_kb.search_keyboard_with_model(model_id=model_id, model_name=model_name)
        )
    elif action == "no":
        if operation == 6:
            message_text = (
                f"✅ Услуга успешно добавлена в корзину!\n\n"
                f"🔹 <b>{name_operation}:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{product_name}</b>\n"
                f"🎨 Цвет: <b>{color}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
            )
        else:  # operation == 1 или operation == 2
            message_text = (
                f"✅ Услуга успешно добавлена в корзину!\n\n"
                f"🔹 <b>{name_operation}:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{product_name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
            )

        await callback.message.delete()
        # Отправляем сообщение об успешном добавлении
        await callback.message.answer(message_text)
        # Отправляем отдельное сообщение с клавиатурой
        await callback.message.answer(
            f"Выберете нужную опцию для модели: {model_name}",
            reply_markup=user_kb.search_keyboard_with_model(model_id=model_id, model_name=model_name)
        )

    await state.clear()
    await callback.answer()


###################### СПИСОК ПОЗИЦИЙ КОРЗИНЫ ####################

@cart_router.message(F.text == '🛒 Корзина')
async def send_product_cart(message: Message):
    telegram_id = message.from_user.id

    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)
    total_price = 0
    messages = []  # Список для хранения всех отправленных сообщений

    if product_cart:
        messages_to_delete = []  # Список для хранения ID сообщений для удаления
        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            task_id = product.task_id
            name = product.product_name
            quantity = product.quantity
            operation = product.operation
            assembly_required = product.assembly_required
            touch_or_backlight = product.touch_or_backlight

            # Приводим operation к целому числу
            try:
                operation = int(operation)
            except (ValueError, TypeError):
                operation = 0

            # Инициализируем переменные
            price = product.price or 0
            comment = ""
            name_operation = OPERATION_NAMES.get(operation, "Неизвестная операция")
            formatted_price = f"{price:,.0f}".replace(',', ' ')

            # Инициализируем price_assembly для операций 1, 2 и 6
            price_assembly = 0
            if operation in (1, 2, 6):  # Операции с разборкой/сборкой
                # Получаем цену разборки/сборки
                data_price_assembly = await planfix_price_assembly_basic_back_cover(model_id=product_id)
                try:
                    if data_price_assembly.get("result") == "success":
                        entries = data_price_assembly.get("directoryEntries", [])
                        if entries and "customFieldData" in entries[0]:
                            custom_fields = entries[0]["customFieldData"]
                            for field in custom_fields:
                                if field.get("field", {}).get("id") == 3780:  # Поле "Цена разборки/сборки"
                                    price_assembly = field.get("value")
                                    break
                    if price_assembly is None:
                        logger.warning(f"Цена разборки/сборки не найдена в ответе: {data_price_assembly}")
                        price_assembly = 0
                except Exception as e:
                    logger.error(f"Ошибка извлечения цены разборки/сборки: {e}, данные: {data_price_assembly}")
                    price_assembly = 0

            # Логика для операции 4: получаем данные из Planfix
            if operation == 4:
                product_cart_data = await planfix_production_task_id(task_id=task_id)
                custom_fields = product_cart_data.get("task", {}).get("customFieldData", [])

                price = 0
                comment = ""
                for field in custom_fields:
                    field_id = field.get("field", {}).get("id")
                    if field_id == 12126:  # ID поля Price
                        price = field.get("value") or 0
                    elif field_id == 5498:  # ID поля Комментарии
                        comment = field.get("value", "")

                formatted_price = f"{price:,.0f}".replace(',', ' ')
                await CartDAO.update(filter_by={"id": prod_cart_id}, price=price)

            # Формируем message_text в зависимости от операции
            if operation == 1:
                confirmation_status = "Подтвержден"
                formatted_assembly_price = f"{int(price_assembly):,.0f}".replace(',', ' ') + " руб."
                if assembly_required:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                        f"📝 Описание: Тестирование\n\n"
                        f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
                        f"💰 Цена разбора/сборки: <b>{formatted_assembly_price}</b>\n"
                    )
                else:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                        f"📝 Описание: Тестирование"
                    )
            elif operation == 2:
                confirmation_status = "Подтвержден"
                formatted_assembly_price = f"{int(price_assembly):,.0f}".replace(',', ' ') + " руб."
                if assembly_required:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                        f"📝 Описание: Тестирование и замена подсветки/тача\n\n"
                        f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
                        f"💰 Цена разбора/сборки: <b>{formatted_assembly_price}</b>\n"
                    )
                else:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                        f"📝 Описание: Тестирование и замена подсветки/тача"
                    )
            elif operation == 3:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Разборка и сборка дисплея"
                )
            elif operation == 4:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: {comment or 'Тестирование'}"
                )
            elif operation == 5:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Поставка запчасти"
                )
            elif operation == 6:
                data_back_cover = await planfix_basic_back_cover_cart(task_id=task_id, filter_id=104414)
                custom_fields = data_back_cover.get("directoryEntries", [{}])[0].get("customFieldData", [])
                color = "не указан"
                for field in custom_fields:
                    field_id = field.get("field", {}).get("id")
                    if field_id == 3892:  # ID поля Цвет
                        color = field.get("value", {}).get("value", "не указан")
                    elif field_id == 3902:  # ID поля Прайс-лист
                        pricelist_key = field.get("value", {}).get("id", "не указан")
                        data_pricelist = await planfix_price_basic_back_cover(model_id=int(product_id), pricelist_key=pricelist_key)
                        if data_pricelist.get('result') == 'success' and 'entry' in data_pricelist:
                            for field_data in data_pricelist['entry']['customFieldData']:
                                price_back_cover = int(field_data['value'])  # Преобразуем в int
                                formatted_price = f"{price_back_cover:,.0f}".replace(',', ' ')
                            await CartDAO.update(filter_by={"id": prod_cart_id}, price=price_back_cover)
                            price = price_back_cover

                confirmation_status = "Подтвержден"
                formatted_assembly_price = f"{int(price_assembly):,.0f}".replace(',', ' ') + " руб."

                if assembly_required:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"🎨 Цвет: <b>{color}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n\n"
                        f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
                        f"💰 Цена разбора/сборки: <b>{formatted_assembly_price}</b>\n"
                    )
                else:
                    message_text = (
                        f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                        f"📌 Артикул: <b>{task_id}</b>\n"
                        f"ℹ️ Модель: <b>{name}</b>\n"
                        f"🎨 Цвет: <b>{color}</b>\n"
                        f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    )
            elif operation == 7:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Продажа устройства - {touch_or_backlight}"
                )
            else:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Нет описания"
                )

            # Учитываем price и price_assembly в зависимости от операции
            if operation in (1, 2, 6):  # Операции с разборкой/сборкой
                # Для операций 1, 2 и 6: если assembly_required == True, добавляем price + price_assembly, иначе только price
                if assembly_required:
                    total_price += (price + int(price_assembly)) * quantity
                else:
                    total_price += price * quantity
            else:
                # Для остальных операций добавляем только price
                total_price += price * quantity

            # Отправляем сообщение
            sent_message = await message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )
            messages.append(sent_message)
            messages_to_delete.append(sent_message.message_id)

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"📝 Описание товаров в корзине:\n"
            f"🔢 Общее кол-во товаров: {total_quantity} шт.\n"
            f"💵 Общая сумма заказа: {formatted_total_price} руб."
        )
        total_message = await message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
        messages.append(total_message)
        messages_to_delete.append(total_message.message_id)

        return messages

    else:
        result = await message.answer("Корзина пуста.")
        return [result]

# УДАЛЕНИЕ ПОЗИЦИИ ИЗ СПИСКА КОРЗИНЫ
@cart_router.callback_query(F.data.startswith('cart-aiagent-product-delete'))
async def delete_product_aiagent_cart(callback_query: types.CallbackQuery):
    product_id = callback_query.data.split('_')[1]
    prod_cart_id = int(callback_query.data.split('_')[2])

    # Удаляем товар из корзины
    await CartDAO.delete(filter_by={"id": prod_cart_id})

    # Подтверждаем удаление
    await callback_query.answer("Товар удалён из корзины.")

    # Пересчитываем и обновляем корзину
    telegram_id = callback_query.from_user.id
    product_cart = await CartDAO.find_all(telegram_id=telegram_id)

    total_quantity = sum(product.quantity for product in product_cart)
    total_price = 0
    messages = []  # Список для хранения отправленных сообщений

    if product_cart:
        for idx, product in enumerate(product_cart):
            prod_cart_id = product.id
            product_id = product.product_id
            task_id = product.task_id
            name = product.product_name
            quantity = product.quantity

            product_cart_data = await planfix_production_task_id(task_id=task_id)
            custom_fields = product_cart_data.get("task", {}).get("customFieldData", [])

            price = 0
            comment = ""
            for field in custom_fields:
                field_id = field.get("field", {}).get("id")
                if field_id == 12126:  # ID поля Price
                    price = field.get("value") or 0
                elif field_id == 5498:  # ID поля Комментарии
                    comment = field.get("value", "")

            total_price += price * quantity
            formatted_price = f"{price:,.0f}".replace(',', ' ')

            message_text = (
                f"🔹 <b>{idx + 1}. Готовая продукция:</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{name}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                f"📝 Описание: {comment or 'нет описания'}"
            )

            sent_message = await callback_query.message.answer(
                message_text,
                reply_markup=kb.cart_aiagent_product_keyboard(product_id=product_id, prod_cart_id=prod_cart_id)
            )
            messages.append(sent_message)

        formatted_total_price = f"{total_price:,.0f}".replace(',', ' ')
        cart_text = (
            f"Описание товаров в корзине:\n"
            f"Общее кол-во товаров: {total_quantity} шт.\n"
            f"Общая сумма заказа: {formatted_total_price} руб."
        )
        total_message = await callback_query.message.answer(cart_text, reply_markup=kb.cart_order_keyboard())
        messages.append(total_message)

        # Возвращаем список сообщений
        return messages
    else:
        result = await callback_query.message.answer("Корзина пуста.")
        return [result]

# ОЧИСТКА КОРЗИНЫ
@cart_router.callback_query(F.data.startswith('clear_cart'))
async def clear_cart(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    await CartDAO.delete(telegram_id=telegram_id, delete_all=True)
    await callback_query.answer('Корзина очищена.')
    # Отправляем сообщение пользователю
    result = await callback_query.message.answer("Корзина очищена.")
    return [result]