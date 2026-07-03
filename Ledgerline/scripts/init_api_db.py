import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps/api"))

from app.db.session import init_databases


if __name__ == "__main__":
    init_databases()
    print("Ledgerline databases initialized.")