from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup  # Импортируем BeautifulSoup для удаления HTML-тегов

from bot.config import bot  # Импортируем уже созданный объект bot

# Инициализация FastAPI
app = FastAPI()

# Модель для входящих данных от Planfix
class PlanfixComment(BaseModel):
    task_id: str
    comment: str
    telegram_id: str  # Telegram ID пользователя, которому нужно отправить сообщение

# Функция для удаления HTML-тегов и форматирования текста для Telegram
def strip_html_tags(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "html.parser")
    
    formatted_text = []
    for element in soup.children:
        if element.name == "blockquote":
            # Для <blockquote> оборачиваем текст в тег <blockquote> для Telegram
            block_text = element.get_text(separator="\n").strip()
            formatted_text.append(f"<blockquote>{block_text}</blockquote>")
        else:
            # Для остальных элементов просто добавляем текст
            text = element.get_text(separator="\n").strip()
            if text:
                formatted_text.append(text)

    # Объединяем все части с одиночным переносом строки
    return "\n".join(filter(None, formatted_text)).strip()

# Эндпоинт для получения комментариев от Planfix
@app.post("/planfix/webhook")
async def planfix_webhook(request: Request):
    body = await request.json()
    logger.info(f"Received raw webhook from Planfix: {body}")
    try:
        comment = PlanfixComment(**body)
        logger.info(f"Parsed webhook from Planfix: {comment}")
        
        # Удаляем HTML-теги и форматируем текст
        clean_comment = strip_html_tags(comment.comment)
        logger.info(f"Cleaned comment: {clean_comment}")
        
        # Проверяем, что комментарий не пустой
        if not clean_comment:
            logger.warning(f"Пустой комментарий в вебхуке от Planfix для telegram_id={comment.telegram_id}, пропускаем отправку")
            return {"status": "skipped", "message": "Empty comment"}

        logger.info(f"Sending message to Telegram ID: {comment.telegram_id}")
        # Используем parse_mode="HTML" для поддержки <blockquote>
        await bot.send_message(chat_id=comment.telegram_id, text=clean_comment, parse_mode="HTML")
        logger.info(f"Comment from Planfix (task_id={comment.task_id}) sent to Telegram user {comment.telegram_id}")
        return {"status": "success", "message": "Comment sent to Telegram"}
    except Exception as e:
        logger.error(f"Error processing Planfix webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing webhook: {str(e)}")

# Тестовый эндпоинт для проверки работы сервера (GET)
@app.get("/")
async def root():
    logger.info("Received GET request to root endpoint")
    return {"message": "FastAPI server is running"}