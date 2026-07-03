# Agent 交接与接入说明

更新时间：2026-05-09

---

# 一、当前结论

`src/agent/` 已经是一个自包含 Agent 子系统，可以独立运行，也可以被 QuantAITrade 或其他 App 通过 Python SDK / FastAPI 调用。

当前 Agent 的定位：

- 只给交易建议，不直接下单。
- 自己保存决策、反馈、记忆、交易记录、持仓记录、审计记录和周期总结。
- 外部系统只作为行情、上下文和反馈来源。

---

# 二、当前完成度

| 能力 | 状态 | 说明 |
| --- | --- | --- |
| 独立目录 | 已完成 | 所有 Agent 相关内容在 `src/agent/` |
| 独立数据库 | 已完成 | `src/agent/data/agent.db` |
| 独立运行 | 已完成 | `python -m src.agent.runner` |
| API 调用 | 已完成 | `/api/v1/agent/*` |
| SDK 调用 | 已完成 | `from src.agent import AgentService` |
| Skill 拆分 | 已完成 | `multi_timeframe_strategy`、`risk_review` |
| Tool 拆分 | 已完成 | `tools/indicators.py` |
| 多周期分析 | 已完成第一版 | 15m / 1h / 4h / 1d |
| 多空建议 | 已完成第一版 | long_plan / short_plan |
| 学习记忆 | 已完成第一版 | feedback / trade_result 事件记忆 |
| 条件审计 | 已完成第一版 | decisions / feedback / trades / positions / memories / reports |
| 日周月年总结 | 已完成第一版 | `/api/v1/agent/summary` |
| 报告生成 | 未完成 | 仅预留 `reports/` 和 `agent_reports` |
| LLM 深度复盘 | 未完成 | 当前为规则 + Skill 编排 |
| UI 展示 | 未完成 | API 已有，页面未接 |

---

# 三、关键文件

```text
src/agent/
├── AGENT_DESIGN.md          # 设计与实现说明
├── AGENT_HANDOFF.md         # 本交接文档
├── README.md                # 快速说明
├── service.py               # 对外统一入口
├── runner.py                # CLI 独立运行入口
├── brain.py                 # Agent 编排层
├── database.py              # Agent 自有 SQLite 仓储
├── memory_store.py          # Agent profile / 偏好 / 记忆
├── audit.py                 # 条件审计查询
├── analyzer.py              # 日/周/月/年总结
├── adapters/
│   ├── market_data.py       # 外部行情适配
│   └── portfolio.py         # Agent 自有持仓快照
├── skills/
│   ├── registry.py
│   ├── multi_timeframe_strategy.py
│   └── risk_review.py
└── tools/
    └── indicators.py
```

---

# 四、独立运行

初始化 Agent 数据库：

```bash
python -m src.agent.runner --init-db
```

生成一次建议：

```bash
python -m src.agent.runner --symbol BTC/USDT --run-env paper --json
```

如果本地没有对应 K 线，Agent 会保守输出：

```text
OBSERVE
```

这是预期行为，不是错误。

---

# 五、Python SDK 接入

```python
from src.agent import AgentService

agent = AgentService()

decision = agent.create_decision({
    "run_env": "paper",
    "portfolio_id": "main_crypto",
    "account_id": "paper_001",
    "position_group_id": "btc_ai_swing",
    "strategy_id": "agent_discretionary_v1",
    "asset": {
        "symbol": "BTC/USDT",
        "asset_class": "crypto",
        "exchange": "binance"
    }
})
```

提交反馈：

```python
agent.submit_feedback(
    decision_id=decision["decision_id"],
    feedback_type="accepted",
    comment="用户采纳建议，手动执行。"
)
```

记录交易结果：

```python
agent.record_trade({
    "run_env": "paper",
    "portfolio_id": "main_crypto",
    "account_id": "paper_001",
    "position_group_id": "btc_ai_swing",
    "strategy_id": "agent_discretionary_v1",
    "decision_id": decision["decision_id"],
    "symbol": "BTC/USDT",
    "asset_class": "crypto",
    "side": "BUY",
    "price": 65000,
    "quantity": 0.01,
    "realized_pnl": 0
})
```

---

# 六、API 接入

启动 API：

```bash
python -m src.api.server
```

Agent 接口：

```text
POST /api/v1/agent/init
POST /api/v1/agent/decisions
GET  /api/v1/agent/decisions
GET  /api/v1/agent/decisions/{decision_id}
POST /api/v1/agent/decisions/{decision_id}/feedback
POST /api/v1/agent/trades
POST /api/v1/agent/positions
GET  /api/v1/agent/positions
GET  /api/v1/agent/performance
GET  /api/v1/agent/audit
GET  /api/v1/agent/summary
```

创建建议请求：

```json
{
  "run_env": "paper",
  "portfolio_id": "main_crypto",
  "account_id": "paper_001",
  "position_group_id": "btc_ai_swing",
  "strategy_id": "agent_discretionary_v1",
  "asset": {
    "symbol": "BTC/USDT",
    "asset_class": "crypto",
    "exchange": "binance"
  },
  "user_instruction": "只给建议，不自动下单"
}
```

---

# 七、审计与总结

审计决策：

```text
GET /api/v1/agent/audit?record_type=decisions&run_env=paper&symbol=BTC/USDT
```

审计记忆：

```text
GET /api/v1/agent/audit?record_type=memories&memory_type=feedback
```

月度总结：

```text
GET /api/v1/agent/summary?period=month&run_env=paper
```

年度单品种总结：

```text
GET /api/v1/agent/summary?period=year&symbol=BTC/USDT
```

---

# 八、当前建议逻辑

```text
MarketDataAdapter
    ↓
多周期行情：15m / 1h / 4h / 1d
    ↓
tools/indicators.py
    ↓
MA / EMA / RSI / MACD / Bollinger / ATR / 支撑压力 / 趋势斜率
    ↓
skills/multi_timeframe_strategy.py
    ↓
多周期评分 + long_plan + short_plan
    ↓
skills/risk_review.py
    ↓
盈亏比、波动、追高/追空风险
    ↓
brain.py
    ↓
BUY / SELL / HOLD / REDUCE / OBSERVE
```

---

# 九、下一步建议

优先级最高：

1. 给 Agent 增加单元测试，覆盖 Skill、审计、周期总结。
2. 在 UI 增加 Agent 决策详情页，展示 `metadata.analysis`。
3. 增加报告生成 Skill：日/周/月/年 Markdown 报告写入 `reports/` 和 `agent_reports`。
4. 增加历史相似行情检索 Skill。
5. 增加 LLM 复盘 Skill，但仍保持“不直接下单”的边界。

