# QuantAITrade Agent

这是一个自包含 Agent 包。所有 Agent 相关内容都放在本目录内：

- `data/agent.db`：Agent 自己的数据库，保存决策、反馈、记忆、交易、持仓、报告和绩效快照。
- `memory/`：Agent 的 profile、偏好、特点和长期记忆。
- `skills/`：Agent 自己的行为规则和技能说明。
- `tools/`：Agent 自己可复用的工具函数。
- `adapters/`：连接外部量化系统、行情源、执行系统的适配层。
- `reports/`：Agent 生成的分析报告目录。

外部系统只应通过 `AgentService`、CLI 或 API 调用 Agent。Agent 不直接调用交易所下单接口。

## 独立运行

```bash
python -m src.agent.runner --init-db
python -m src.agent.runner --symbol BTC/USDT --run-env paper --json
```

当前 Agent 只给建议，不直接下单。一次决策会读取多周期行情快照，计算趋势、RSI、MACD、布林带、ATR、支撑压力、成交量状态，并同时生成多头和空头方案。

更完整的内部设计见 [AGENT_DESIGN.md](AGENT_DESIGN.md)。

后续接入其他系统时，优先看 [AGENT_HANDOFF.md](AGENT_HANDOFF.md)。

## Skill 调用架构

Agent 的 Brain 不直接塞满所有策略细节，而是调用 `skills/` 里的能力模块：

```text
brain.py
  -> skills/registry.py
  -> skills/multi_timeframe_strategy.py
  -> skills/risk_review.py
  -> tools/indicators.py
```

当前已实现两个可调用 Skill：

- `multi_timeframe_strategy`：多周期行情、指标、支撑压力、多空方案。
- `risk_review`：盈亏比、波动、追高/追空风险复核。

## 当前建议逻辑

```text
多周期行情
  -> 15m / 1h / 4h / 1d 数据快照
  -> 均线结构、RSI、MACD、布林带、ATR、支撑压力、成交量
  -> 每个周期单独评分
  -> 按周期权重合成 bullish / bearish / neutral
  -> 同时生成 long_plan 和 short_plan
  -> 输出最终建议 BUY / SELL / HOLD / REDUCE / OBSERVE
```

Agent 的建议里会包含：

- `reasoning`：多周期投票、市场结构、关键位、多空方案。
- `risk_notes`：盈亏比、波动风险、追高/追空提醒。
- `metadata.analysis`：完整结构化分析结果。
- `metadata.strategy`：本次使用的策略说明。
- `stop_loss` / `take_profit`：建议方向的失效位和目标位。

## 学习、审计和总结

当前 Agent 已支持第一版学习与审计：

- 用户反馈会写入 Agent 自己的记忆。
- 通过 Agent 记录的交易结果会写入 Agent 自己的记忆。
- `/api/v1/agent/audit` 可按条件审计决策、反馈、交易、持仓、记忆、报告。
- `/api/v1/agent/summary` 可生成日、周、月、年总结。

示例：

```text
GET /api/v1/agent/audit?record_type=decisions&run_env=paper&symbol=BTC/USDT
GET /api/v1/agent/audit?record_type=memories&memory_type=feedback
GET /api/v1/agent/summary?period=month&run_env=paper
GET /api/v1/agent/summary?period=year&symbol=BTC/USDT
```

## 嵌入调用

```python
from src.agent import AgentService

agent = AgentService()
decision = agent.create_decision({
    "run_env": "paper",
    "asset": {"symbol": "BTC/USDT", "asset_class": "crypto"},
    "portfolio_id": "main_crypto",
    "account_id": "paper_001",
    "position_group_id": "btc_ai_swing"
})
```
