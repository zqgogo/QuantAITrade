import os
import tempfile

_test_dir = tempfile.mkdtemp(prefix="ledgerline_test_")
os.environ["LEDGERLINE_DATA_DIR"] = _test_dir
os.environ["LEDGERLINE_TRADING_DATABASE_URL"] = f"sqlite:///{_test_dir}/trading.db"
os.environ["LEDGERLINE_MARKET_DATABASE_URL"] = f"sqlite:///{_test_dir}/market.db"