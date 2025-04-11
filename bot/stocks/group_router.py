from aiogram import Router, types
from loguru import logger
import re

from bot.config import bot, target_chat_id
from bot.planfix import add_outgoing_comment_to_chat
from bot.users.dao import UserDAO

group_router = Router()

# Обработчик для сообщений в группе, которые являются ответом или цитированием
@group_router.message()
async def handle_group_reply(message: types.Message):
    # Проверяем, что сообщение отправлено в группу или супергруппу
    if message.chat.type not in ["group", "supergroup"]:
        return

    # Проверяем, что сообщение отправлено в целевую группу
    if str(message.chat.id) != str(target_chat_id):
        logger.debug(f"Сообщение в группе {message.chat.id} проигнорировано, так как target_chat_id={target_chat_id}")
        return

    # Проверяем, что это ответ на другое сообщение или цитирование
    if not message.reply_to_message and not message.quote:
        logger.debug("Сообщение в группе не является ответом и не содержит цитирования")
        return

    # Пытаемся получить user_id
    user_id = None
    target_message = None

    # Если это ответ (Reply)
    if message.reply_to_message:
        target_message = message.reply_to_message
        logger.debug("Сообщение является ответом (Reply)")

    # Если это цитирование
    elif message.quote:
        target_message = message  # Мы не можем найти оригинальное сообщение, используем само сообщение с цитатой
        logger.debug("Сообщение содержит цитирование")

    if not target_message:
        logger.debug("Не удалось найти целевое сообщение")
        return

    # Пытаемся получить user_id из forward_from
    if target_message.forward_from:
        user_id = target_message.forward_from.id
        logger.debug(f"Извлечён user_id из forward_from: {user_id}")
    else:
        # Если forward_from отсутствует, пытаемся извлечь user_id из текста сообщения
        if target_message.text:
            # Ищем user_id в формате "Входящее сообщение от {user_id}" или "Исходящее сообщение для {user_id}"
            match = re.search(r"(?:Входящее сообщение от|Исходящее сообщение для) (\d+)", target_message.text)
            if match:
                user_id = int(match.group(1))
                logger.debug(f"Извлечён user_id из текста сообщения: {user_id}")
            else:
                logger.debug("Не удалось извлечь user_id из текста сообщения")
                return
        else:
            logger.debug("Сообщение, на которое отвечают, не содержит текста")
            return

    if not user_id:
        logger.debug("Не удалось определить user_id")
        return

    # Извлекаем только текст ответа (без цитирования)
    reply_text = message.text if message.text else "Сообщение без текста"

    logger.info(f"Получен ответ в группе от {message.from_user.id} для пользователя {user_id}: {reply_text}")

    # Отправляем ответ пользователю в личный чат (без цитирования)
    try:
        await bot.send_message(
            chat_id=user_id,
            text=reply_text
        )
        logger.info(f"Ответ отправлен пользователю {user_id}: {reply_text}")
        await message.answer(f"Ответ успешно отправлен пользователю {user_id}.")
    except Exception as e:
        logger.error(f"Не удалось отправить ответ пользователю {user_id}: {e}")
        await message.answer(f"Ошибка: не удалось отправить ответ пользователю {user_id}.")

    # Добавляем комментарий в Planfix (только сам ответ)
    user_data = await UserDAO.find_one_or_none(telegram_id=user_id)
    if user_data and user_data.chat_pf_id:
        success = await add_outgoing_comment_to_chat(
            chat_pf_id=user_data.chat_pf_id,
            comment=reply_text
        )
        if success:
            logger.info(f"Комментарий добавлен в Planfix для пользователя {user_id}")
        else:
            logger.error(f"Не удалось добавить комментарий в Planfix для пользователя {user_id}")
            await message.answer(f"Ошибка: не удалось добавить комментарий в Planfix для пользователя {user_id}.")
    else:
        logger.warning(f"У пользователя {user_id} нет chat_pf_id")
        await message.answer(f"Ошибка: у пользователя {user_id} нет активного чата в Planfix.")