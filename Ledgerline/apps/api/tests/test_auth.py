import asyncio

import pytest

from app.core.auth import verify_api_key


@pytest.fixture(autouse=True)
def _reset_env():
    from app.core.config import settings

    original_env = settings.environment
    original_key = settings.api_key
    yield
    settings.environment = original_env
    settings.api_key = original_key


def _verify(**kwargs):
    return asyncio.run(verify_api_key(**kwargs))


def test_development_returns_none_without_key():
    from app.core.config import settings

    settings.environment = "development"
    assert _verify() is None
    assert _verify(api_key="anything") is None


def test_production_rejects_missing_key():
    from app.core.config import settings

    settings.environment = "production"
    with pytest.raises(Exception):
        _verify()


def test_production_rejects_invalid_key():
    from app.core.config import settings

    settings.environment = "production"
    settings.api_key = "correct-key"
    with pytest.raises(Exception) as exc_info:
        _verify(api_key="wrong-key")
    assert exc_info.value.status_code == 401


def test_production_accepts_valid_key():
    from app.core.config import settings

    settings.environment = "production"
    settings.api_key = "correct-key"
    result = _verify(api_key="correct-key")
    assert result == "correct-key"