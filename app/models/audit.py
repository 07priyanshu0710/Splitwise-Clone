
from app.db.base_class import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.sql import func
import datetime

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    entity_type: Mapped[str] = mapped_column(String, index=True) # e.g. "Expense", "Group"
    entity_id: Mapped[int] = mapped_column(nullable=True) # Nullable because ID might be irrelevant for some actions
    user_id: Mapped[int] = mapped_column(nullable=True) # User who performed the action
    changes: Mapped[dict] = mapped_column(JSON, nullable=True) # JSON diff
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
