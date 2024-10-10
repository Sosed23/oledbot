from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.dispatcher.router import Router


stock_router = Router()


@stock_router.inline_query()
async def inline_show_categories(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    if query_text == "":  # Если запрос пустой, показываем категории
        results = [
            InlineQueryResultArticle(
                id="category_1",
                title="Категория 1",
                input_message_content=InputTextMessageContent(
                    message_text="Вы выбрали категорию 1"
                ),
                description="Описание категории 1",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Посмотреть товары", callback_data="category_1")]
                ])
            )
        ]
    else:  # Если запрос содержит текст, например, поиск товаров
        results = [
            InlineQueryResultArticle(
                id="product_1",
                title="Товар 1",
                input_message_content=InputTextMessageContent(
                    message_text="Товар 1"
                ),
                description="Цена товара 1",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text="Купить товар", callback_data="product_1")]
                ])
            )
        ]

    # Отправляем результаты инлайн-запроса
    await inline_query.answer(results, cache_time=1)
