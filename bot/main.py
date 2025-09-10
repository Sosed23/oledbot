import asyncio
from contextlib import asynccontextmanager
import uvicorn
from aiogram import types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from loguru import logger
import re

from bot.config import bot, admins, dp, target_chat_id
from bot.users.router import user_router
from bot.stocks.router_product import product_router
from bot.stocks.router_cart import cart_router
from bot.stocks.router_search import search_router
from bot.stocks.router_order import order_router
from bot.stocks.router_aiagent import aiagent_router
from bot.stocks.group_router import group_router
from bot.stocks.router_web_filter import web_filter_router
from bot.webhook import app as fastapi_app  # Импортируем FastAPI-приложение
from bot.planfix import add_incoming_comment_to_chat, add_outgoing_comment_to_chat
from bot.users.dao import UserDAO

def strip_html(text: str) -> str:
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

# Middleware для пересылки входящих сообщений (от пользователя к боту)
class ForwardIncomingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        if event.web_app_data:
            logger.debug(f"web_app_data received: {event.web_app_data.data}")
            # For web_app_data, directly call handler and return its result to allow dp processing
            return await handler(event, data)

        try:
            if event.chat.type == "private" and event.text is not None:  # Только для личных чатов с текстом (skip web_app_data forwarding)
                user_id = event.from_user.id
                username = event.from_user.username if event.from_user.username else "None"
                message_text = event.text

                # Список кнопок меню, для которых пропускаем Planfix
                menu_buttons = [
                    "✨ Поиск с ИИ",
                    "🛒 Корзина",
                    "🔍 Поиск модели",
                    "🗂 Мои заказы",
                    "Фильтр моделей"
                ]

                is_menu_button = message_text in menu_buttons

                # Пересылаем сообщение в группу Telegram
                logger.debug(f"Пересылка входящего сообщения в Telegram-группу: user_id={user_id}, username={username}, is_menu={is_menu_button}")
                user_info = f"Входящее сообщение от {user_id} (@{username})"
                await bot.send_message(
                    chat_id=target_chat_id,
                    text=user_info
                )
                await bot.forward_message(
                    chat_id=target_chat_id,
                    from_chat_id=event.chat.id,
                    message_id=event.message_id
                )
                logger.info(f"{user_info} переслано в {target_chat_id}")

                # Пропускаем проверку chat_pf_id для команды /start и кнопок меню
                if message_text.startswith("/start") or is_menu_button:
                    logger.debug(f"Команда /start или меню-кнопка, пропускаем проверку chat_pf_id для пользователя {user_id}")
                else:
                    # Получаем данные пользователя через DAO
                    logger.debug(f"Получение данных пользователя: telegram_id={user_id}")
                    user_data = await UserDAO.find_one_or_none(telegram_id=user_id)
                    if user_data and user_data.chat_pf_id:
                        logger.debug(f"Данные пользователя: chat_pf_id={user_data.chat_pf_id}, contact_pf_id={user_data.contact_pf_id}")
                        success = await add_incoming_comment_to_chat(
                            chat_pf_id=user_data.chat_pf_id,
                            contact_pf_id=user_data.contact_pf_id,
                            comment=message_text
                        )
                        if not success:
                            logger.error(f"Не удалось добавить комментарий в Planfix для пользователя {user_id}")
                            # Не блокируем обработку, логируем
                    else:
                        logger.warning(f"У пользователя {user_id} нет chat_pf_id для пользовательского сообщения '{message_text}'")

        except Exception as e:
            logger.error(f"Ошибка при пересылке входящего сообщения: {e}")

        # Всегда передаём управление дальше
        logger.debug("Calling handler from middleware")
        handler_result = await handler(event, data)
        return handler_result

# Middleware для пересылки исходящих сообщений (от бота к пользователю) в Planfix и Telegram-группу
class ForwardOutgoingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        if isinstance(event, types.Message):
            logger.debug(f"Исходящее middleware вызвано для события: {event.text}")
        elif isinstance(event, types.CallbackQuery):
            logger.debug(f"Исходящее middleware вызвано для callback: {event.data}")

        result = await handler(event, data)
        logger.debug(f"Результат обработчика: {result}")

        if result is None:
            logger.debug("Результат обработчика — None, обработка не требуется.")
            return result

        try:
            if isinstance(result, types.Message):
                user_id = result.chat.id
                username = result.chat.username if result.chat.username else "None"
                message_text = result.text if result.text else "Сообщение без текста"

                logger.debug(f"Перехват исходящего сообщения: {message_text} для пользователя {user_id}")

                # Очищаем HTML перед отправкой в Planfix
                clean_message_text = strip_html(message_text)

                logger.info(f"Обрабатываем исходящее сообщение: {clean_message_text}")
                user_data = await UserDAO.find_one_or_none(telegram_id=user_id)
                if user_data and user_data.chat_pf_id:
                    success = await add_outgoing_comment_to_chat(
                        chat_pf_id=user_data.chat_pf_id,
                        comment=clean_message_text
                    )
                    if not success:
                        logger.error(f"Не удалось добавить исходящий комментарий в Planfix для пользователя {user_id}")
                    else:
                        logger.info(f"Исходящий комментарий добавлен в Planfix для пользователя {user_id}")
                else:
                    logger.warning(f"У пользователя {user_id} нет chat_pf_id")

                user_info = f"Исходящее сообщение для {user_id} (@{username})"
                await bot.send_message(
                    chat_id=target_chat_id,
                    text=user_info
                )
                await bot.forward_message(
                    chat_id=target_chat_id,
                    from_chat_id=result.chat.id,
                    message_id=result.message_id
                )
                logger.info(f"{user_info} переслано в {target_chat_id}")

            elif isinstance(result, list) and all(isinstance(msg, types.Message) for msg in result):
                for msg in result:
                    user_id = msg.chat.id
                    username = msg.chat.username if msg.chat.username else "None"
                    message_text = msg.text if msg.text else "Сообщение без текста"

                    logger.debug(f"Перехват исходящего сообщения: {message_text} для пользователя {user_id}")

                    # Очищаем HTML перед отправкой в Planfix
                    clean_message_text = strip_html(message_text)

                    logger.info(f"Обрабатываем исходящее сообщение: {clean_message_text}")
                    user_data = await UserDAO.find_one_or_none(telegram_id=user_id)
                    if user_data and user_data.chat_pf_id:
                        success = await add_outgoing_comment_to_chat(
                            chat_pf_id=user_data.chat_pf_id,
                            comment=clean_message_text
                        )
                        if not success:
                            logger.error(f"Не удалось добавить исходящий комментарий в Planfix для пользователя {user_id}")
                        else:
                            logger.info(f"Исходящий комментарий добавлен в Planfix для пользователя {user_id}")
                    else:
                        logger.warning(f"У пользователя {user_id} нет chat_pf_id")

                    user_info = f"Исходящее сообщение для {user_id} (@{username})"
                    await bot.send_message(
                        chat_id=target_chat_id,
                        text=user_info
                    )
                    await bot.forward_message(
                        chat_id=target_chat_id,
                        from_chat_id=msg.chat.id,
                        message_id=msg.message_id
                    )
                    logger.info(f"{user_info} переслано в {target_chat_id}")

            else:
                logger.warning(f"Результат не является сообщением или списком сообщений: {type(result)}")
        except Exception as e:
            logger.error(f"Ошибка при обработке исходящего сообщения: {e}")

        return result

# Функция, которая настроит командное меню
async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

# Функция, которая выполнится когда бот запустится
async def start_bot():
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except:
            pass
    logger.info("Бот успешно запущен.")

# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
    logger.error("Бот остановлен!")

# Функция для запуска бота и FastAPI
async def run_all():
    # Запускаем polling для бота
    logger.info("Starting bot polling...")
    bot_task = asyncio.create_task(dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()))

    # Запускаем FastAPI-сервер
    logger.info("Starting FastAPI server...")
    config = uvicorn.Config(fastapi_app, host="0.0.0.0", port=1111, log_level="info")
    server = uvicorn.Server(config)
    fastapi_task = asyncio.create_task(server.serve())

    # Ожидаем завершения обеих задач
    await asyncio.gather(bot_task, fastapi_task)

# Функция для регистрации роутеров и middleware
def setup_bot():
    dp.message.middleware(ForwardIncomingMessageMiddleware())
    dp.message.outer_middleware(ForwardOutgoingMessageMiddleware())
    dp.callback_query.outer_middleware(ForwardOutgoingMessageMiddleware())

    @dp.message(F.web_app_data)
    async def direct_web_app_handler(message: types.Message):
        logger.info(f"direct_web_app_handler called for message from user {message.from_user.id}")
        try:
            logger.info("Direct dp handler triggered for web_app_data")
            logger.info(f"Received web_app_data raw: {message.web_app_data.data}")
            import json
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            data = json.loads(message.web_app_data.data)
            logger.info(f"Parsed data: {data}")
            action = data.get('action')
            logger.info(f"Action: {action}")
            if action == 'select_model':
                logger.info("Processing 'select_model' action")
                model_name = data.get('name', '')
                model_id = data.get('model_id', '')
                logger.info(f"Model name: {model_name}, model_id: {model_id}")
                if model_id is None:
                    logger.error("model_id is None in select_model action")
                    await message.answer("Ошибка: ID модели не указан.")
                    return
                kb = InlineKeyboardBuilder()
                model_name_safe = model_name.replace(' ', '_')
                kb.button(text="Переклейка дисплея", callback_data=f"cart_web_re-gluing_{model_id}_{model_name_safe}")
                kb.button(text="Замена задней крышки", callback_data=f"cart_web_back_cover_{model_id}_{model_name_safe}")
                kb.button(text="Продать битик", callback_data=f"cart_web_sell_broken_{model_id}_{model_name_safe}")
                kb.button(text="Купить дисплей (восстановленный)", callback_data=f"cart_web_ready_products_{model_id}_{model_name_safe}")
                kb.button(text="Купить дисплей (запчасть)", callback_data=f"cart_web_spare_parts_{model_id}_{model_name_safe}")
                kb.adjust(2, 1, 2)
                markup = kb.as_markup()
                text = f"Выберете нужную опцию для модели: {model_name}"
                response = await message.answer(
                    text,
                    reply_markup=markup
                )
                logger.info(f"Sent message to user {message.from_user.id}: text='{text}', keyboard with {len(markup.inline_keyboard)} buttons")
                return response
            elif action == 'open':
                logger.info("Processing 'open' action")
                await message.answer("Вы успешно передали данные боту кнопкой «Фильтр моделей».")
                return
            else:
                logger.warning(f"Unknown action in web_app_data: {action}")
                await message.delete()
                logger.info("Deleted message for unknown action")
                return
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in web_app_data: {e}")
            await message.answer("Ошибка обработки данных из Web App.")
        except Exception as e:
            logger.error(f"Error in direct_web_app_handler: {e}")
            await message.answer("Error processing web_app_data")

    # Удаляем debug_all_messages, так как он дублирует логику

    dp.include_router(user_router)
    dp.include_router(product_router)
    dp.include_router(cart_router)
    dp.include_router(search_router)
    dp.include_router(order_router)
    dp.include_router(aiagent_router)
    dp.include_router(group_router)
    dp.include_router(web_filter_router)
    logger.info("web_filter_router included successfully")

    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

if __name__ == "__main__":
    setup_bot()
    asyncio.run(run_all())