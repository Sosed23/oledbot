from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cart_product_keyboard(product_id: int, prod_cart_id: int, quantity: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"cart-product_[-]_{prod_cart_id}_{quantity}")
    kb.button(text="➕", callback_data=f"cart-product_[+]_{prod_cart_id}_{quantity}")
    kb.button(
        text="✖️", callback_data=f"cart-product-delete_{product_id}_{prod_cart_id}")
    kb.adjust(3)
    return kb.as_markup()
