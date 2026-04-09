from pydantic import BaseModel

class MonthlySummaryResponse(BaseModel):
    month: str
    total_paid: float
    total_owed: float
