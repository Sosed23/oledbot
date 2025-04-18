from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from loguru import logger
from bot.planfix import planfix_all_production_filter, planfix_production_task_id
from bot.stocks.keyboards import inline_kb_cart as in_kb
from bot.stocks.dao import CartDAO

async def handle_production_common(callback: CallbackQuery, state: FSMContext, operation: str = "4"):

    try:
        state_data = await state.get_data()
        model_name = state_data.get('model_name', 'не указан')
        model_id = state_data.get('model_id', 'не указан')
        
        data_production = await planfix_all_production_filter(model_id=model_id)
        
        if not data_production or "tasks" not in data_production:
            result = await callback.message.answer("Нет данных о продукции.")
            await callback.answer()
            return result
        
        messages = []
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
                    formatted_price = f"{int(price):,}".replace(",", " ")
                elif field_name == "Комментарии":
                    description = field.get("value", "Описание отсутствует")
            
            message_text = (
                f"🔹 <b>Дисплей (восстановленный)</b>\n"
                f"📌 Артикул: <b>{task_id}</b>\n"
                f"ℹ️ Модель: <b>{model}</b>\n"
                f"💰 Цена: <b>{formatted_price} руб.</b>\n"
                f"📝 Описание: {description}"
            )
            
            result = await callback.message.answer(
                message_text,
                reply_markup=in_kb.aiagent_cart_keyboard(
                    model_id=model_id, model_name=model_name, operation=operation, task_id=task_id
                ),
                parse_mode="HTML"
            )
            messages.append(result)
        
        await callback.answer()
        return messages
    except Exception as e:
        logger.error(f"Ошибка в handle_production_common: {e}")
        result = await callback.message.answer("Произошла ошибка при обработке данных.")
        await callback.answer()
        return result

async def add_to_cart(callback_query: types.CallbackQuery, prefix: str):

    try:
        data_parts = callback_query.data.split('_')
        if len(data_parts) != 5 or data_parts[0] != prefix:
            raise ValueError("Неверный формат callback_data")
        
        model_id = int(data_parts[1])
        model_name = data_parts[2]
        operation = data_parts[3]
        task_id = data_parts[4]
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

        result = await callback_query.message.answer(
            f"📝 Новый дисплей (восстановленный) добавлен в корзину:\n"
            f"📌 Артикул: <b>{task_id}</b>\n"
            f"ℹ️ Модель: <b>{model_name}</b>\n"
            f"💰 Цена: <b>{price} руб.</b>\n",
            parse_mode="HTML"
        )
        await callback_query.message.delete()
        return result
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара в корзину для telegram_id={telegram_id}: {e}")
        result = await callback_query.message.answer("Произошла ошибка при добавлении товара в корзину. Попробуйте снова.")
        return result