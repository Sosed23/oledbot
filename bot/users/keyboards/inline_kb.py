from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Кнопка инлайн меню", callback_data="back_home")
    kb.adjust(1)
    return kb.as_markup()


def device_brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Устройство", callback_data="device_select")
    kb.button(text="Бренд", callback_data="brand_select")
    kb.adjust(2)
    return kb.as_markup()


def device_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Смартфон", callback_data="device_Смартфон")
    kb.button(text="Планшет", callback_data="device_Планшет")
    kb.button(text="Смарт часы", callback_data="device_Смарт часы")
    kb.button(text="◀️ Назад", callback_data="device_back")
    kb.adjust(3, 1)
    return kb.as_markup()


def brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Apple", callback_data="brand_Apple")
    kb.button(text="Samsung", callback_data="brand_Samsung")
    kb.button(text="Demo", callback_data="brand_Демо")
    kb.button(text="Смарт часы", callback_data="brand_back")
    kb.adjust(2)
    return kb.as_markup()
