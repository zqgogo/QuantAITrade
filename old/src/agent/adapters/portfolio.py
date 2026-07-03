"""Agent-owned portfolio adapter."""

from typing import Any, Dict

from ..database import agent_db


class PortfolioAdapter:
    def get_snapshot(
        self,
        run_env: str,
        portfolio_id: str,
        account_id: str,
        position_group_id: str,
        symbol: str,
    ) -> Dict[str, Any]:
        positions = agent_db.list_positions(
            limit=50,
            run_env=run_env,
            portfolio_id=portfolio_id,
            account_id=account_id,
            position_group_id=position_group_id,
            symbol=symbol,
            status="open",
        )
        exposure = sum(float(p["entry_price"]) * float(p["quantity"]) for p in positions)
        unrealized = sum(float(p["unrealized_pnl"] or 0) for p in positions)
        return {
            "open_positions": positions,
            "open_position_count": len(positions),
            "exposure": exposure,
            "unrealized_pnl": unrealized,
        }


portfolio_adapter = PortfolioAdapter()

