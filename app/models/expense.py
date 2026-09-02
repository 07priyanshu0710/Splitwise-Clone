from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Numeric, Enum as SAEnum, CheckConstraint, Index
from sqlalchemy.sql import func
import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List
import enum

from app.core.constants import INR_CURRENCY_CODE

if TYPE_CHECKING:
    from .user import User
    from .group import Group

class SplitType(str, enum.Enum):
    EQUAL = "equal"
    UNEQUAL = "unequal"
    PERCENTAGE = "percentage"
    SHARE = "share"

class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("currency_code = 'INR'", name="currency_inr"),
        Index("ix_expenses_group_created_at", "group_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    currency_code: Mapped[str] = mapped_column(
        String(3),
        default=INR_CURRENCY_CODE,
        server_default=INR_CURRENCY_CODE,
    )
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)

    split_type: Mapped[SplitType] = mapped_column(SAEnum(SplitType))

    payer: Mapped["User"] = relationship(back_populates="expenses_paid")
    group: Mapped["Group"] = relationship(back_populates="expenses")
    splits: Mapped[List["ExpenseSplit"]] = relationship(back_populates="expense", cascade="all, delete-orphan")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"
    __table_args__ = (
        Index("ix_expense_splits_expense_id", "expense_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)
    percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=True)
    shares: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=True)

    expense: Mapped["Expense"] = relationship(back_populates="splits")
    user: Mapped["User"] = relationship(back_populates="expense_splits")
