
from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Numeric
from sqlalchemy.sql import func
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .group import Group

class Settlement(Base):
    __tablename__ = "settlements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    payee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    currency_code: Mapped[str] = mapped_column(String, default="USD")
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    payer: Mapped["User"] = relationship("User", foreign_keys=[payer_id], back_populates="sent_settlements")
    payee: Mapped["User"] = relationship("User", foreign_keys=[payee_id], back_populates="received_settlements")

class Balance(Base):
    """
    Table to cache current balances between users in a group.
    This is an optimization; balances can be calculated from expenses and settlements.
    """
    __tablename__ = "balances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owes_to_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # Determines direction
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2)) # Always positive
    currency_code: Mapped[str] = mapped_column(String, default="USD")
    last_updated: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    owes_to: Mapped["User"] = relationship("User", foreign_keys=[owes_to_id])
