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


def aiagent_cart_keyboard(model_id: int, model_name: str, operation: str, task_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="В корзину",
        callback_data=f"aiagent-cart_{model_id}_{model_name}_{operation}_{task_id}"
    )
    kb.adjust(1)
    return kb.as_markup()


def search_aiagent_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Цена переклейки", callback_data="search_aiagent_re-gluing")
    kb.button(text="Продать битик", callback_data="search_aiagent_crash-display")
    kb.button(text="Готовая продукция", callback_data="search_aiagent_production")
    kb.button(text="Запчасти", callback_data="search_aiagent_spare-parts")
    kb.adjust(2, 2)
    return kb.as_markup()

def cart_aiagent_product_keyboard(product_id: int, prod_cart_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    # kb.button(
    #     text="➖", callback_data=f"cart-product_[-]_{prod_cart_id}_{quantity}")
    # kb.button(
    #     text="➕", callback_data=f"cart-product_[+]_{prod_cart_id}_{quantity}")
    kb.button(
        text="✖️ Удалить из корзины", callback_data=f"cart-aiagent-product-delete_{product_id}_{prod_cart_id}")
    kb.adjust(1)
    return kb.as_markup()


def re_gluing_cart_keyboard(model_id: int, model_name: str, operation: str, task_id: str, price: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="В корзину",
        callback_data=f"re-gluing-cart_{model_id}_{model_name}_{operation}_{task_id}_{price}"
    )
    kb.adjust(1)
    return kb.as_markup()