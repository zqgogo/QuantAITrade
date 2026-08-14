from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class TradingBase(DeclarativeBase):
    pass


class MarketBase(DeclarativeBase):
    pass


trading_engine = create_engine(settings.trading_database_url, connect_args={"check_same_thread": False})
market_engine = create_engine(settings.market_database_url, connect_args={"check_same_thread": False})

TradingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=trading_engine)
MarketSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=market_engine)


def init_databases() -> None:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    from app.modules.trading import models as trading_models  # noqa: F401
    from app.modules.market import models as market_models  # noqa: F401
    from app.modules.ai import models as ai_models  # noqa: F401
    from app.modules.monitoring import models as monitoring_models  # noqa: F401
    TradingBase.metadata.create_all(bind=trading_engine)
    MarketBase.metadata.create_all(bind=market_engine)

