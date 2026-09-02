from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLog]):
    def __init__(self, db: Session):
        super().__init__(AuditLog, db)

    def record(
        self,
        *,
        action: str,
        entity_type: str,
        entity_id: Optional[int],
        user_id: Optional[int],
        changes: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            changes=changes,
        )
        self.db.add(audit_log)
        self.db.flush()
        return audit_log
