from enum import Enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import BigInteger, ForeignKey, String, Integer, DateTime, Enum as SQLEnum
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

    telegram_id: Mapped[int] = mapped_column(ForeignKey(
        'users.telegram_id', ondelete='CASCADE'), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), default=OrderStatus.PENDING)
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

    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'))
    product_id: Mapped[int] = mapped_column(Integer)
    product_name: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[int] = mapped_column(Integer)

    # Relationship
    order: Mapped['Order'] = relationship(back_populates='items')


class OrderStatusHistory(Base):
    """Модель для хранения истории изменений статуса заказа"""
    __tablename__ = 'order_status_history'

    order_id: Mapped[int] = mapped_column(
        ForeignKey('orders.id', ondelete='CASCADE'))
    status: Mapped[OrderStatus] = mapped_column(SQLEnum(OrderStatus))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationship
    order: Mapped['Order'] = relationship(back_populates='status_history')


# Добавляем связь с User моделью
User.orders = relationship('Order', back_populates='user',
                           cascade='all, delete-orphan')
