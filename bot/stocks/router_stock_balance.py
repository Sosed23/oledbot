from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.planfix import planfix_stock_balance

stock_router = Router()

# Количество результатов на одной странице
RESULTS_PER_PAGE = 50


@stock_router.message(F.text == '📋 Просмотр остатков')
async def stockbalance(message: Message):
    all_stock = await planfix_stock_balance()

    for product_name, stock_balance in all_stock:
        await message.answer(f'{product_name} | Остаток: {stock_balance} шт.')


@stock_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()
    offset = int(inline_query.offset) if inline_query.offset else 0

    # Получаем список товаров в зависимости от текста запроса
    if query_text == "":  # Если запрос пустой, показываем все товары
        products = await planfix_stock_balance()
    else:  # Если запрос содержит текст, ищем товары по имени
        products = await planfix_stock_balance(query_text)

    # Ограничиваем результаты текущей страницей
    page_products = products[offset:offset + RESULTS_PER_PAGE]

    # Преобразуем результаты в список InlineQueryResult
    results = [
        InlineQueryResultArticle(
            id=str(offset + index),
            title=f"{product_name} - {stock_balance}",
            input_message_content=InputTextMessageContent(
                message_text=f"{product_name}: {stock_balance} шт."
            ),
            description=f"Доступно на складе: {stock_balance} шт."
        )
        for index, (product_name, stock_balance) in enumerate(page_products)
    ]

    # Определяем, есть ли следующая страница
    next_offset = str(
        offset + RESULTS_PER_PAGE) if len(products) > offset + RESULTS_PER_PAGE else ""

    # Отправляем результаты в ответ на инлайн-запрос с учетом пагинации
    await inline_query.answer(results, cache_time=1, next_offset=next_offset)


# Создаем кнопку, которая запускает инлайн-режим в текущем чате
inline_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Поиск товара",
                # Пустая строка запускает инлайн-режим в текущем чате
                switch_inline_query_current_chat=""
            )
        ]
    ]
)

# Отправляем сообщение с кнопкой


@stock_router.message(F.text == '📋 Поиск товара')
async def send_search_button(message: Message):
    await message.answer("Нажмите на кнопку для поиска товара:", reply_markup=inline_button)
