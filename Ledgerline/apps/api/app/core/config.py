from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ledgerline API"
    app_version: str = "0.1.0"
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]
    data_dir: Path = Path("var")
    config_dir: Path = Path("../../config")
    llm_config_file: str = "llm.config.json"
    llm_demo_config_file: str = "llm.config.demo.json"
    trading_database_url: str = "sqlite:///./var/trading.db"
    market_database_url: str = "sqlite:///./var/market.db"
    chroma_path: str = "./var/chroma"
    api_key: str = "dev-secret-key"

    model_config = SettingsConfigDict(env_prefix="LEDGERLINE_", env_file=".env")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
