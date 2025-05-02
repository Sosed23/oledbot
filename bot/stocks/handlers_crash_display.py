from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command
from loguru import logger
from bot.planfix import planfix_stock_balance_filter, upload_photo_to_planfix, planfix_price_assembly_basic_back_cover, add_outgoing_comment_to_chat
from bot.utils.planfix_utils import extract_price_from_data
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO
from bot.users.dao import UserDAO
from collections import defaultdict
import asyncio
import re

from bot.operations import OPERATION_NAMES, PLANFIX_TO_OPERATION_ID

media_groups = defaultdict(list)
MEDIA_GROUP_TIMEOUT = 1.0

class CrashDisplayOrder(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_photo = State()

def strip_html(text: str) -> str:
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

async def handle_crash_display_common(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    model_name = state_data.get('model_name', 'не указан')
    model_id = state_data.get('model_id', 'не указан')

    data_crash_display_plus = await planfix_stock_balance_filter(model_id=model_id, operation="2")
    data_crash_display_minus = await planfix_stock_balance_filter(model_id=model_id, operation="3")

    price_plus = extract_price_from_data(data_crash_display_plus)
    price_minus = extract_price_from_data(data_crash_display_minus)
    
    operation = 7

    # Получаем chat_pf_id для отправки в Planfix
    telegram_id = callback.from_user.id
    data_chat_pf_id = await UserDAO.find_one_or_none(telegram_id=telegram_id)
    if not data_chat_pf_id or not data_chat_pf_id.chat_pf_id:
        logger.warning(f"У пользователя {telegram_id} отсутствует chat_pf_id")
        await callback.message.answer("Ошибка: у вас нет активного чата в Planfix. Пожалуйста, перезапустите бота с помощью /start.")
        await state.clear()
        return
    chat_pf_id = data_chat_pf_id.chat_pf_id

    if price_plus and float(price_plus) > 0:
        formatted_price_plus = f"{int(price_plus):,}".replace(",", " ")
        message_text = (
            f"🔹 <b>Битик с оригинальной подсветкой/тачом</b>\n"
            f"📌 Артикул: <b>{model_id}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"💰 Цена: <b>{formatted_price_plus} руб.</b>"
        )
        
        result = await callback.message.answer(
            message_text,
            reply_markup=in_kb.crash_display_cart_keyboard(
                model_id=model_id,
                model_name=model_name,
                operation=operation,
                task_id=model_id,
                price=price_plus,
                touch_or_backlight='False'
            ),
            parse_mode="HTML"
        )

        # Отправляем сообщение в Planfix
        clean_message_text = strip_html(message_text)
        success = await add_outgoing_comment_to_chat(chat_pf_id=chat_pf_id, comment=clean_message_text)
        if not success:
            logger.error(f"Не удалось отправить сообщение в Planfix для пользователя {telegram_id}")
            await callback.message.answer("Ошибка: не удалось отправить сообщение в Planfix.")
        else:
            logger.info(f"Сообщение успешно отправлено в Planfix для пользователя {telegram_id}")
        
        await callback.answer()

    if price_minus and float(price_minus) > 0:
        formatted_price_minus = f"{int(price_minus):,}".replace(",", " ")
        message_text = (
            f"🔹 <b>Битик с повреждённой подсветкой/тачом</b>\n"
            f"📌 Артикул: <b>{model_id}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"💰 Цена: <b>{formatted_price_minus} руб.</b>"
        )
        
        result = await callback.message.answer(
            message_text,
            reply_markup=in_kb.crash_display_cart_keyboard(
                model_id=model_id,
                model_name=model_name,
                operation=operation,
                task_id=model_id,
                price=price_minus,
                touch_or_backlight='True'
            ),
            parse_mode="HTML"
        )

        # Отправляем сообщение в Planfix
        clean_message_text = strip_html(message_text)
        success = await add_outgoing_comment_to_chat(chat_pf_id=chat_pf_id, comment=clean_message_text)
        if not success:
            logger.error(f"Не удалось отправить сообщение в Planfix для пользователя {telegram_id}")
            await callback.message.answer("Ошибка: не удалось отправить сообщение в Planfix.")
        else:
            logger.info(f"Сообщение успешно отправлено в Planfix для пользователя {telegram_id}")
    
        await callback.answer()

async def add_crash_display_search_ai_cart(callback_query: types.CallbackQuery, prefix: str, state: FSMContext):
    model_id = int(callback_query.data.split('_')[1])
    model_name = callback_query.data.split('_')[2]
    operation = callback_query.data.split('_')[3]
    task_id = int(callback_query.data.split('_')[4])
    price = int(float(callback_query.data.split('_')[5]))
    touch_or_backlight = callback_query.data.split('_')[6]
    
    touch_or_backlight_bool = touch_or_backlight.lower() == 'true'

    await state.update_data(
        model_id=model_id,
        model_name=model_name,
        operation=operation,
        task_id=task_id,
        price=price,
        touch_or_backlight=touch_or_backlight_bool,
        telegram_id=callback_query.from_user.id
    )

    await callback_query.message.answer("Введите количество битика (целое число):")
    await state.set_state(CrashDisplayOrder.waiting_for_quantity)
    
    await callback_query.answer()

async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = int(message.text)
        if quantity <= 0:
            await message.answer("Количество должно быть положительным числом. Пожалуйста, введите снова:")
            return
    except ValueError:
        await message.answer("Пожалуйста, введите целое число для количества:")
        return

    await state.update_data(quantity=quantity)

    await message.answer("Пожалуйста, прикрепите фото битика:")
    await state.set_state(CrashDisplayOrder.waiting_for_photo)

async def process_photo(message: types.Message, state: FSMContext):
    from bot.config import bot
    
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото:")
        return

    media_group_id = message.media_group_id
    if media_group_id:
        media_groups[media_group_id].append(message)
        await asyncio.sleep(MEDIA_GROUP_TIMEOUT)
        if media_groups[media_group_id][-1].message_id != message.message_id:
            return
        messages = media_groups[media_group_id]
        del media_groups[media_group_id]
    else:
        messages = [message]

    state_data = await state.get_data()
    logger.debug(f"Состояние FSM перед обработкой: {state_data}")

    model_id = state_data.get('model_id')
    model_name = state_data.get('model_name')
    operation = state_data.get('operation')
    price = state_data.get('price')
    touch_or_backlight = state_data.get('touch_or_backlight')
    telegram_id = state_data.get('telegram_id')
    quantity = state_data.get('quantity')

    data_chat_pf_id = await UserDAO.find_one_or_none(telegram_id=telegram_id)
    if not data_chat_pf_id or not data_chat_pf_id.chat_pf_id:
        logger.warning(f"У пользователя {telegram_id} отсутствует chat_pf_id")
        await message.answer("Ошибка: у вас нет активного чата в Planfix. Пожалуйста, перезапустите бота с помощью /start.")
        await state.clear()
        return
    chat_pf_id = data_chat_pf_id.chat_pf_id

    photo_files = []
    photo_file_ids = []
    failed_photos = 0

    for msg in messages:
        if msg.photo:
            photo = msg.photo[-1]
            try:
                from io import BytesIO
                buffer = BytesIO()
                await bot.download(file=photo.file_id, destination=buffer)
                photo_bytes = buffer.getvalue()
                logger.info(f"Фото успешно скачано из Telegram, размер: {len(photo_bytes)} байт")
                photo_files.append(photo_bytes)
                photo_file_ids.append(photo.file_id)
            except Exception as e:
                logger.error(f"Ошибка при скачиванием фото из Telegram: {e}")
                failed_photos += 1
                continue

    if not photo_files:
        await message.answer("Не удалось скачать ни одно фото. Пожалуйста, попробуйте снова.")
        return

    if failed_photos > 0:
        await message.answer(f"Не удалось скачать {failed_photos} фото. Загружено только {len(photo_files)} фото.")

    success = await upload_photo_to_planfix(chat_pf_id=chat_pf_id, photo_files=photo_files)
    if not success:
        await message.answer("Ошибка при загрузке фото в Planfix. Пожалуйста, попробуйте снова.")
        return

    task_id_crash_display_response = await planfix_price_assembly_basic_back_cover(model_id=model_id)
    task_id_crash_display = task_id_crash_display_response['directoryEntries'][0]['key']

    existing_cart = await CartDAO.find_one_or_none(
        telegram_id=telegram_id,
        product_id=model_id,
        operation=operation
    )
    if existing_cart:
        new_quantity = existing_cart.quantity + quantity
        existing_file_ids = existing_cart.photo_file_ids or []
        updated_file_ids = existing_file_ids + photo_file_ids
        data = {
            "quantity": new_quantity,
            "photo_file_ids": updated_file_ids
        }
        valid_columns = ["quantity", "photo_file_ids"]
        data = {k: v for k, v in data.items() if k in valid_columns}
        logger.debug(f"Данные для обновления: {data}")
        await CartDAO.update(
            filter_by={
                "telegram_id": telegram_id,
                "product_id": model_id,
                "operation": operation
            },
            data=data
        )
        logger.info(f"Запись в корзине обновлена: telegram_id={telegram_id}, product_id={model_id}, operation={operation}, новое количество={new_quantity}")
    else:
        await CartDAO.add(
            telegram_id=telegram_id,
            product_id=model_id,
            product_name=model_name,
            quantity=quantity,
            operation=operation,
            task_id=task_id_crash_display,
            price=price,
            assembly_required=False,
            touch_or_backlight=touch_or_backlight,
            photo_file_ids=photo_file_ids
        )
        logger.info(f"Новая запись добавлена в корзину: telegram_id={telegram_id}, product_id={model_id}, operation={operation}")

    if touch_or_backlight == False:
        message_text = (
            f"✅ Услуга успешно добавлена в корзину!\n\n"
            f"🔹 <b>Битик с оригинальной подсветкой/тачом</b>\n"
            f"📌 Артикул: <b>{task_id_crash_display}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"🔢 Количество: <b>{quantity} шт.</b>\n"
            f"💰 Цена: <b>{price} руб.</b>"
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

    else:
        message_text = (
            f"✅ Услуга успешно добавлена в корзину!\n\n"
            f"🔹 <b>Битик с повреждённой подсветкой/тачом</b>\n"
            f"📌 Артикул: <b>{task_id_crash_display}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"🔢 Количество: <b>{quantity} шт.</b>\n"
            f"💰 Цена: <b>{price} руб.</b>"
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