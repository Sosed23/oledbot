from aiogram import Router, F
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, Message
from bot.planfix import planfix_stock_balance

stock_router = Router()


@stock_router.message(F.text == '📋 Просмотр остатков')
async def stock_balance(message: Message):
    all_balance = planfix_stock_balance()

    all_balance_tasks = all_balance['tasks']

    for task in all_balance_tasks:
        for custom_field in task['customFieldData']:
            if custom_field['field']['id'] == 12116:
                stock_balance = custom_field['value']
                await message.answer(f'{stock_balance}')


@stock_router.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    query_text = inline_query.query.strip()

    if query_text == "":
        results = [
            InlineQueryResultArticle(
                id="1",
                title="Stock Information",
                input_message_content=InputTextMessageContent(
                    message_text="Запрос информации по товарам"
                ),
                description="Placeholder: информация по stock"
            )
        ]
    else:
        results = [
            InlineQueryResultArticle(
                id="2",
                title=f"Результат для {query_text}",
                input_message_content=InputTextMessageContent(
                    message_text=f"Вы искали: {query_text}"
                ),
                description=f"Результат поиска для '{query_text}'"
            )
        ]

    await inline_query.answer(results, cache_time=1)
