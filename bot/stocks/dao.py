from bot.dao.base import BaseDAO
from bot.stocks.models_cart import Cart
from bot.database import async_session_maker

from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger


class CartDAO(BaseDAO):
    model = Cart
