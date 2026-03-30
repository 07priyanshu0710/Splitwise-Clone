
from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, ForeignKey, DateTime, Numeric, Enum as SAEnum
from sqlalchemy.sql import func
import datetime
from typing import TYPE_CHECKING, List
import enum

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

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String)
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    curvature_code: Mapped[str] = mapped_column(String, default="USD") # Currency
    date: Mapped[datetime.datetime] = mapped_column(DateTime, default=func.now())
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    payer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=True)
    
    split_type: Mapped[SplitType] = mapped_column(SAEnum(SplitType))

    # Relationships
    payer: Mapped["User"] = relationship(back_populates="expenses_paid")
    group: Mapped["Group"] = relationship(back_populates="expenses")
    splits: Mapped[List["ExpenseSplit"]] = relationship(back_populates="expense", cascade="all, delete-orphan")

class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True) # For unequal split
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True) # For percentage split
    shares: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True) # For share split

    # Relationships
    expense: Mapped["Expense"] = relationship(back_populates="splits")
    user: Mapped["User"] = relationship(back_populates="expense_splits")
