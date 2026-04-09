from typing import List
import logging
from app.repositories.report_repository import ReportRepository
from app.core.logging_config import LoggerMixin

class ReportService(LoggerMixin):
    def __init__(self, repository: ReportRepository):
        self.repository = repository

    def get_monthly_summary(self, user_id: int) -> List[dict]:
        self.logger.info(f"Generating monthly summary for user {user_id}")
        return self.repository.get_monthly_summary(user_id)
