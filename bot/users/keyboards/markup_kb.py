from aiogram.types import ReplyKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def back_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    webapp_url = f"https://oledbot.setdev.ru/webapp?user_id={user_id}"
    kb = ReplyKeyboardBuilder()
    kb.button(text="Фильтр моделей", web_app=WebAppInfo(url=webapp_url))
    kb.button(text="✨ Поиск с ИИ")
    kb.button(text="🔍 Поиск модели")
    kb.button(text="🛒 Корзина")
    kb.button(text="🗂 Мои заказы")
    # kb.button(text="Тест")
    kb.adjust(2, 2)
    return kb.as_markup(resize_keyboard=True)
