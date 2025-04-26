from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Кнопка инлайн меню", callback_data="back_home")
    kb.adjust(1)
    return kb.as_markup()


def device_brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Устройство", callback_data="device_select")
    kb.button(text="Бренд", callback_data="brand_select")
    kb.adjust(2)
    return kb.as_markup()


def device_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Смартфон", callback_data="device_Смартфон")
    kb.button(text="Планшет", callback_data="device_Планшет")
    kb.button(text="Смарт часы", callback_data="device_Смарт часы")
    kb.button(text="◀️ Назад", callback_data="device_back")
    kb.adjust(3, 1)
    return kb.as_markup()


def brand_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Apple", callback_data="brand_Apple")
    kb.button(text="Samsung", callback_data="brand_Samsung")
    kb.button(text="Demo", callback_data="brand_Демо")
    kb.button(text="◀️ Назад", callback_data="brand_back")
    kb.adjust(3, 1)
    return kb.as_markup()


def product_keyboard(product_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(
        text="В корзину",
        callback_data=f"product-cart_{product_id}"
    )
    kb.adjust(1)
    return kb.as_markup()


def search_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Переклейка дисплея", callback_data="search_re-gluing")
    kb.button(text="Замена задней крышки", callback_data="search_back_cover")
    kb.button(text="Продать битик", callback_data="search_crash-display")
    kb.button(text="Купить дисплей (восстановленный)", callback_data="search_production")
    kb.button(text="Купить дисплей (запчасть)", callback_data="search_spare-parts")
    kb.adjust(2, 1, 2)
    return kb.as_markup()

def search_keyboard_with_model(model_id: str, model_name: str = "не указана") -> InlineKeyboardMarkup:

    # Ограничиваем длину model_name для callback_data (Telegram ограничивает длину callback_data до 64 байт)
    model_name = model_name[:15] if model_name else "не указана"

    kb = InlineKeyboardBuilder()
    kb.button(text="Переклейка дисплея", callback_data=f"cart_search_re-gluing_{model_id}_{model_name}")
    kb.button(text="Замена задней крышки", callback_data=f"cart_search_back_cover_{model_id}_{model_name}")
    kb.button(text="Продать битик", callback_data=f"cart_sell_broken_{model_id}_{model_name}")
    kb.button(text="Купить дисплей (восстановленный)", callback_data=f"cart_ready_products_{model_id}_{model_name}")
    kb.button(text="Купить дисплей (запчасть)", callback_data=f"cart_spare_parts_{model_id}_{model_name}")
    kb.adjust(2, 1, 2)
    return kb.as_markup()

# def search_keyboard_with_model(model_id: str, model_name: str = "не указана") -> InlineKeyboardMarkup:

#     # Ограничиваем длину model_name для callback_data (Telegram ограничивает длину callback_data до 64 байт)
#     model_name = model_name[:15] if model_name else "не указана"

#     kb = InlineKeyboardBuilder()
#     kb.button(text="Переклейка дисплея", callback_data=f"cart_search_re-gluing_{model_id}")
#     kb.button(text="Замена задней крышки", callback_data=f"cart_search_back_cover_{model_id}")
#     kb.button(text="Продать битик", callback_data=f"cart_sell_broken_{model_id}_{model_name}")
#     kb.button(text="Купить дисплей (восстановленный)", callback_data=f"cart_ready_products_{model_id}")
#     kb.button(text="Купить дисплей (запчасть)", callback_data=f"cart_spare_parts_{model_id}")
#     kb.adjust(2, 1, 2)
#     return kb.as_markup()