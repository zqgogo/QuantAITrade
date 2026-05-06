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

