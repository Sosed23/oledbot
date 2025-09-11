from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import select, text
from bot.database import async_session_maker
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup  # Импортируем BeautifulSoup для удаления HTML-тегов
from typing import List, Optional
from pathlib import Path

from bot.config import bot  # Импортируем уже созданный объект bot
from bot.stocks.dao import OrderDAO, OrderStatusHistoryDAO, CartDAO

OPERATION_NAMES = {}

# Инициализация FastAPI
app = FastAPI()


# Mount static files
app.mount("/static", StaticFiles(directory="bot/static"), name="static")

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open(Path(__file__).parent / "static" / "index.html", "r", encoding="utf-8") as f:
        return f.read()

# Old endpoints (for backward compatibility)
@app.get("/api/devices")
async def get_devices():
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM devices ORDER BY name"))
        devices = [row[0] for row in result.fetchall()]
        return {"devices": devices}

@app.get("/api/brands/{device}")
async def get_brands(device: str):
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM brands ORDER BY name"))
        brands = [row[0] for row in result.fetchall()]
        return {"brands": brands}

@app.get("/api/series/{device}/{brand}")
async def get_series(device: str, brand: str):
    sql = "SELECT DISTINCT s.name FROM series s JOIN devices d ON s.device_id = d.id JOIN brands b ON s.brand_id = b.id WHERE d.name = :device AND b.name = :brand ORDER BY s.name"
    async with async_session_maker() as session:
        result = await session.execute(text(sql), {"device": device, "brand": brand})
        series = [row[0] for row in result.fetchall()]
        return {"series": series}

@app.get("/api/models/{device}/{brand}/{series}")
async def get_models(device: str, brand: str, series: str):
    sql = """
    SELECT d.name as device, b.name as brand, s.name as series, mn.name, mn.model_id
    FROM models_new mn
    JOIN devices d ON mn.device_id = d.id
    JOIN brands b ON mn.brand_id = b.id
    JOIN series s ON mn.series_id = s.id
    WHERE d.name = :device AND b.name = :brand AND s.name = :series
    ORDER BY mn.name
    """
    async with async_session_maker() as session:
        result = await session.execute(text(sql), {"device": device, "brand": brand, "series": series})
        models = []
        for row in result.fetchall():
            models.append({
                "device": row[0],
                "brand": row[1],
                "series": row[2],
                "name": row[3],
                "model_id": row[4]
            })
        return {"models": models}

# New endpoints (for web app with multiple selection)
@app.get("/api/v2/devices")
async def get_devices_v2():
    """Return list of all available devices"""
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM devices ORDER BY name"))
        devices = [row[0] for row in result.fetchall()]
        return {"devices": devices}

@app.get("/api/v2/brands")
async def get_brands_v2():
    """Return list of all available brands"""
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM brands ORDER BY name"))
        brands = [row[0] for row in result.fetchall()]
        return {"brands": brands}

@app.get("/api/v2/series")
async def get_series_v2(
    devices: List[str] = Query(None, description="Filter series by devices"),
    brands: List[str] = Query(None, description="Filter series by brands")
):
    """
    Return list of series, optionally filtered by devices and brands.
    Supports multiple selection for both devices and brands.
    """
    sql = "SELECT DISTINCT s.name FROM series s JOIN devices d ON s.device_id = d.id JOIN brands b ON s.brand_id = b.id WHERE 1=1"
    params = {}
    if devices:
        sql += " AND d.name = ANY(:devices)"
        params['devices'] = devices
    if brands:
        sql += " AND b.name = ANY(:brands)"
        params['brands'] = brands
    sql += " ORDER BY s.name"
    async with async_session_maker() as session:
        result = await session.execute(text(sql), params)
        series = [row[0] for row in result.fetchall()]
        return {"series": series}

@app.get("/api/v2/models")
async def get_models_v2(
    devices: List[str] = Query(None, description="Filter models by devices"),
    brands: List[str] = Query(None, description="Filter models by brands"),
    series: List[str] = Query(None, description="Filter models by series")
):
    """
    Return list of models, optionally filtered by devices, brands and series.
    Supports multiple selection for all parameters.
    """
    sql = """
    SELECT d.name as device, b.name as brand, s.name as series, mn.name, mn.model_id
    FROM models_new mn
    JOIN devices d ON mn.device_id = d.id
    JOIN brands b ON mn.brand_id = b.id
    JOIN series s ON mn.series_id = s.id
    WHERE 1=1
    """
    params = {}
    if devices:
        sql += " AND d.name = ANY(:devices)"
        params['devices'] = devices
    if brands:
        sql += " AND b.name = ANY(:brands)"
        params['brands'] = brands
    if series:
        sql += " AND s.name = ANY(:series)"
        params['series'] = series
    sql += " ORDER BY mn.name"
    async with async_session_maker() as session:
        result = await session.execute(text(sql), params)
        models = []
        for row in result.fetchall():
            models.append({
                "device": row[0],
                "brand": row[1],
                "series": row[2],
                "name": row[3],
                "model_id": row[4]
            })
        return {"models": models}

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

@app.get("/api/v2/orders")
async def get_orders_v2(telegram_id: int = Query(..., description="Telegram ID of the user")):
    """
    Return list of orders for a specific user by telegram_id.
    """
    try:
        my_orders = await OrderDAO.find_all(telegram_id=telegram_id)
        orders_data = []
        for order in my_orders:
            status_history = await OrderStatusHistoryDAO.find_all(order_id=order.id)
            last_status = sorted(status_history, key=lambda x: x.timestamp, reverse=True)[0].status if status_history else order.status or "Неизвестно"
            
            order_items = order.items
            grouped_items = {}
            for item in order_items:
                operation_id = int(item.operation) if isinstance(item.operation, (int, str)) and str(item.operation).isdigit() else item.operation
                operation_name = OPERATION_NAMES.get(operation_id, f"Операция {operation_id}")
                if operation_name not in grouped_items:
                    grouped_items[operation_name] = []
                grouped_items[operation_name].append({
                    "product_name": item.product_name,
                    "price": item.price
                })
 
            items_data = []
            for operation, items in grouped_items.items():
                for item in items:
                    items_data.append(f"   🔹 {item['product_name']} 💰 Цена: {item['price']} руб.")
            
            order_info = {
                "id": order.id,
                "status": last_status,
                "total_amount": order.total_amount,
                "items": items_data
            }
            orders_data.append(order_info)
         
        return {"orders": orders_data}
    except Exception as e:
        logger.error(f"Error fetching orders for telegram_id={telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching orders")