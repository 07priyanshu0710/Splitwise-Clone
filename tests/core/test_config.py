import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_secret_key_is_required(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_secret_key_requires_at_least_32_characters():
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="too-short", _env_file=None)
