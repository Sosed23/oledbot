import re
from aiogram import Router, F, types
from loguru import logger

from bot.config import target_chat_id

group_router = Router()

@group_router.message(F.chat.id == target_chat_id)
async def handle_group_message(message: types.Message):
    # Проверяем, является ли сообщение ответом на другое сообщение
    if message.reply_to_message and message.reply_to_message.text and "Входящее сообщение от" in message.reply_to_message.text:
        try:
            # Извлекаем user_id из текста с помощью регулярного выражения
            # Формат: "Входящее сообщение от 2011633414 (@myvmeste2023)"
            user_info = message.reply_to_message.text
            match = re.search(r"Входящее сообщение от (\d+)", user_info)
            if not match:
                result = await message.reply("Ошибка: не удалось извлечь user_id из пересланного сообщения.")
                return result

            user_id = int(match.group(1))  # Извлекаем user_id

            # Убедимся, что user_id — это ID пользователя (положительное число)
            if user_id < 0:
                result = await message.reply("Ошибка: это сообщение было переслано не от пользователя.")
                return result

            # Получаем текст ответа
            reply_text = message.text

            # Отправляем сообщение пользователю
            await message.bot.send_message(
                chat_id=user_id,
                text=reply_text
            )
            logger.info(f"Сообщение от группы переслано пользователю {user_id}: {reply_text}")
            result = await message.reply(f"Сообщение отправлено пользователю {user_id}.")
            return result

        except ValueError:
            result = await message.reply("Ошибка: не удалось извлечь user_id из пересланного сообщения.")
            return result
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю: {e}")
            result = await message.reply(f"Ошибка при отправке: {e}")
            return result
    else:
        # Если это не ответ на пересланное сообщение, возвращаем инструкцию
        result = await message.reply("Пожалуйста, используйте функцию 'Ответить' на пересланное сообщение пользователя.")
        return result