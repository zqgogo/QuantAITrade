# AI 量化交易 Agent 设计与实现说明

更新时间：2026-05-09

交接和外部接入说明见 [AGENT_HANDOFF.md](AGENT_HANDOFF.md)。

---

# 一、当前定位

当前 Agent 是一个自包含的“建议 + 审计 + 学习”子系统：

```text
Agent 获取上下文
    ↓
调用 Skill 分析
    ↓
生成多空建议
    ↓
写入 Agent 自己的数据库
    ↓
等待用户反馈
    ↓
反馈进入 Agent 记忆
```

当前阶段不下单、不直接控制资金。

---

# 二、运行边界

Agent 自己拥有：

- 决策逻辑
- Skill
- Tool
- 记忆
- 偏好
- 特点
- 决策记录
- 用户反馈
- 通过 Agent 记录的交易
- Agent 侧持仓
- 分析报告

外部量化系统只提供：

- 行情数据
- 账户/持仓上下文
- 手动反馈
- 可选的执行结果回填

---

# 三、目录结构

```text
src/agent/
├── service.py              # Agent 对外统一入口
├── runner.py               # Agent 独立 CLI 入口
├── brain.py                # Agent 编排层，调用 skill 并生成最终建议
├── schemas.py              # Agent 数据结构
├── database.py             # Agent 自有 SQLite 数据库
├── memory_store.py         # Agent 记忆、偏好、特点
├── adapters/               # 外部系统适配层
├── skills/                 # Agent 可调用技能
├── tools/                  # 无决策逻辑的工具函数
├── memory/                 # profile 与长期记忆文件
├── reports/                # Agent 生成的报告
└── data/agent.db           # Agent 自己的数据库
```

---

# 四、Skill 与 Tool 分工

## Skill

Skill 是 Agent 可调用的“能力模块”，可以包含策略判断，但不直接下单。

当前已实现：

```text
skills/
├── base.py                         # Skill 抽象接口
├── registry.py                     # Skill 注册与调用
├── multi_timeframe_strategy.py     # 多周期策略分析
├── risk_review.py                  # 风险复核
└── decision_policy.md              # 行为规则说明
```

调用方式：

```python
from src.agent.skills import skill_registry

analysis = skill_registry.run("multi_timeframe_strategy", {"market": market})
risk = skill_registry.run("risk_review", {"analysis": analysis, "action": action})
```

## Tool

Tool 是无决策逻辑的底层函数，只负责计算或取数。

当前已实现：

```text
tools/
└── indicators.py
```

包含：

- MA
- EMA
- RSI
- MACD
- 布林带
- ATR
- 支撑压力
- 趋势斜率

---

# 五、当前建议逻辑

```text
AgentService.create_decision()
    ↓
MarketDataAdapter 获取多周期行情
    ↓
PortfolioAdapter 获取 Agent 自有持仓
    ↓
MemoryStore 读取 profile / 偏好 / 记忆
    ↓
AgentBrain 调用 Skill
    ↓
multi_timeframe_strategy 生成市场分析
    ↓
risk_review 生成风险复核
    ↓
AgentBrain 汇总为 AgentDecision
    ↓
AgentDatabase 写入 agent_decisions
```

---

# 六、多周期策略 Skill

`multi_timeframe_strategy` 默认分析：

- `15m`
- `1h`
- `4h`
- `1d`

每个周期计算：

- 均线结构
- RSI
- MACD
- 布林带位置
- ATR
- 支撑压力
- 成交量倍率
- 趋势斜率

每个周期会得到一个 `score`。

再按周期权重合成：

```text
15m: 0.7
1h : 1.0
4h : 1.2
1d : 1.4
```

最终得到：

- `bullish`
- `bearish`
- `neutral`
- `insufficient_data`

---

# 七、多空建议

Agent 每次都会同时生成：

```text
long_plan
short_plan
```

每个计划包含：

- 入场区间
- 失效位
- 目标位
- 失效原因

最终动作可能是：

- `BUY`
- `SELL`
- `HOLD`
- `REDUCE`
- `OBSERVE`

注意：

> `SELL` 在当前阶段表示做空建议或空头方案，不代表 Agent 自动下单。

---

# 八、记录系统

Agent 自己的数据库位于：

```text
src/agent/data/agent.db
```

当前表包括：

- `agent_profile`
- `agent_memories`
- `agent_decisions`
- `agent_feedback`
- `agent_trade_records`
- `agent_positions`
- `agent_reports`
- `agent_performance_snapshots`

所有 Agent 产生的数据都在 Agent 目录内部。

---

# 九、反馈闭环

用户可以通过 API 或代码提交反馈：

```text
POST /api/v1/agent/decisions/{decision_id}/feedback
```

反馈会：

- 写入 `agent_feedback`
- 更新决策状态
- 写入 `agent_memories`

这样 Agent 后续可以读取历史反馈，逐步形成偏好和经验。

---

# 十、学习能力

当前学习是第一版“事件记忆”：

- 用户反馈会写入 `agent_memories`，类型为 `feedback`。
- 通过 Agent 记录的交易会写入 `agent_memories`，类型为 `trade_result`。
- Agent 每次决策会读取 profile 和最近重要记忆，放入 `memory_snapshot`。

后续可以继续增强为：

- 定期总结记忆
- 错误归因
- 有效信号归因
- 针对不同品种形成偏好

---

# 十一、审计能力

Agent 支持按条件审计自己的记录：

```text
GET /api/v1/agent/audit
```

支持的 `record_type`：

- `decisions`
- `feedback`
- `trades`
- `positions`
- `memories`
- `reports`

常用过滤条件：

- `run_env`
- `portfolio_id`
- `account_id`
- `position_group_id`
- `strategy_id`
- `symbol`
- `action`
- `side`
- `status`
- `feedback_type`
- `memory_type`
- `start_ts`
- `end_ts`

示例：

```text
/api/v1/agent/audit?record_type=decisions&run_env=paper&symbol=BTC/USDT
/api/v1/agent/audit?record_type=trades&position_group_id=btc_ai_swing
```

---

# 十二、周期总结

Agent 支持日、周、月、年总结：

```text
GET /api/v1/agent/summary?period=day
GET /api/v1/agent/summary?period=week
GET /api/v1/agent/summary?period=month
GET /api/v1/agent/summary?period=year
```

可按以下维度过滤：

- `run_env`
- `portfolio_id`
- `account_id`
- `position_group_id`
- `strategy_id`
- `symbol`

总结内容包括：

- 决策次数
- 交易次数
- 开仓/平仓数量
- 已实现盈亏
- 手续费
- 净盈亏
- 胜率
- 动作分布
- 标的分布
- 反馈分布

---

# 十三、当前缺口

还需要继续实现：

- LLM 深度复盘 Skill
- 历史相似行情检索 Skill
- 月度/年度报告生成 Skill
- 单笔交易复盘 Skill
- Agent 记忆总结与压缩
- UI 展示 Agent 的 `metadata.analysis`
- 更完整的回测结果回填
