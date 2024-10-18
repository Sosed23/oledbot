from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, ForeignKey, String, Integer

from typing import Optional
from bot.database import Base


class User(Base):
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String)
    first_name: Mapped[Optional[str]] = mapped_column(String)
    last_name: Mapped[Optional[str]] = mapped_column(String)
    referral_id: Mapped[Optional[int]] = mapped_column(Integer)
