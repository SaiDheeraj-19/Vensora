from app.config import get_settings
from pydantic import ValidationError
import pytest

def test_settings_load_successfully():
    settings = get_settings()
    assert settings.SECRET_KEY == "test_secret_key_1234567890"
    assert settings.POSTGRES_USER == "test_user"
    assert "sqlite" in settings.DATABASE_URL or "postgresql" in settings.DATABASE_URL
    assert settings.ENVIRONMENT == "development"

def test_settings_validation_error_on_missing_secret(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    from app.config.settings import Settings
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    assert "SECRET_KEY" in str(exc_info.value)
