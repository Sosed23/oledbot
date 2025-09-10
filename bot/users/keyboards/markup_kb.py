from aiogram.types import ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from bot.config import webapp_url


def back_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Фильтр моделей", web_app=WebAppInfo(url=webapp_url))
    kb.button(text="✨ Поиск с ИИ")
    kb.button(text="🔍 Поиск модели")
    kb.button(text="🛒 Корзина")
    kb.button(text="🗂 Мои заказы")
    # kb.button(text="Тест")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)
