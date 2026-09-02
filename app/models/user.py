from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.sql import func
import datetime
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .group import GroupMember
    from .expense import Expense, ExpenseSplit
    from .transaction import Settlement, Balance

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    mobile_number: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    group_memberships: Mapped[List["GroupMember"]] = relationship(back_populates="user")
    expenses_paid: Mapped[List["Expense"]] = relationship(back_populates="payer")
    expense_splits: Mapped[List["ExpenseSplit"]] = relationship(back_populates="user")
    sent_settlements: Mapped[List["Settlement"]] = relationship("Settlement", foreign_keys="Settlement.payer_id", back_populates="payer")
    received_settlements: Mapped[List["Settlement"]] = relationship("Settlement", foreign_keys="Settlement.payee_id", back_populates="payee")
