from aiogram import F, Router, types
import json
from loguru import logger
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
import asyncio

web_filter_router = Router()

class FilterState(StatesGroup):
    waiting_device = State()
    waiting_brand = State()
    waiting_series = State()
    waiting_model = State()

API_BASE = "http://localhost:800/api/v2"

async def fetch_api(endpoint: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}/{endpoint}") as response:
            if response.status == 200:
                return await response.json()
            else:
                return None

@web_filter_router.message(Command("filter"))
async def start_filter(message: types.Message, state: FSMContext):
    data = await fetch_api("devices")
    if not data:
        await message.answer("Ошибка загрузки устройств. Убедитесь, что web app запущен.")
        return
    devices = data["devices"]
    
    # Filter to only show required devices
    required_devices = ["Смартфон", "Планшет", "Смарт часы"]
    filtered_devices = [d for d in devices if d in required_devices]
    
    kb = InlineKeyboardBuilder()
    for device in filtered_devices:
        kb.button(text=device, callback_data=f"device_{device}")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await message.answer("Выберите устройство:", reply_markup=kb.as_markup())
    await state.set_state(FilterState.waiting_device)

@web_filter_router.callback_query(F.data.startswith("device_"), FilterState.waiting_device)
async def select_device(callback: types.CallbackQuery, state: FSMContext):
    device = callback.data.split("_", 1)[1]
    data = await fetch_api("brands")
    if not data:
        await callback.message.answer("Ошибка загрузки брендов.")
        await callback.answer()
        return
    brands = data["brands"]
    
    # Filter to only show required brands
    required_brands = ["Samsung", "Apple"]
    filtered_brands = [b for b in brands if b in required_brands]
    
    kb = InlineKeyboardBuilder()
    for brand in filtered_brands:
        kb.button(text=brand, callback_data=f"brand_{device}_{brand}")
    kb.button(text="◀️ Назад", callback_data="device_back")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer(f"Выберите бренд для {device}:", reply_markup=kb.as_markup())
    await state.update_data(device=device)
    await state.set_state(FilterState.waiting_brand)
    await callback.answer()

@web_filter_router.callback_query(F.data.startswith("brand_"), FilterState.waiting_brand)
async def select_brand(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 2)
    device = parts[1]
    brand = parts[2]
    
    # Use new API endpoint with query parameters
    data = await fetch_api(f"series?devices={device}&brands={brand}")
    if not data:
        await callback.message.answer("Ошибка загрузки серий.")
        await callback.answer()
        return
    series_list = data["series"]
    
    # If no series available for this brand/device combination
    # This can happen when a brand exists for a device type but doesn't have any series/models yet
    if not series_list:
        await callback.message.answer(f"Для бренда {brand} и устройства {device} серии не найдены.")
        await callback.answer()
        return
    
    kb = InlineKeyboardBuilder()
    for series in series_list:
        kb.button(text=series, callback_data=f"series_{device}_{brand}_{series}")
    kb.button(text="◀️ Назад", callback_data="brand_back")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer(f"Выберите серию для {brand}:", reply_markup=kb.as_markup())
    await state.update_data(brand=brand)
    await state.set_state(FilterState.waiting_series)
    await callback.answer()

@web_filter_router.callback_query(F.data.startswith("series_"), FilterState.waiting_series)
async def select_series(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 3)
    device = parts[1]
    brand = parts[2]
    series = parts[3]
    
    # Use new API endpoint with query parameters
    data = await fetch_api(f"models?devices={device}&brands={brand}&series={series}")
    if not data:
        await callback.message.answer("Ошибка загрузки моделей.")
        await callback.answer()
        return
    models = data["models"]
    kb = InlineKeyboardBuilder()
    for model in models:
        model_name = model["name"]
        model_id = model["model_id"]
        kb.button(text=model_name, callback_data=f"model_{device}_{brand}_{series}_{model_id}")
    kb.button(text="◀️ Назад", callback_data="series_back")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer(f"Выберите модель для серии {series}:", reply_markup=kb.as_markup())
    await state.update_data(series=series)
    await state.set_state(FilterState.waiting_model)
    await callback.answer()

@web_filter_router.callback_query(F.data.startswith("model_"), FilterState.waiting_model)
async def select_model(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split("_", 5)
    device = parts[1]
    brand = parts[2]
    series = parts[3]
    model_id = parts[4]
    # Здесь можно интегрировать с Planfix, используя model_id как proxy
    # Для примера, показываем опции как в search_keyboard_with_model
    kb = InlineKeyboardBuilder()
    kb.button(text="Переклейка дисплея", callback_data=f"cart_web_re-gluing_{model_id}")
    kb.button(text="Замена задней крышки", callback_data=f"cart_web_back_cover_{model_id}")
    kb.button(text="Продать битик", callback_data=f"cart_web_sell_broken_{model_id}")
    kb.button(text="Купить дисплей (восстановленный)", callback_data=f"cart_web_ready_products_{model_id}")
    kb.button(text="Купить дисплей (запчасть)", callback_data=f"cart_web_spare_parts_{model_id}")
    kb.adjust(2, 1, 2)
    await callback.message.answer(
        f"Выбрана модель с ID: {model_id} (устройство: {device}, бренд: {brand}, серия: {series})\nВыберите опцию:",
        reply_markup=kb.as_markup()
    )
    await state.clear()
    await callback.answer()

# Back handlers
@web_filter_router.callback_query(F.data == "device_back", FilterState.waiting_brand)
async def back_to_device(callback: types.CallbackQuery, state: FSMContext):
    data = await fetch_api("devices")
    if not data:
        await callback.message.answer("Ошибка загрузки устройств.")
        await callback.answer()
        return
    devices = data["devices"]
    
    # Filter to only show required devices
    required_devices = ["Смартфон", "Планшет", "Смарт часы"]
    filtered_devices = [d for d in devices if d in required_devices]
    
    kb = InlineKeyboardBuilder()
    for device in filtered_devices:
        kb.button(text=device, callback_data=f"device_{device}")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer("Выберите устройство:", reply_markup=kb.as_markup())
    await state.set_state(FilterState.waiting_device)
    await callback.answer()

@web_filter_router.callback_query(F.data == "brand_back", FilterState.waiting_series)
async def back_to_brand(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    device = state_data.get("device")
    data = await fetch_api("brands")
    if not data:
        await callback.message.answer("Ошибка загрузки брендов.")
        await callback.answer()
        return
    brands = data["brands"]
    
    # Filter to only show required brands
    required_brands = ["Samsung", "Apple"]
    filtered_brands = [b for b in brands if b in required_brands]
    
    kb = InlineKeyboardBuilder()
    for brand in filtered_brands:
        kb.button(text=brand, callback_data=f"brand_{device}_{brand}")
    kb.button(text="◀️ Назад", callback_data="device_back")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer(f"Выберите бренд для {device}:", reply_markup=kb.as_markup())
    await state.set_state(FilterState.waiting_brand)
    await callback.answer()

@web_filter_router.callback_query(F.data == "series_back", FilterState.waiting_model)
async def back_to_series(callback: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    device = state_data.get("device")
    brand = state_data.get("brand")
    
    # Use new API endpoint with query parameters
    data = await fetch_api(f"series?devices={device}&brands={brand}")
    if not data:
        await callback.message.answer("Ошибка загрузки серий.")
        await callback.answer()
        return
    series_list = data["series"]
    kb = InlineKeyboardBuilder()
    for series in series_list:
        kb.button(text=series, callback_data=f"series_{device}_{brand}_{series}")
    kb.button(text="◀️ Назад", callback_data="brand_back")
    kb.button(text="❌ Отмена", callback_data="filter_cancel")
    kb.adjust(1)
    await callback.message.answer(f"Выберите серию для {brand}:", reply_markup=kb.as_markup())
    await state.set_state(FilterState.waiting_series)
    await callback.answer()

@web_filter_router.callback_query(F.data == "filter_cancel")
async def cancel_filter(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("Фильтрация отменена.")
    await callback.answer()

@web_filter_router.message(F.web_app_data)
async def handle_web_app_data(message: types.Message):
    logger.info("handle_web_app_data called")
    try:
        data = json.loads(message.web_app_data)
        logger.info(f"Parsed web_app_data: {data}")
        if data.get('action') == 'select_model':
            model_name = data.get('name', '')
            model_id = data.get('model_id', '')
            if model_id is None:
                logger.error("model_id is None in select_model action")
                return await message.answer("Ошибка: ID модели не указан.")
            logger.info(f"Processing select_model: name={model_name}, model_id={model_id}")
            kb = InlineKeyboardBuilder()
            kb.button(text="Переклейка дисплея", callback_data=f"cart_web_re-gluing_{model_id}")
            kb.button(text="Замена задней крышки", callback_data=f"cart_web_back_cover_{model_id}")
            kb.button(text="Продать битик", callback_data=f"cart_web_sell_broken_{model_id}")
            kb.button(text="Купить дисплей (восстановленный)", callback_data=f"cart_web_ready_products_{model_id}")
            kb.button(text="Купить дисплей (запчасть)", callback_data=f"cart_web_spare_parts_{model_id}")
            kb.adjust(2, 1, 2)
            return await message.answer(
                f"Выберете нужную опцию для модели: {model_name}",
                reply_markup=kb.as_markup()
            )
        elif data.get('action') == 'open':
            logger.info("Web app opened, showing filter menu")
            return await message.answer("Вы успешно передали данные боту кнопкой «Фильтр моделей».")
        else:
            logger.info(f"Unknown action in web_app_data: {data.get('action', 'no action')}")
            # Для других действий удаляем сообщение
            await message.delete()
            return None
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in web_app_data: {e}")
        return await message.answer("Ошибка обработки данных из Web App.")