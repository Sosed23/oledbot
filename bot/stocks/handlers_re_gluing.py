from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from loguru import logger
from bot.planfix import planfix_price_basic_nomenclature_re_gluing, planfix_basic_nomenclature_re_gluing, planfix_stock_balance
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO

from bot.operations import OPERATION_NAMES, PLANFIX_TO_OPERATION_ID


import asyncio

async def handle_re_gluing_common(callback: CallbackQuery, state: FSMContext):
    try:
        state_data = await state.get_data()
        model_name = state_data.get('model_name', 'не указан')
        model_id = state_data.get('model_id', 'не указан')
        
        data_basic_nomenclature_re_gluing = await planfix_basic_nomenclature_re_gluing(model_id=model_id, filter_id=104412)

        # await callback.message.answer(f'{data_basic_nomenclature_re_gluing}')

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
                            callback_data = f"re_gluing_cart:{callback_model_id}:{callback_model_name}:{operation_id}:{basic_key}:{pricelist_formatted}"
                            logger.debug(f"Callback data: {callback_data} (length: {len(callback_data.encode('utf-8'))} bytes)")
                            
                            await callback.message.answer(
                                f"{value_re_gluing}",
                                reply_markup=in_kb.re_gluing_cart_keyboard(
                                    model_id=callback_model_id,
                                    model_name=callback_model_name,
                                    operation=operation_id,
                                    task_id=basic_key,
                                    price=value
                                )
                            )
                            # # Задержка между сообщениями
                            # await asyncio.sleep(0.1)
                else:
                    logger.warning(f"Некорректный ответ от planfix_price_basic_nomenclature_re_gluing: {data_pricelist}")
            else:
                logger.debug(f"Пропущен вызов planfix_price_basic_nomenclature_re_gluing: basic_key={basic_key}, pricelist_key={pricelist_key}, name_model={name_model}")
        
        await callback.answer()

    except Exception as e:
        logger.error(f"Ошибка в handle_re_gluing_common: {e}")
        result = await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()
        return result
    


async def add_re_gluing_cart(callback_query: types.CallbackQuery, prefix: str):

    product_id = int(callback_query.data.split('_')[1])
    model_name = callback_query.data.split('_')[2]
    operation = callback_query.data.split('_')[3]
    task_id = int(callback_query.data.split('_')[4])
    price = int(float(callback_query.data.split('_')[5]))
    telegram_id = callback_query.from_user.id

    # product_cart = await CartDAO.find_one_or_none(product_id=product_id, telegram_id=telegram_id)

    # if not product_cart:

    #     product_data = await planfix_stock_balance()
    #     product_name = next((item[1] for item in product_data if item[0] == product_id), "Неизвестный товар")

    await CartDAO.add(
        telegram_id=telegram_id,
        product_id=product_id,
        product_name=model_name,
        quantity=1,
        operation=operation,
        task_id=task_id,
        price=price,
        assembly_required=False,
        touch_or_backlight=False
    )
    await callback_query.answer(f'Новый товар {model_name} добавлен в корзину.')

    await callback_query.answer()