from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from loguru import logger
from bot.planfix import planfix_price_basic_nomenclature_re_gluing, planfix_basic_nomenclature_re_gluing
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO

from bot.operations import OPERATION_NAMES, PLANFIX_TO_OPERATION_ID


import asyncio

async def handle_re_gluing_common(callback: CallbackQuery, state: FSMContext):
    try:
        state_data = await state.get_data()
        model_name = state_data.get('model_name', 'не указан')
        model_id = state_data.get('model_id', 'не указан')
        
        data_basic_nomenclature_re_gluing = await planfix_basic_nomenclature_re_gluing(model_id=model_id)

        messages = []
        
        for entry in data_basic_nomenclature_re_gluing['directoryEntries']:
            pricelist_key = None
            name_model = None
            
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
                            formatted_value = f"{int(value):,}".replace(",", " ")
                            value_re_gluing = (
                                f"🔹 <b>{name_operation}</b>\n"
                                f"📌 Артикул: <b>{model_id}</b>\n"
                                f"ℹ️ Модель: <b>{model_name}</b>\n"
                                f"💰 Цена: <b>{formatted_value} руб.</b>"
                            )
                            
                            # Ограничиваем длину только для callback_data
                            callback_model_id = str(model_id)[:10]
                            callback_model_name = model_name[:15]
                            callback_data = f"re_gluing_cart:{callback_model_id}:{callback_model_name}:{operation_id}"
                            logger.debug(f"Callback data: {callback_data} (length: {len(callback_data.encode('utf-8'))} bytes)")
                            
                            await callback.message.answer(
                                f"{value_re_gluing}",
                                reply_markup=in_kb.re_gluing_cart_keyboard(
                                    model_id=callback_model_id,
                                    model_name=callback_model_name,
                                    operation=operation_id
                                )
                            )
                            # Задержка между сообщениями
                            await asyncio.sleep(0.1)
                else:
                    logger.warning(f"Некорректный ответ от planfix_price_basic_nomenclature_re_gluing: {data_pricelist}")
            else:
                logger.debug(f"Пропущен вызов planfix_price_basic_nomenclature_re_gluing: pricelist_key={pricelist_key}, name_model={name_model}")

        # await callback.message.answer("\n".join(messages))
        
    except Exception as e:
        logger.error(f"Ошибка в handle_re_gluing_common: {e}")
        result = await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()
        return result