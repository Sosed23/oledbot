from aiogram.filters import CommandObject, CommandStart
from loguru import logger
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from bot.users.dao import UserDAO
from bot.users.utils import get_refer_id_or_none
from bot.users.keyboards import markup_kb

user_router = Router()


@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    try:
        user_id = message.from_user.id
        user_info = await UserDAO.find_one_or_none(telegram_id=user_id)

        if user_info:
            await message.answer(f"👋 Привет, {message.from_user.full_name}! Выберите необходимое действие",
                                 reply_markup=markup_kb.back_keyboard())
            return

        # Добавление нового пользователя
        await UserDAO.add(
            telegram_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        await message.answer()

    except Exception as e:
        logger.error(
            f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")
