from app.core.config import Settings, get_settings

_LEDGERLINE_ENV_VARS = [
    "LEDGERLINE_DATA_DIR",
    "LEDGERLINE_TRADING_DATABASE_URL",
    "LEDGERLINE_MARKET_DATABASE_URL",
]


def test_defaults(monkeypatch):
    for var in _LEDGERLINE_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("LEDGERLINE_ENVIRONMENT", raising=False)
    monkeypatch.delenv("LEDGERLINE_API_KEY", raising=False)

    s = Settings(_env_file=None)
    assert s.app_name == "Ledgerline API"
    assert s.environment == "development"
    assert s.api_key == "dev-secret-key"
    assert s.data_dir.name == "var"
    assert "http://localhost:3000" in s.cors_origins


def test_env_override(monkeypatch):
    monkeypatch.setenv("LEDGERLINE_ENVIRONMENT", "production")
    monkeypatch.setenv("LEDGERLINE_API_KEY", "custom-key")
    s = Settings(_env_file=None)
    assert s.environment == "production"
    assert s.api_key == "custom-key"


def test_get_settings_is_cached():
    assert get_settings() is get_settings()