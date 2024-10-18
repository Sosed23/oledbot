from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, String, Integer

from typing import Optional
from bot.database import Base
from bot.users.models import User


class Cart(Base):
    telegram_id: Mapped[int] = mapped_column(ForeignKey(
        'users.telegram_id', ondelete='CASCADE'), nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer)
    product_name: Mapped[Optional[str]] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    user: Mapped['User'] = relationship(back_populates='cart')


User.cart = relationship('Cart', back_populates='user',
                         cascade='all, delete-orphan')
