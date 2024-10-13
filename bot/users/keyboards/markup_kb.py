from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="📋 Просмотр остатков")
    kb.button(text="📋 Поиск товара")  # Добавление кнопки "📋 Поиск товара"
    kb.adjust(2)  # Настройка на 2 кнопки в одном ряду
    return kb.as_markup(resize_keyboard=True)
