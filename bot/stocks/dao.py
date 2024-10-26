from bot.dao.base import BaseDAO
from bot.stocks.models_cart import Cart
from bot.stocks.models_order import Order, OrderItem, OrderStatusHistory, OrderStatus
from bot.database import async_session_maker

from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class CartDAO(BaseDAO):
    model = Cart


class OrderDAO(BaseDAO):
    model = Order


class OrderItemDAO(BaseDAO):
    model = OrderItem


class OrderStatusHistoryDAO(BaseDAO):
    model = OrderStatusHistory
