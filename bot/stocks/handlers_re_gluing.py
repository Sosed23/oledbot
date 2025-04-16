from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from loguru import logger
from bot.planfix import planfix_all_production_filter, planfix_production_task_id, planfix_basic_nomenclature_re_gluing
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO

async def handle_re_gluing_common(callback: CallbackQuery, state: FSMContext):

    try:
        state_data = await state.get_data()
        model_name = state_data.get('model_name', 'не указан')
        model_id = state_data.get('model_id', 'не указан')
        
        data_basic_nomenclature_re_gluing = await planfix_basic_nomenclature_re_gluing(model_id=model_id)

        await callback.message.answer(f'{data_basic_nomenclature_re_gluing}')

        await callback.answer()
        
    except Exception as e:
        logger.error(f"Ошибка в handle_production_common: {e}")
        result = await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()
        return result