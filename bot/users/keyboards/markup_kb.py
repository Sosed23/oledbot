from aiogram.types import ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Фильтр моделей", web_app=WebAppInfo(url="http://212.109.221.68:1111/webapp"))
    kb.button(text="✨ Поиск с ИИ")
    kb.button(text="🔍 Поиск модели")
    kb.button(text="🛒 Корзина")
    kb.button(text="🗂 Мои заказы")
    # kb.button(text="Тест")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)
