import asyncio
from aiogram import types
from aiogram.filters import Command
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from loguru import logger

from bot.config import bot, admins, dp, target_chat_id
from bot.users.router import user_router
from bot.stocks.router_product import product_router
from bot.stocks.router_cart import cart_router
from bot.stocks.router_search import search_router
from bot.stocks.router_order import order_router
from bot.stocks.router_aiagent import aiagent_router
from bot.stocks.group_router import group_router

# Middleware для пересылки входящих сообщений (от пользователя к боту)
class ForwardIncomingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message, data: dict):
        try:
            if event.chat.type == "private":  # Только для личных чатов
                user_id = event.from_user.id
                username = event.from_user.username if event.from_user.username else "None"
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
        except Exception as e:
            logger.error(f"Ошибка при пересылке входящего сообщения: {e}")

        # Передаём управление дальше (чтобы другие обработчики сработали)
        return await handler(event, data)

# Middleware для пересылки исходящих сообщений (от бота к пользователю)
class ForwardOutgoingMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        # Логируем начало работы middleware
        if isinstance(event, types.Message):
            logger.debug(f"Исходящее middleware вызвано для события: {event.text}")
        elif isinstance(event, types.CallbackQuery):
            logger.debug(f"Исходящее middleware вызвано для callback: {event.data}")

        # Вызываем обработчик
        result = await handler(event, data)

        # Логируем результат обработчика
        logger.debug(f"Результат обработчика: {result}")

        # Если результат — None, пропускаем пересылку
        if result is None:
            logger.debug("Результат обработчика — None, пересылка не требуется.")
            return result

        try:
            # Если результат — это одно сообщение
            if isinstance(result, types.Message):
                user_info = f"Исходящее сообщение для {result.chat.id} (@{result.chat.username})"
                logger.info(f"Пересылаем исходящее сообщение: {result.text}")
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
            # Если результат — это список сообщений
            elif isinstance(result, list) and all(isinstance(msg, types.Message) for msg in result):
                for msg in result:
                    user_info = f"Исходящее сообщение для {msg.chat.id} (@{msg.chat.username})"
                    logger.info(f"Пересылаем исходящее сообщение: {msg.text}")
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
            logger.error(f"Ошибка при пересылке исходящего сообщения: {e}")

        return result

# Функция, которая настроит командное меню (дефолтное для всех пользователей)
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

async def main():
    # Регистрация middleware для входящих сообщений
    dp.message.middleware(ForwardIncomingMessageMiddleware())
    # Регистрация middleware для исходящих сообщений (для Message)
    dp.message.outer_middleware(ForwardOutgoingMessageMiddleware())
    # Регистрация middleware для исходящих сообщений (для CallbackQuery)
    dp.callback_query.outer_middleware(ForwardOutgoingMessageMiddleware())

    # Регистрация роутеров
    dp.include_router(user_router)
    dp.include_router(product_router)
    dp.include_router(cart_router)
    dp.include_router(search_router)
    dp.include_router(order_router)
    dp.include_router(aiagent_router)
    dp.include_router(group_router)

    # Регистрация функций
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    # Запуск бота в режиме long polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа была прервана")