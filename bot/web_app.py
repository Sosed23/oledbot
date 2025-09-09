from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from bot.database import async_session_maker
import uvicorn
from typing import List, Optional

app = FastAPI(title="Device Filter API", description="API for filtering devices, brands, series, models for spare parts")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/devices")
async def get_devices():
    """Return list of all available devices"""
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM devices ORDER BY name"))
        devices = [row[0] for row in result.fetchall()]
        return {"devices": devices}

@app.get("/api/brands")
async def get_brands():
    """Return list of all available brands"""
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT name FROM brands ORDER BY name"))
        brands = [row[0] for row in result.fetchall()]
        return {"brands": brands}

@app.get("/api/series")
async def get_series(
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

@app.get("/api/models")
async def get_models(
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

@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint working", "status": "success"}

# Print registered routes for debugging
@app.on_event("startup")
async def print_routes():
    print("Registered API routes:")
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/api'):
            print(f"  {route.methods} {route.path}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)