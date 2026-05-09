"""Agent decision brain.

The agent does not place orders. It builds an auditable market view, compares
long and short scenarios, then returns a suggestion with invalidation levels.
"""

from .config import DEFAULT_PROMPT_VERSION
from .schemas import AgentAction, AgentContext, AgentDecision, new_id, utc_ts
from .skills import skill_registry


class AgentBrain:
    def decide(self, context: AgentContext) -> AgentDecision:
        market = context.market_context or {}
        portfolio = context.portfolio_context or {}
        memory = context.memory_context or {}

        latest_price = market.get("latest_price")
        frames = market.get("timeframes") or {}
        open_positions = portfolio.get("open_position_count", 0)
        analysis = skill_registry.run("multi_timeframe_strategy", {"market": market})

        if not latest_price:
            action = AgentAction.OBSERVE.value
            confidence = 0.25
            reasoning = "行情数据不足，无法完成多周期趋势、波动和关键价位分析。"
            risk_notes = "等待最新与历史行情补齐；只允许记录观察，不给入场建议。"
        else:
            action, confidence = self._choose_action(analysis, open_positions)
            reasoning = self._build_reasoning(analysis, frames, open_positions)
            risk_review = skill_registry.run("risk_review", {"analysis": analysis, "action": action})
            risk_notes = self._build_risk_notes(risk_review)

        stop_loss, take_profit = self._build_trade_levels(analysis, action)

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
                "brain": "multi_factor_v1",
                "prompt_version": DEFAULT_PROMPT_VERSION,
                "created_by": "src.agent.brain.AgentBrain",
                "analysis": analysis,
                "strategy": self._strategy_summary(analysis),
                "skills": skill_registry.describe(),
            },
            created_at=utc_ts(),
            updated_at=utc_ts(),
        )

    def _choose_action(self, analysis: dict, open_positions: int) -> tuple[str, float]:
        bias = analysis["market_bias"]
        direction_score = abs(float(analysis["direction_score"]))
        confidence = min(0.88, 0.45 + direction_score * 0.35)
        if analysis["available_timeframes"] < 2:
            return AgentAction.OBSERVE.value, min(confidence, 0.45)
        if bias == "bullish":
            return AgentAction.BUY.value, confidence
        if bias == "bearish":
            return (AgentAction.REDUCE.value if open_positions else AgentAction.SELL.value), confidence
        return AgentAction.HOLD.value if open_positions else AgentAction.OBSERVE.value, min(confidence, 0.55)

    def _build_reasoning(self, analysis: dict, frames: dict, open_positions: int) -> str:
        votes = analysis["frame_votes"]
        vote_text = "；".join(
            f"{name}: {item['trend']} score={item['score']}"
            for name, item in votes.items()
        ) or "无有效周期"
        long_plan = analysis["long_plan"]
        short_plan = analysis["short_plan"]
        return (
            f"多周期综合偏向：{analysis['market_bias']}，方向分={analysis['direction_score']}。"
            f"周期投票：{vote_text}。"
            f"当前结构：{analysis['regime']}，RSI={self._fmt(analysis.get('rsi'))}，"
            f"ATR%={self._fmt(analysis.get('atr_percent'))}。"
            f"关键支撑={self._fmt(analysis.get('support'))}，关键压力={self._fmt(analysis.get('resistance'))}。"
            f"多头方案：入场区 {long_plan['entry_zone']}，失效 {long_plan['invalidation']}，目标 {long_plan['targets']}。"
            f"空头方案：入场区 {short_plan['entry_zone']}，失效 {short_plan['invalidation']}，目标 {short_plan['targets']}。"
            f"当前仓位组持仓数={open_positions}。"
        )

    def _build_risk_notes(self, risk_review: dict) -> str:
        warnings = risk_review.get("warnings") or []
        return f"{risk_review.get('summary', '')}。" + ("；".join(warnings) if warnings else "等待价格触发计划，不提前执行。")

    def _build_trade_levels(self, analysis: dict, action: str) -> tuple[dict, dict]:
        if action == AgentAction.BUY.value:
            plan = analysis["long_plan"]
        elif action == AgentAction.SELL.value:
            plan = analysis["short_plan"]
        else:
            return {}, {}
        return (
            {"type": "invalidation", "price": plan["invalidation"], "reason": plan["invalidation_reason"]},
            {"type": "targets", "prices": plan["targets"]},
        )

    def _strategy_summary(self, analysis: dict) -> dict:
        return {
            "name": "multi_timeframe_momentum_reversion",
            "description": "结合多周期趋势、均线结构、MACD、RSI、布林位置、ATR、支撑压力和成交量的建议策略。",
            "market_bias": analysis["market_bias"],
            "long_enabled": analysis["market_bias"] in {"bullish", "neutral"},
            "short_enabled": analysis["market_bias"] in {"bearish", "neutral"},
            "risk_model": "ATR + support/resistance invalidation",
        }

    def _fmt(self, value: object) -> str:
        if value is None:
            return "N/A"
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value)


agent_brain = AgentBrain()
