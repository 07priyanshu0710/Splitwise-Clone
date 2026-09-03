from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BusinessLogicError
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import UserService


def test_register_user_preserves_unexpected_server_error():
    repository = MagicMock()
    repository.get_by_email.return_value = None
    repository.create.side_effect = RuntimeError("database unavailable")
    service = UserService(repository)

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.register_user(
            UserCreate(
                email="person@example.com",
                password="password123",
                full_name="Person",
            )
        )

    repository.db.rollback.assert_called_once_with()


def test_register_user_maps_concurrent_unique_conflict_to_business_error():
    repository = MagicMock()
    repository.get_by_email.return_value = None
    repository.create.side_effect = IntegrityError(
        statement="INSERT INTO users",
        params={},
        orig=Exception("unique violation"),
    )
    service = UserService(repository)

    with pytest.raises(BusinessLogicError, match="already registered"):
        service.register_user(
            UserCreate(
                email="person@example.com",
                password="password123",
                full_name="Person",
            )
        )

    repository.db.rollback.assert_called_once_with()


def test_update_user_preserves_unexpected_server_error():
    repository = MagicMock()
    repository.update.side_effect = RuntimeError("database unavailable")
    service = UserService(repository)
    user = MagicMock(email="person@example.com", mobile_number=None)

    with pytest.raises(RuntimeError, match="database unavailable"):
        service.update_user(user, UserUpdate(full_name="Updated Person"))

    repository.db.rollback.assert_called_once_with()
