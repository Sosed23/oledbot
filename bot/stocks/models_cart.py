from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import TSVECTOR
from typing import Optional, Any
from bot.database import Base
from bot.users.models import User  # Добавлен импорт модели User


class Cart(Base):
    __tablename__ = 'carts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False
    )
    product_id: Mapped[Optional[int]] = mapped_column(Integer)
    product_name: Mapped[Optional[str]] = mapped_column(String)
    task_id: Mapped[Optional[int]] = mapped_column(Integer)
    operation: Mapped[Optional[str]] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)

    assembly_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Разбор/Сбор
    touch_or_backlight: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Подсветка/Тач


    # Односторонняя связь: Cart знает о User, но User не знает о Cart
    user: Mapped['User'] = relationship("User")


class Model(Base):
    __tablename__ = 'models'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_name: Mapped[Optional[str]] = mapped_column(String)  # Поле для model_name
    model_engineer: Mapped[Optional[str]] = mapped_column(String)  # Поле для model_engineer
    model_id: Mapped[Optional[str]] = mapped_column(String)  # Поле для model_id
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)
