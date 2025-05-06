from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from loguru import logger
from bot.planfix import planfix_stock_balance_spare_parts_filter, add_outgoing_comment_to_chat
from bot.utils.planfix_utils import strip_html
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO
from bot.users.dao import UserDAO

from bot.operations import OPERATION_NAMES, PLANFIX_TO_OPERATION_ID

class SparePartsOrder(StatesGroup):
    waiting_for_quantity = State()

async def handle_spare_parts_common(callback: CallbackQuery, state: FSMContext):
    try:
        state_data = await state.get_data()
        model_name = state_data.get('model_name', 'не указан')
        model_id = state_data.get('model_id', 'не указан')

        # Запрашиваем данные о запчастях
        data_spare_parts = await planfix_stock_balance_spare_parts_filter(model_id=model_id)

        if data_spare_parts.get('result') != 'success' or 'tasks' not in data_spare_parts:
            logger.warning(f"Ошибка получения данных о запчастях: {data_spare_parts}")
            await callback.message.answer("Не удалось получить данные о запчастях.")
            await callback.answer()
            return

        for task in data_spare_parts['tasks']:
            price = None
            spare_part_name = None
            spare_part_id = None
            balance = None

            for field_data in task['customFieldData']:
                if 'value' not in field_data or field_data['value'] is None:
                    logger.warning(f"Отсутствует или пустое 'value' в field_data: {field_data}")
                    continue

                field_id = field_data['field']['id']
                value = field_data['value']

                if field_id == 5718:  # Цена закупки, RUB
                    price = value
                elif field_id == 5512:  # Запчасть
                    spare_part_name = value.get('value') if isinstance(value, dict) else value
                    spare_part_id = value.get('id') if isinstance(value, dict) else None
                elif field_id == 5722:  # Св. остаток
                    balance = value

            if price and spare_part_name and spare_part_id and balance:
                price_formatted = f"{int(price):,}".replace(",", " ")
                balance_str = f"{int(balance)} шт."
                spare_part_formatted = (
                    f"🔹 <b>{spare_part_name}</b>\n"
                    f"📌 Артикул: <b>{spare_part_id}</b>\n"
                    f"ℹ️ Модель: <b>{model_name}</b>\n"
                    f"💰 Цена: <b>{price_formatted} руб.</b>\n"
                    f"📦 Остаток: <b>{balance_str}</b>"
                )

                # Ограничиваем длину для callback_data
                callback_model_id = str(model_id)[:10]
                callback_model_name = model_name[:15]
                callback_data = f"spare-parts-cart_{callback_model_id}_{callback_model_name}_5_{spare_part_id}_{price}"

                # Получаем chat_pf_id для отправки в Planfix
                telegram_id = callback.from_user.id
                data_chat_pf_id = await UserDAO.find_one_or_none(telegram_id=telegram_id)
                if not data_chat_pf_id or not data_chat_pf_id.chat_pf_id:
                    logger.warning(f"У пользователя {telegram_id} отсутствует chat_pf_id")
                    await callback.message.answer("Ошибка: у вас нет активного чата в Planfix. Пожалуйста, перезапустите бота с помощью /start.")
                    await state.clear()
                    return
                chat_pf_id = data_chat_pf_id.chat_pf_id

                await callback.message.answer(
                    spare_part_formatted,
                    reply_markup=in_kb.spare_parts_cart_keyboard(
                        model_id=callback_model_id,
                        model_name=callback_model_name,
                        operation="5",
                        task_id=str(spare_part_id),
                        price=price
                    ),
                    parse_mode="HTML"
                )

                # Отправляем сообщение в Planfix
                clean_message_text = strip_html(spare_part_formatted)
                success = await add_outgoing_comment_to_chat(chat_pf_id=chat_pf_id, comment=clean_message_text)
                if not success:
                    logger.error(f"Не удалось отправить сообщение в Planfix для пользователя {telegram_id}")
                    await callback.message.answer("Ошибка: не удалось отправить сообщение в Planfix.")
                else:
                    logger.info(f"Сообщение успешно отправлено в Planfix для пользователя {telegram_id}")

        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_spare_parts_common: {e}")
        await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()

async def add_spare_parts_search_ai_cart(callback_query: types.CallbackQuery, prefix: str, state: FSMContext):
    try:
        # Разбираем callback_data
        parts = callback_query.data.split('_')
        model_id = int(parts[1])
        model_name = parts[2]
        operation = parts[3]
        spare_part_id = int(parts[4])
        price = int(float(parts[5]))

        # Получаем данные о запчастях для получения остатка и spare_part_id
        data_spare_parts = await planfix_stock_balance_spare_parts_filter(model_id=model_id)
        balance = None
        found_spare_part_id = None
        for task in data_spare_parts.get('tasks', []):
            for field_data in task['customFieldData']:
                if field_data['field']['id'] == 5512 and isinstance(field_data['value'], dict):
                    if field_data['value'].get('id') == spare_part_id:
                        found_spare_part_id = field_data['value']['id']
                        for other_field in task['customFieldData']:
                            if other_field['field']['id'] == 5722:  # Св. остаток
                                balance = int(other_field['value'])
                        break
            if found_spare_part_id:
                break

        if balance is None or balance <= 0:
            await callback_query.message.answer("Запчасть отсутствует на складе.")
            await callback_query.answer()
            return

        if found_spare_part_id is None:
            await callback_query.message.answer("Не удалось получить ID запчасти.")
            await callback_query.answer()
            return

        # Сохраняем данные в состояние
        await state.update_data(
            model_id=model_id,
            model_name=model_name,
            operation=operation,
            spare_part_id=spare_part_id,
            price=price,
            balance=balance,
            telegram_id=callback_query.from_user.id
        )

        await callback_query.message.answer(f"Введите количество запчастей (не более {balance} шт.):")
        await state.set_state(SparePartsOrder.waiting_for_quantity)
        await callback_query.answer()

    except Exception as e:
        logger.error(f"Ошибка в add_spare_parts_search_ai_cart: {e}")
        await callback_query.message.answer("Произошла ошибка при добавлении запчасти.")
        await callback_query.answer()

async def process_quantity_spare_parts(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
        state_data = await state.get_data()
        balance = state_data.get('balance', 0)

        if quantity <= 0:
            await message.answer("Количество должно быть положительным числом. Пожалуйста, введите снова:")
            return
        if quantity > balance:
            await message.answer(f"Количество не может превышать остаток ({balance} шт.). Пожалуйста, введите снова:")
            return

        model_id = state_data.get('model_id')
        model_name = state_data.get('model_name')
        operation = state_data.get('operation')
        spare_part_id = state_data.get('spare_part_id')
        price = state_data.get('price')
        telegram_id = state_data.get('telegram_id')

        # Получаем chat_pf_id для отправки в Planfix
        data_chat_pf_id = await UserDAO.find_one_or_none(telegram_id=telegram_id)
        if not data_chat_pf_id or not data_chat_pf_id.chat_pf_id:
            logger.warning(f"У пользователя {telegram_id} отсутствует chat_pf_id")
            await message.answer("Ошибка: у вас нет активного чата в Planfix. Пожалуйста, перезапустите бота с помощью /start.")
            await state.clear()
            return
        chat_pf_id = data_chat_pf_id.chat_pf_id

        # Добавляем новую запись в корзину
        await CartDAO.add(
            telegram_id=telegram_id,
            product_id=model_id,
            product_name=model_name,
            quantity=quantity,
            operation=operation,
            task_id=spare_part_id,
            price=price,
            assembly_required=False
        )
        logger.info(f"Новая запись добавлена в корзину: telegram_id={telegram_id}, product_id={model_id}, operation={operation}, spare_part_id={spare_part_id}")

        price_formatted = f"{int(price):,}".replace(",", " ")
        amount = quantity * price
        amount_formatted = f"{int(amount):,}".replace(",", " ")

        message_text = (
            f"✅ Запчасть успешно добавлена в корзину!\n\n"
            f"🔹 <b>Дисплей (запчасть)</b>\n"
            f"📌 Артикул: <b>{spare_part_id}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"🔢 Количество: <b>{quantity} шт.</b>\n"
            f"💰 Цена: <b>{price_formatted} руб.</b>\n"
            f"🧾 Стоимость: <b>{amount_formatted} руб.</b>"
        )
        await message.answer(message_text, parse_mode="HTML")

        # Отправляем сообщение в Planfix
        clean_message_text = strip_html(message_text)
        success = await add_outgoing_comment_to_chat(chat_pf_id=chat_pf_id, comment=clean_message_text)
        if not success:
            logger.error(f"Не удалось отправить сообщение в Planfix для пользователя {telegram_id}")
            await message.answer("Ошибка: не удалось отправить сообщение в Planfix.")
        else:
            logger.info(f"Сообщение успешно отправлено в Planfix для пользователя {telegram_id}")

        await state.clear()

    except ValueError:
        await message.answer("Пожалуйста, введите целое число для количества:")
    except Exception as e:
        logger.error(f"Ошибка в process_quantity_spare_parts: {e}")
        await message.answer("Произошла ошибка при обработке количества.")
        await state.clear()