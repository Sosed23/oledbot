from enum import Enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, ForeignKey, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database import Base
from bot.users.models import User


class OrderStatus(str, Enum):
    PENDING = "pending"  # Создан, ожидает обработки
    PROCESSING = "processing"  # В обработке
    CONFIRMED = "confirmed"  # Подтвержден
    PAID = "paid"  # Оплачен
    SHIPPING = "shipping"  # В доставке
    COMPLETED = "completed"  # Выполнен
    CANCELLED = "cancelled"  # Отменен
    REFUNDED = "refunded"  # Возвращен


class Order(Base):
    """Основная модель заказа"""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(
        ForeignKey('users.telegram_id', ondelete='CASCADE'), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String, default=OrderStatus.PENDING.value  # Используем String вместо SQLEnum
    )
    total_amount: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped['User'] = relationship(back_populates='orders')
    items: Mapped[List['OrderItem']] = relationship(
        back_populates='order', cascade='all, delete-orphan'
    )
    status_history: Mapped[List['OrderStatusHistory']] = relationship(
        back_populates='order', cascade='all, delete-orphan'
    )


class OrderItem(Base):
    """Модель для отдельных товаров в заказе"""
    __tablename__ = 'order_items'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'), nullable=False
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship
    order: Mapped['Order'] = relationship(back_populates='items')


class OrderStatusHistory(Base):
    """Модель для хранения истории изменений статуса заказа"""
    __tablename__ = 'order_status_history'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'), nullable=False
    )
    status: Mapped[str] = mapped_column(String, nullable=False)  # Используем String вместо SQLEnum
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationship
    order: Mapped['Order'] = relationship(back_populates='status_history')


# Добавляем связь с моделью User
User.orders = relationship(
    'Order', back_populates='user', cascade='all, delete-orphan'
)