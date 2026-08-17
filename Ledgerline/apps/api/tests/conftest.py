import os
import tempfile

import pytest

from app.db.session import TradingSessionLocal
from app.modules.backtesting.models import BacktestRecord
from app.modules.monitoring.models import AlertNotificationRecord, AlertRuleRecord
from app.modules.trading.models import FxRate, Position, Portfolio, Transaction, Workspace

_test_dir = tempfile.mkdtemp(prefix="ledgerline_test_")
os.environ["LEDGERLINE_DATA_DIR"] = _test_dir
os.environ["LEDGERLINE_TRADING_DATABASE_URL"] = f"sqlite:///{_test_dir}/trading.db"
os.environ["LEDGERLINE_MARKET_DATABASE_URL"] = f"sqlite:///{_test_dir}/market.db"


@pytest.fixture(autouse=True)
def _clean_db():
    yield
    db = TradingSessionLocal()
    try:
        db.execute(AlertNotificationRecord.__table__.delete())
        db.execute(AlertRuleRecord.__table__.delete())
        db.execute(BacktestRecord.__table__.delete())
        db.execute(FxRate.__table__.delete())
        db.execute(Transaction.__table__.delete())
        db.execute(Position.__table__.delete())
        db.execute(Portfolio.__table__.delete())
        db.execute(Workspace.__table__.delete())
        db.commit()
    finally:
        db.close()