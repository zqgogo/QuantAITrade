"""Agent decision brain.

First implementation is deterministic and audit-friendly. It can be replaced
or extended with an LLM later without changing the service/database contract.
"""

from .config import DEFAULT_PROMPT_VERSION
from .schemas import AgentAction, AgentContext, AgentDecision, new_id, utc_ts


class AgentBrain:
    def decide(self, context: AgentContext) -> AgentDecision:
        market = context.market_context or {}
        portfolio = context.portfolio_context or {}
        memory = context.memory_context or {}

        latest_price = market.get("latest_price")
        trend = market.get("trend")
        open_positions = portfolio.get("open_position_count", 0)

        if not latest_price:
            action = AgentAction.OBSERVE.value
            confidence = 0.25
            reasoning = "行情数据不足，无法形成可靠交易判断。"
            risk_notes = "等待数据补齐；禁止在无价格快照时执行。"
        elif trend == "up" and open_positions == 0:
            action = AgentAction.BUY.value
            confidence = 0.68
            reasoning = "短周期均线高于长周期均线，且当前仓位组没有未平仓持仓。"
            risk_notes = "建议小仓试探；单笔风险应控制在 Agent 偏好设定以内。"
        elif trend == "down" and open_positions > 0:
            action = AgentAction.REDUCE.value
            confidence = 0.64
            reasoning = "短周期均线低于长周期均线，当前仓位组已有敞口，优先降低风险。"
            risk_notes = "若跌破止损价，应由执行层触发平仓或人工确认。"
        elif trend == "down":
            action = AgentAction.OBSERVE.value
            confidence = 0.55
            reasoning = "趋势偏弱，但当前仓位组没有持仓，不追空，先观察。"
            risk_notes = "避免在弱势环境中逆势开仓。"
        else:
            action = AgentAction.HOLD.value
            confidence = 0.5
            reasoning = "趋势信号不明确，暂不调整。"
            risk_notes = "等待更清晰的价格、成交量或风险信号。"

        stop_loss = {}
        take_profit = {}
        if latest_price and action in {AgentAction.BUY.value, AgentAction.HOLD.value}:
            stop_loss = {"type": "price", "price": round(float(latest_price) * 0.97, 8)}
            take_profit = {"type": "price", "price": round(float(latest_price) * 1.06, 8)}

        profile = memory.get("profile", {})
        preferences = profile.get("preferences", {})
        requires_confirmation = bool(preferences.get("requires_human_confirmation", True))
        if context.run_env == "live":
            requires_confirmation = True

        return AgentDecision(
            decision_id=new_id("dec"),
            request_id=context.request_id,
            run_env=context.run_env,
            agent_id=context.agent_id,
            portfolio_id=context.portfolio_id,
            account_id=context.account_id,
            position_group_id=context.position_group_id,
            strategy_id=context.strategy_id,
            symbol=context.asset.symbol,
            asset_class=context.asset.asset_class,
            exchange=context.asset.exchange,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            risk_notes=risk_notes,
            suggested_price=float(latest_price) if latest_price else None,
            suggested_quantity=None,
            timeframe=market.get("interval", preferences.get("default_timeframe", "1h")),
            stop_loss=stop_loss,
            take_profit=take_profit,
            requires_human_confirmation=requires_confirmation,
            market_snapshot=market,
            portfolio_snapshot=portfolio,
            risk_snapshot=context.risk_context,
            memory_snapshot=memory,
            metadata={
                "brain": "deterministic_v1",
                "prompt_version": DEFAULT_PROMPT_VERSION,
                "created_by": "src.agent.brain.AgentBrain",
            },
            created_at=utc_ts(),
            updated_at=utc_ts(),
        )


agent_brain = AgentBrain()

