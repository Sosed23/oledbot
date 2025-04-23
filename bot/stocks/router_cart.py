from aiogram import Router, F, types
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from bot.planfix import planfix_production_task_id, planfix_basic_back_cover_cart, planfix_price_basic_back_cover, planfix_price_assembly_basic_back_cover
from bot.stocks.keyboards import inline_kb_cart as kb
from bot.stocks.dao import CartDAO
from bot.operations import OPERATION_NAMES
import logging

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

# Обработчик нажатия кнопки "В корзину"
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
        touch_or_backlight=False
    )

    if not isinstance(cart_item_id, int):
        logger.error(f"CartDAO.add вернул неожиданный тип: {type(cart_item_id)}")
        await callback.answer("Ошибка при добавлении в корзину.", show_alert=True)
        return

    if operation == 6:
        # Для операции 6 задаем вопрос о подтверждении
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
            f"🔹 <b>Замена/Сборка задней крышки</b>\n"
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
                price_assembly=price_assembly  # Добавляем price_assembly
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
        logger.debug("Услуга подтверждена для не-6 операции.")
        await callback.message.answer("Услуга добавлена в корзину!")

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
    price_assembly = state_data.get('price_assembly', 0)  # Извлекаем price_assembly, по умолчанию 0

    # Получаем данные для формирования сообщения
    data_back_cover = await planfix_basic_back_cover_cart(task_id=task_id, filter_id=104414)
    custom_fields = data_back_cover.get("directoryEntries", [{}])[0].get("customFieldData", [])
    color = "не указан"
    name_operation = OPERATION_NAMES.get(6, "Неизвестная операция")
    
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

    if action == "yes":
        # Подтверждение: обновляем assembly_required=True
        await CartDAO.update(
            filter_by={"id": prod_cart_id},
            assembly_required=True
        )
        logger.info(f"Услуга подтверждена: prod_cart_id={prod_cart_id}")

        message_text = (
            f"✅ <b>Услуга успешно добавлена в корзину!</b>\n\n"
            f"🔹 <b>{name_operation}:</b>\n"
            f"📌 Артикул: <b>{task_id}</b>\n"
            f"ℹ️ Модель: <b>{product_name}</b>\n"
            f"🎨 Цвет: <b>{color}</b>\n"
            f"💰 Цена: <b>{formatted_price} руб.</b>\n\n"
            f"📝 Разбор/Сбор: <b>{confirmation_status}</b>\n"
            f"💰 Цена разбора/сбора: <b>{formatted_assembly_price}</b>\n"
        )

        await callback.message.delete()
        await callback.message.answer(message_text)
    elif action == "no":
        
        message_text = (
            f"✅ <b>Услуга успешно добавлена в корзину!</b>\n\n"
            f"🔹 <b>{name_operation}:</b>\n"
            f"📌 Артикул: <b>{task_id}</b>\n"
            f"ℹ️ Модель: <b>{product_name}</b>\n"
            f"🎨 Цвет: <b>{color}</b>\n"
            f"💰 Цена: <b>{formatted_price} руб.</b>\n"
        )

        await callback.message.delete()
        await callback.message.answer(message_text)

    await state.clear()
    await callback.answer()

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
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Тестирование"
                )
            elif operation == 2:
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

                confirmation_status = "✅ Подтверждено" if assembly_required else "❌ Не подтверждено"
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"🎨 Цвет: <b>{color}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Статус: <b>{confirmation_status}</b>"
                )
            elif operation == 7:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Продажа устройства"
                )
            else:
                message_text = (
                    f"🔹 <b>{idx + 1}. {name_operation}:</b>\n"
                    f"📌 Артикул: <b>{task_id}</b>\n"
                    f"ℹ️ Модель: <b>{name}</b>\n"
                    f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                    f"📝 Описание: Нет описания"
                )

            total_price += price * quantity if assembly_required else 0  # Учитываем только подтвержденные услуги

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