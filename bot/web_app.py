from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import select, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database import Base, async_session_maker
import uvicorn
from typing import List, Optional
import logging
from bot.stocks.dao import OrderDAO, OrderStatusHistoryDAO, CartDAO


class Device(Base):
    __tablename__ = 'devices'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

class Brand(Base):
    __tablename__ = 'brands'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)

class Series(Base):
    __tablename__ = 'series'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey('devices.id'))
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id'))
    name: Mapped[str] = mapped_column(String(255))
    device: Mapped['Device'] = relationship()
    brand: Mapped['Brand'] = relationship()

class ModelNew(Base):
    __tablename__ = 'models_new'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[int] = mapped_column(ForeignKey('devices.id'))
    brand_id: Mapped[int] = mapped_column(ForeignKey('brands.id'))
    series_id: Mapped[int] = mapped_column(ForeignKey('series.id'))
    name: Mapped[str] = mapped_column(String(255))
    model_id: Mapped[Optional[int]] = mapped_column(Integer)
    device: Mapped['Device'] = relationship()
    brand: Mapped['Brand'] = relationship()
    series: Mapped['Series'] = relationship()

app = FastAPI(title="Device Filter API", description="API for filtering devices, brands, series, models for spare parts")

# Mount static files
app.mount("/static", StaticFiles(directory="bot/static"), name="static")

logger = logging.getLogger(__name__)

OPERATION_NAMES = {}

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open("bot/static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/cart", response_class=HTMLResponse)
async def get_cart():
    with open("bot/static/cart.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/orders", response_class=HTMLResponse)
async def get_orders():
    with open("bot/static/orders.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/devices")
async def get_devices():
    """Return list of all available devices"""
    async with async_session_maker() as session:
        stmt = select(Device.name)
        result = await session.execute(stmt)
        devices = [row.name for row in result.scalars().all()]
        return {"devices": devices}

@app.get("/api/brands")
async def get_brands():
    """Return list of all available brands"""
    async with async_session_maker() as session:
        stmt = select(Brand.name)
        result = await session.execute(stmt)
        brands = [row.name for row in result.scalars().all()]
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
    stmt = select(Series.name)
    if devices:
        stmt = stmt.join(Device).where(Device.name.in_(devices))
    if brands:
        stmt = stmt.join(Brand).where(Brand.name.in_(brands))
    stmt = stmt.distinct().order_by(Series.name)
    async with async_session_maker() as session:
        result = await session.execute(stmt)
        series = [row.name for row in result.scalars().all()]
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
    stmt = select(
        Device.name.label('device'),
        Brand.name.label('brand'),
        Series.name.label('series'),
        ModelNew.name,
        ModelNew.model_id
    ).select_from(ModelNew).join(Device).join(Brand).join(Series)
    if devices:
        stmt = stmt.where(Device.name.in_(devices))
    if brands:
        stmt = stmt.where(Brand.name.in_(brands))
    if series:
        stmt = stmt.where(Series.name.in_(series))
    stmt = stmt.order_by(ModelNew.name)
    async with async_session_maker() as session:
        result = await session.execute(stmt)
        models = []
        for row in result.fetchall():
            models.append({
                "device": row.device,
                "brand": row.brand,
                "series": row.series,
                "name": row.name,
                "model_id": row.model_id
            })
        return {"models": models}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "Test endpoint working", "status": "success"}

@app.get("/api/v2/cart")
async def get_cart_v2(telegram_id: str = Query(..., description="Telegram ID of the user")):
    """
    Return list of cart items for a specific user by telegram_id.
    """
    try:
        cart_items = await CartDAO.find_all(telegram_id=telegram_id)
        items_data = []
        total_amount = 0
        for item in cart_items:
            operation_name = f"Операция {item.operation}" if item.operation else "Неизвестная операция"
            name = f"{item.product_name} - {operation_name}"
            item_total = item.price * item.quantity
            total_amount += item_total
            items_data.append({
                "name": name,
                "price": item.price,
                "quantity": item.quantity,
                "total": item_total
            })

        return {
            "cart": {
                "items": items_data,
                "total_amount": total_amount
            }
        }
    except Exception as e:
        logger.error(f"Error fetching cart for telegram_id={telegram_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching cart")

# Print registered routes for debugging
@app.on_event("startup")
async def print_routes():
    print("Registered API routes:")
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/api'):
            print(f"  {route.methods} {route.path}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1111)