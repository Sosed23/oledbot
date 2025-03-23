from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    # kb.button(text="📋 Каталог товара")
    kb.button(text="✨ Поиск с ИИ")
    kb.button(text="🔍 Поиск товара")
    kb.button(text="🛒 Корзина")
    kb.button(text="🗂 Мои заказы")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)
