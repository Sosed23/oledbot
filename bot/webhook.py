from fastapi import FastAPI, HTTPException, Request, Query
import json
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import json
from pydantic import BaseModel
from loguru import logger
from bs4 import BeautifulSoup  # Импортируем BeautifulSoup для удаления HTML-тегов
from typing import List, Optional

from bot.config import bot  # Импортируем уже созданный объект bot

# Инициализация FastAPI
app = FastAPI()

# Path to the filters JSON files
FILTERS_PATH = Path(__file__).parent / "stocks" / "filters.json"
NEW_FILTERS_PATH = Path(__file__).parent / "stocks" / "new_filters.json"

# Load old filters data (for backward compatibility)
def load_filters():
    try:
        with open(FILTERS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Filters file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON in filters file")

# Load new filters data
def load_new_filters():
    try:
        with open(NEW_FILTERS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="New filters file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid JSON in new filters file")

filters_data = load_filters()
new_filters_data = load_new_filters()

# Mount static files
app.mount("/static", StaticFiles(directory="bot/static"), name="static")

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open(Path(__file__).parent / "static" / "index.html", "r", encoding="utf-8") as f:
        return f.read()

# Old endpoints (for backward compatibility)
@app.get("/api/devices")
async def get_devices():
    return {"devices": list(filters_data["devices"].keys())}

@app.get("/api/brands/{device}")
async def get_brands(device: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    return {"brands": list(brands.keys())}

@app.get("/api/series/{device}/{brand}")
async def get_series(device: str, brand: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    if brand not in brands:
        raise HTTPException(status_code=404, detail="Brand not found")
    series = brands[brand]["series"]
    return {"series": list(series.keys())}

@app.get("/api/models/{device}/{brand}/{series}")
async def get_models(device: str, brand: str, series: str):
    if device not in filters_data["devices"]:
        raise HTTPException(status_code=404, detail="Device not found")
    brands = filters_data["devices"][device]["brands"]
    if brand not in brands:
        raise HTTPException(status_code=404, detail="Brand not found")
    series_data = brands[brand]["series"]
    if series not in series_data:
        raise HTTPException(status_code=404, detail="Series not found")
    models = series_data[series]["models"]
    return {"models": models}

# New endpoints (for web app with multiple selection)
@app.get("/api/v2/devices")
async def get_devices_v2():
    """Return list of all available devices"""
    return {"devices": new_filters_data["devices"]}

@app.get("/api/v2/brands")
async def get_brands_v2():
    """Return list of all available brands"""
    return {"brands": new_filters_data["brands"]}

@app.get("/api/v2/series")
async def get_series_v2(
    devices: List[str] = Query(None, description="Filter series by devices"),
    brands: List[str] = Query(None, description="Filter series by brands")
):
    """
    Return list of series, optionally filtered by devices and brands.
    Supports multiple selection for both devices and brands.
    """
    series_list = new_filters_data["series"]
    
    # Filter by devices if provided
    if devices:
        series_list = [s for s in series_list if s["device"] in devices]
    
    # Filter by brands if provided
    if brands:
        series_list = [s for s in series_list if s["brand"] in brands]
    
    # Return unique series names
    unique_series = list({s["name"] for s in series_list})
    return {"series": unique_series}

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
    print(f"get_models_v2 called with devices={devices}, brands={brands}, series={series}")
    models_list = new_filters_data["models"]
    print(f"Initial models count: {len(models_list)}")
    
    # Filter by devices if provided
    if devices:
        models_list = [m for m in models_list if m["device"] in devices]
        print(f"After device filter ({devices}): {len(models_list)} models")
    
    # Filter by brands if provided
    if brands:
        models_list = [m for m in models_list if m["brand"] in brands]
        print(f"After brand filter ({brands}): {len(models_list)} models")
    
    # Filter by series if provided
    if series:
        models_list = [m for m in models_list if m["series"] in series]
        print(f"After series filter ({series}): {len(models_list)} models")
    
    print(f"Returning {len(models_list)} models: {models_list}")
    return {"models": models_list}

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