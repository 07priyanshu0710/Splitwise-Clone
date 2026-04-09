from typing import Any, List
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api import deps
from app.services.report_service import ReportService
from app.schemas.report import MonthlySummaryResponse

router = APIRouter()

@router.get("/monthly-summary", response_model=List[MonthlySummaryResponse])
def get_monthly_summary(
    current_user: User = Depends(deps.get_current_active_user),
    service: ReportService = Depends(deps.get_report_service)
) -> Any:
    return service.get_monthly_summary(current_user.id)
