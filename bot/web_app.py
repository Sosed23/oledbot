from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy import select, String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database import Base, async_session_maker
import uvicorn
from typing import List, Optional
import logging
from bot.stocks.dao import OrderDAO, OrderStatusHistoryDAO

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
app.mount("/static", StaticFiles(directory="static"), name="static")

logger = logging.getLogger(__name__)

OPERATION_NAMES = {}

@app.get("/webapp", response_class=HTMLResponse)
async def get_webapp():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/cart", response_class=HTMLResponse)
async def get_cart():
    with open("static/cart.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/orders", response_class=HTMLResponse)
async def get_orders():
    with open("static/orders.html", "r", encoding="utf-8") as f:
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

# Print registered routes for debugging
@app.on_event("startup")
async def print_routes():
    print("Registered API routes:")
    for route in app.routes:
        if hasattr(route, 'path') and route.path.startswith('/api'):
            print(f"  {route.methods} {route.path}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=1111)