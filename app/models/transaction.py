from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Numeric, CheckConstraint, Index
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.core.constants import INR_CURRENCY_CODE

if TYPE_CHECKING:
    from .user import User
    from .group import Group

class Settlement(Base):
    __tablename__ = "settlements"
    __table_args__ = (
        CheckConstraint("currency_code = 'INR'", name="currency_inr"),
        Index("ix_settlements_group_created_at", "group_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    payee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default=INR_CURRENCY_CODE,
        server_default=INR_CURRENCY_CODE,
    )
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payer: Mapped["User"] = relationship("User", foreign_keys=[payer_id], back_populates="sent_settlements")
    payee: Mapped["User"] = relationship("User", foreign_keys=[payee_id], back_populates="received_settlements")

class Balance(Base):
    __tablename__ = "balances"
    __table_args__ = (
        CheckConstraint("user_id <> owes_to_id", name="different_users"),
        CheckConstraint("amount > 0", name="positive_amount"),
        Index(
            "uq_balances_user_owes_group",
            "user_id",
            "owes_to_id",
            "group_id",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
        Index("ix_balances_group_id", "group_id"),
        Index("ix_balances_owes_to_id", "owes_to_id"),
        CheckConstraint("currency_code = 'INR'", name="currency_inr"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owes_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default=INR_CURRENCY_CODE,
        server_default=INR_CURRENCY_CODE,
    )
    last_updated: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    owes_to: Mapped["User"] = relationship("User", foreign_keys=[owes_to_id])
