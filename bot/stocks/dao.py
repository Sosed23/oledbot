from bot.dao.base import BaseDAO
from bot.stocks.models import Cart


class CartDAO(BaseDAO):
    model = Cart
