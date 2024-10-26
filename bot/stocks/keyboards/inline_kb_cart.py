from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def cart_product_keyboard(product_id: int, prod_cart_id: int, quantity: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="➖", callback_data=f"cart-product_[-]_{prod_cart_id}_{quantity}")
    kb.button(
        text="➕", callback_data=f"cart-product_[+]_{prod_cart_id}_{quantity}")
    kb.button(
        text="✖️", callback_data=f"cart-product-delete_{product_id}_{prod_cart_id}")
    kb.adjust(3)
    return kb.as_markup()


def product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="➖", callback_data=f"cart-product_[-]_{product_id}")
    kb.button(text="➕", callback_data=f"cart-product_[+]_{product_id}")
    kb.button(
        text="✖️", callback_data=f"cart-product-delete_{product_id}")
    kb.adjust(3)
    return kb.as_markup()


def cart_order_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Оформить заказ", callback_data="place_order")
    kb.button(text="Очистить корзину", callback_data="clear_cart")
    kb.adjust(2)
    return kb.as_markup()
