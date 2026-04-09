import pytest
from unittest.mock import MagicMock
from app.services.report_service import ReportService

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def report_service(mock_repo):
    return ReportService(repository=mock_repo)

def test_get_monthly_summary(report_service, mock_repo):
    user_id = 1
    mock_repo.get_monthly_summary.return_value = [
        {"month": "2024-01", "total_paid": 100.0, "total_owed": 50.0}
    ]
    
    result = report_service.get_monthly_summary(user_id)
    
    assert len(result) == 1
    assert result[0]["month"] == "2024-01"
    mock_repo.get_monthly_summary.assert_called_once_with(user_id)
