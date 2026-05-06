"""Public service API for the self-contained agent."""

from typing import Any, Dict, Optional

from .adapters.market_data import market_data_adapter
from .adapters.portfolio import portfolio_adapter
from .brain import agent_brain
from .config import DEFAULT_AGENT_ID
from .database import agent_db
from .memory_store import agent_memory
from .schemas import (
    AgentContext,
    AgentFeedback,
    AgentPosition,
    AgentTradeRecord,
    AssetRef,
    new_id,
)


class AgentService:
    """Stable boundary for CLI, API, SDK and embedding use."""

    def __init__(self):
        agent_db.init_database()

    def create_decision(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        context = self._build_context(payload)

        if not context.market_context:
            context.market_context = market_data_adapter.get_snapshot(
                context.asset.symbol,
                payload.get("interval") or payload.get("timeframe") or "1h",
            )

        if not context.portfolio_context:
            context.portfolio_context = portfolio_adapter.get_snapshot(
                run_env=context.run_env,
                portfolio_id=context.portfolio_id,
                account_id=context.account_id,
                position_group_id=context.position_group_id,
                symbol=context.asset.symbol,
            )

        if not context.memory_context:
            context.memory_context = agent_memory.context()

        decision = agent_brain.decide(context)
        agent_db.save_decision(decision)
        return decision.to_dict()

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        return agent_db.get_decision(decision_id)

    def list_decisions(self, limit: int = 50, **filters: Any) -> Dict[str, Any]:
        return {"items": agent_db.list_decisions(limit=limit, **filters), "limit": limit}

    def submit_feedback(
        self,
        decision_id: str,
        feedback_type: str,
        comment: str = "",
        executed_price: Optional[float] = None,
        executed_quantity: Optional[float] = None,
        result_snapshot: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        feedback = AgentFeedback(
            feedback_id=new_id("fb"),
            decision_id=decision_id,
            feedback_type=feedback_type,
            comment=comment,
            executed_price=executed_price,
            executed_quantity=executed_quantity,
            result_snapshot=result_snapshot or {},
        )
        agent_db.save_feedback(feedback)
        agent_memory.add_memory(
            summary=f"决策 {decision_id} 收到反馈：{feedback_type}。{comment}".strip(),
            memory_type="feedback",
            payload=feedback.to_dict(),
            importance=0.7 if feedback_type in {"accepted", "executed_manually"} else 0.4,
        )
        return feedback.to_dict()

    def record_trade(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        trade = AgentTradeRecord(
            trade_id=payload.get("trade_id") or new_id("trd"),
            run_env=payload.get("run_env", "paper"),
            portfolio_id=payload.get("portfolio_id", "default_portfolio"),
            account_id=payload.get("account_id", "default_account"),
            position_group_id=payload.get("position_group_id", "default_group"),
            strategy_id=payload.get("strategy_id", "agent_discretionary_v1"),
            decision_id=payload.get("decision_id"),
            symbol=payload["symbol"],
            asset_class=payload.get("asset_class", "crypto"),
            side=payload["side"],
            price=float(payload["price"]),
            quantity=float(payload["quantity"]),
            status=payload.get("status", "recorded"),
            source_type=payload.get("source_type", "agent"),
            realized_pnl=float(payload.get("realized_pnl", 0.0)),
            fees=float(payload.get("fees", 0.0)),
            notes=payload.get("notes", ""),
        )
        agent_db.save_trade(trade)
        return trade.to_dict()

    def save_position(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        position = AgentPosition(
            position_id=payload.get("position_id") or new_id("pos"),
            run_env=payload.get("run_env", "paper"),
            portfolio_id=payload.get("portfolio_id", "default_portfolio"),
            account_id=payload.get("account_id", "default_account"),
            position_group_id=payload.get("position_group_id", "default_group"),
            strategy_id=payload.get("strategy_id", "agent_discretionary_v1"),
            symbol=payload["symbol"],
            asset_class=payload.get("asset_class", "crypto"),
            side=payload.get("side", "long"),
            entry_price=float(payload["entry_price"]),
            quantity=float(payload["quantity"]),
            status=payload.get("status", "open"),
            realized_pnl=float(payload.get("realized_pnl", 0.0)),
            unrealized_pnl=float(payload.get("unrealized_pnl", 0.0)),
            max_drawdown=float(payload.get("max_drawdown", 0.0)),
            notes=payload.get("notes", ""),
        )
        agent_db.save_position(position)
        return position.to_dict()

    def list_positions(self, limit: int = 100, **filters: Any) -> Dict[str, Any]:
        return {"items": agent_db.list_positions(limit=limit, **filters), "limit": limit}

    def performance_summary(self, **filters: Any) -> Dict[str, Any]:
        return agent_db.summarize_performance(**filters)

    def init_database(self) -> Dict[str, Any]:
        agent_db.init_database()
        return {"success": True, "db_path": str(agent_db.db_path)}

    def _build_context(self, payload: Dict[str, Any]) -> AgentContext:
        asset_payload = payload.get("asset") or {}
        if "symbol" in payload and "symbol" not in asset_payload:
            asset_payload["symbol"] = payload["symbol"]
        asset = AssetRef(
            symbol=asset_payload.get("symbol", "BTC/USDT"),
            asset_class=asset_payload.get("asset_class", payload.get("asset_class", "crypto")),
            exchange=asset_payload.get("exchange", payload.get("exchange", "unknown")),
            currency=asset_payload.get("currency", payload.get("currency", "USDT")),
        )
        return AgentContext(
            request_id=payload.get("request_id") or new_id("req"),
            run_env=payload.get("run_env", "paper"),
            agent_id=payload.get("agent_id", DEFAULT_AGENT_ID),
            portfolio_id=payload.get("portfolio_id", "default_portfolio"),
            account_id=payload.get("account_id", "default_account"),
            position_group_id=payload.get("position_group_id", "default_group"),
            strategy_id=payload.get("strategy_id", "agent_discretionary_v1"),
            asset=asset,
            task_type=payload.get("task_type", "decision"),
            market_context=payload.get("market_context") or {},
            portfolio_context=payload.get("portfolio_context") or {},
            risk_context=payload.get("risk_context") or {},
            memory_context=payload.get("memory_context") or {},
            user_instruction=payload.get("user_instruction", "只给建议，不自动下单"),
        )


agent_service = AgentService()

