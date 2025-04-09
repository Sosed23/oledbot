from aiogram.filters import CommandObject, CommandStart
from loguru import logger
from aiogram.types import Message
from aiogram.dispatcher.router import Router
from bot.users.dao import UserDAO
from bot.users.keyboards import markup_kb
from bot.planfix import planfix_create_contact, planfix_create_chat

user_router = Router()

@user_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    try:
        user_id = message.from_user.id
        user_info = await UserDAO.find_one_or_none(telegram_id=user_id)

        if user_info:
            result = await message.answer(
                f"👋 Привет, {message.from_user.full_name}! Выберите необходимое действие",
                reply_markup=markup_kb.back_keyboard()
            )
            return result

        # Добавление нового пользователя
        await UserDAO.add(
            telegram_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        # Создание контакта в Planfix, если он ещё не существует
        data_contact = await planfix_create_contact(
            telegram_id=user_id,
            username=message.from_user.username or "Unknown",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )

        contact_pf_id = data_contact['id']

        if not data_contact:
            logger.error(f"Не удалось создать контакт в Planfix для пользователя {user_id}")
            await message.answer("Произошла ошибка при регистрации в Planfix. Пожалуйста, попробуйте снова позже.")
            return

        await UserDAO.update(
            {"telegram_id": user_id},
            contact_pf_id=contact_pf_id
        )

        
        data_chat = await planfix_create_chat(contact_pf_id=contact_pf_id)

        chat_pf_id = data_chat['id']

        await UserDAO.update(
            {"telegram_id": user_id},
            chat_pf_id=chat_pf_id
        )

        result = await message.answer(
            f"👋 Привет, {message.from_user.full_name}! Вы успешно зарегистрированы. Выберите необходимое действие.",
            reply_markup=markup_kb.back_keyboard()
        )
        return result

    except Exception as e:
        logger.error(
            f"Ошибка при выполнении команды /start для пользователя {message.from_user.id}: {e}")
        result = await message.answer("Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте снова позже.")
        return result