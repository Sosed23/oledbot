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

        # Если пользователь уже есть в базе, проверяем наличие chat_pf_id
        if user_info:
            if user_info.chat_pf_id:
                # Если chat_pf_id есть, просто приветствуем пользователя
                result = await message.answer(
                    f"👋 Привет, {message.from_user.full_name}! Выберите необходимое действие",
                    reply_markup=markup_kb.back_keyboard(user_id=user_id)
                )
                return result
            else:
                # Если chat_pf_id нет, пытаемся создать чат
                logger.warning(f"У пользователя {user_id} отсутствует chat_pf_id. Пытаемся создать чат в Planfix...")
                data_chat = await planfix_create_chat(contact_pf_id=user_info.contact_pf_id)
                if data_chat and 'id' in data_chat:
                    chat_pf_id = data_chat['id']
                    await UserDAO.update(
                        {"telegram_id": user_id},
                        chat_pf_id=chat_pf_id
                    )
                    logger.info(f"Чат в Planfix успешно создан для пользователя {user_id}: chat_pf_id={chat_pf_id}")
                    result = await message.answer(
                        f"👋 Привет, {message.from_user.full_name}! Чат в Planfix создан. Выберите необходимое действие.",
                        reply_markup=markup_kb.back_keyboard(user_id=user_id)
                    )
                    return result
                else:
                    logger.error(f"Не удалось создать чат в Planfix для пользователя {user_id}: {data_chat}")
                    result = await message.answer(
                        "Произошла ошибка при создании чата в Planfix. Пожалуйста, попробуйте снова позже или обратитесь в поддержку."
                    )
                    return result

        # Добавление нового пользователя
        await UserDAO.add(
            telegram_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

        # Создание контакта в Planfix
        data_contact = await planfix_create_contact(
            telegram_id=user_id,
            username=message.from_user.username or "Unknown",
            first_name=message.from_user.first_name or "",
            last_name=message.from_user.last_name or ""
        )

        if not data_contact or 'id' not in data_contact:
            logger.error(f"Не удалось создать контакт в Planfix для пользователя {user_id}: {data_contact}")
            await message.answer("Произошла ошибка при регистрации в Planfix. Пожалуйста, попробуйте снова позже.")
            return

        contact_pf_id = data_contact['id']
        await UserDAO.update(
            {"telegram_id": user_id},
            contact_pf_id=contact_pf_id
        )

        # Создание чата в Planfix
        data_chat = await planfix_create_chat(contact_pf_id=contact_pf_id)
        if not data_chat or 'id' not in data_chat:
            logger.error(f"Не удалось создать чат в Planfix для пользователя {user_id}: {data_chat}")
            await message.answer("Произошла ошибка при создании чата в Planfix. Пожалуйста, попробуйте снова позже.")
            return

        chat_pf_id = data_chat['id']
        await UserDAO.update(
            {"telegram_id": user_id},
            chat_pf_id=chat_pf_id
        )

        result = await message.answer(
            f"👋 Привет, {message.from_user.full_name}! Вы успешно зарегистрированы. Выберите необходимое действие.",
            reply_markup=markup_kb.back_keyboard(user_id=user_id)
        )
        return result
    except Exception as e:
        logger.error(f"Произошла ошибка в /start: {e}")
        await message.answer("Произошла непредвиденная ошибка. Пожалуйста, попробуйте снова позже.")