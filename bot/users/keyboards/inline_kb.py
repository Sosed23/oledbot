from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Кнопка инлайн меню", callback_data="back_home")
    kb.adjust(1)
    return kb.as_markup()


def device_brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Устройство", callback_data="device")
    kb.button(text="Бренд", callback_data="brand")
    kb.adjust(2)
    return kb.as_markup()


def device_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Смартфон", callback_data="Смартфон")
    kb.button(text="Планшет", callback_data="Планшет")
    kb.button(text="Смарт часы", callback_data="Смарт часы")
    kb.adjust(2)
    return kb.as_markup()


def brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Apple", callback_data="Apple")
    kb.button(text="Samsung", callback_data="Samsung")
    kb.button(text="Demo", callback_data="Демо")
    kb.adjust(2)
    return kb.as_markup()
