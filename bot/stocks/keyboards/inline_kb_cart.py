from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cart_product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Удалить", callback_data=f"cart-product_{product_id}")
    kb.adjust(1)
    return kb.as_markup()
