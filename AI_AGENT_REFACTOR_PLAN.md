# QuantAITrade AI Agent 改造设计文档（V1）

更新时间：2026-05-06

---

# 一、改造目标

把当前 QuantAITrade 从“量化交易系统里带 AI 分析能力”升级为：

> 独立可运行、可移植、可审计、可接入实盘/模拟盘/回测的 AI 交易 Agent 子系统。

核心要求：

- Agent 可以独立运行，不强绑定 QuantAITrade 主程序。
- Agent 可以被其他 App、Web 系统、脚本、调度器或交易系统通过 API 调用。
- Agent 不直接控制交易所资金，所有下单必须通过执行层和风控层。
- 同一套 Agent 能用于真实盘、模拟盘、回测三种环境。
- 交易、持仓、决策、风控、反馈、结果必须全量记录。
- 支持 BTC、ETH、原油、股票等不同资产类别。
- 支持同一品种的不同账户、不同策略、不同仓位分组独立统计。
- 支持按日、周、月、年查看收益、胜率、回撤、仓位表现和 Agent 表现。

---

# 二、当前项目基础

当前项目已经具备以下基础模块：

- `src/ai/`：AI 数据准备、Prompt 构建、分析调用、建议解析。
- `src/execution/`：交易执行、风控、订单管理、持仓跟踪、交易所连接。
- `src/backtest/`：基础回测引擎。
- `src/api/`：FastAPI 服务和基础 REST 接口。
- `data/`：SQLite 数据模型、K 线数据、交易记录等。
- `src/ui/`：Streamlit 仪表盘和分析页面。
- `main.py`：manual / auto / hybrid 运行模式和调度主入口。

当前缺口：

- Agent 层还不是独立子系统。
- AI 决策、策略信号、风控结果、执行结果之间缺少统一事件链路。
- 真实盘、模拟盘、回测记录没有统一的环境维度。
- 多账户、多资产、多仓位分组能力不足。
- 月度、年度、按账户、按策略、按仓位桶的归因分析还未形成标准接口。
- 外部 App 调用 Agent 的 API 协议还不完整。

---

# 三、核心设计原则

## 1. Agent 独立

Agent 必须能以三种方式运行：

- CLI 独立运行：`python -m src.agent.runner --mode paper`
- API 服务运行：外部系统通过 HTTP 调用 Agent。
- 内嵌运行：QuantAITrade 主系统直接导入 Agent SDK 调用。

Agent 不依赖具体 UI，不依赖固定交易所，不依赖固定数据库实现。

## 2. 决策与执行分离

Agent 只输出标准化决策：

- 建议买入
- 建议卖出
- 建议持有
- 建议减仓
- 建议止损
- 建议观察

Agent 禁止直接调用交易所下单接口。

执行必须经过：

```text
AgentDecision -> RiskCheck -> ExecutionIntent -> Executor -> Order -> Fill -> Position
```

## 3. 所有动作可审计

任何一次 Agent 思考、风控拒绝、用户确认、下单、成交、平仓、回测撮合都要有记录。

每条记录必须能追溯：

- 谁触发的
- 在什么环境触发
- 使用了哪些数据
- Agent 给了什么理由
- 风控是否通过
- 是否执行
- 执行结果如何
- 后续收益如何

## 4. 运行环境隔离

统一使用 `run_env` 区分环境：

- `live`：真实盘
- `paper`：模拟盘
- `backtest`：回测

所有账户、订单、持仓、成交、收益、Agent 决策都必须带 `run_env`。

禁止把真实盘、模拟盘、回测数据混在同一统计口径里。

## 5. 多维度账户与仓位管理

同一个资产可以有多个独立仓位：

- BTC 趋势仓
- BTC 网格仓
- BTC AI 建议仓
- ETH 策略 A 仓
- 原油短线仓
- 股票长线仓

统一通过 `portfolio_id`、`account_id`、`position_group_id`、`strategy_id` 区分。

---

# 四、目标架构

```text
External App / Web / CLI / Scheduler
        |
        v
Agent API / Agent SDK
        |
        v
Agent Core
  - Brain
  - Memory
  - Planner
  - Tool Registry
  - Decision Formatter
        |
        v
Quant Adapter Layer
  - MarketDataProvider
  - PortfolioProvider
  - ExecutionGateway
  - JournalRepository
  - BacktestGateway
        |
        v
Trading System
  - Data
  - Strategy
  - Risk
  - Execution
  - Backtest
  - Analysis
```

---

# 五、推荐目录结构

在现有项目中新增：

```text
src/agent/
├── __init__.py
├── runner.py                 # Agent 独立运行入口
├── core.py                   # Agent 主类
├── brain.py                  # AI 推理和决策
├── planner.py                # 任务规划和工具调用编排
├── memory.py                 # Agent 记忆读取与更新
├── schemas.py                # Agent 输入/输出标准模型
├── service.py                # AgentService，供 API 和主系统调用
├── prompts/
│   ├── decision_prompt.md
│   └── review_prompt.md
├── adapters/
│   ├── market_data.py        # 行情适配器接口
│   ├── portfolio.py          # 账户/持仓适配器接口
│   ├── execution.py          # 执行适配器接口
│   ├── journal.py            # 记录仓储接口
│   └── backtest.py           # 回测适配器接口
└── tools/
    ├── indicators.py
    ├── position_summary.py
    ├── risk_snapshot.py
    └── performance_summary.py

src/journal/
├── __init__.py
├── repository.py             # 交易/决策/结果统一记录
├── analyzer.py               # 日/周/月/年统计
├── schemas.py
└── migrations/
    └── 001_agent_journal.sql
```

---

# 六、Agent 标准输入输出

## 1. Agent 输入

```json
{
  "request_id": "req_20260506_000001",
  "run_env": "paper",
  "agent_id": "default_agent",
  "portfolio_id": "main_crypto",
  "account_id": "binance_testnet_001",
  "position_group_id": "btc_ai_swing",
  "strategy_id": "ai_discretionary_v1",
  "asset": {
    "symbol": "BTC/USDT",
    "asset_class": "crypto",
    "exchange": "binance"
  },
  "task_type": "decision",
  "market_context": {},
  "portfolio_context": {},
  "risk_context": {},
  "memory_context": {},
  "user_instruction": "只给建议，不自动下单"
}
```

## 2. Agent 输出

```json
{
  "decision_id": "dec_20260506_000001",
  "request_id": "req_20260506_000001",
  "run_env": "paper",
  "action": "BUY",
  "confidence": 0.72,
  "symbol": "BTC/USDT",
  "suggested_price": 63500.0,
  "suggested_quantity": 0.01,
  "timeframe": "1h",
  "reasoning": "趋势向上，回撤后重新站上均线，成交量放大。",
  "risk_notes": "若跌破 62000 应止损；单笔风险不超过账户权益 1%。",
  "stop_loss": {
    "type": "price",
    "price": 62000.0
  },
  "take_profit": {
    "type": "price",
    "price": 67000.0
  },
  "requires_human_confirmation": true,
  "metadata": {
    "model": "gpt",
    "prompt_version": "decision_v1"
  }
}
```

---

# 七、API 口子设计

Agent 对外暴露独立 API，其他系统可以只接这些接口。

## 1. 创建 Agent 决策

```text
POST /api/v1/agent/decisions
```

用途：

- 外部 App 请求 Agent 对某个品种、账户、仓位组进行分析。
- 返回标准化交易建议。
- 自动写入 `agent_decisions`。

## 2. 获取决策详情

```text
GET /api/v1/agent/decisions/{decision_id}
```

用途：

- 查看 Agent 当时的推理、数据快照、建议动作、置信度。

## 3. 提交用户反馈

```text
POST /api/v1/agent/decisions/{decision_id}/feedback
```

用途：

- 用户确认执行、拒绝执行、修改数量、修改价格、记录主观原因。

反馈类型：

- `accepted`
- `rejected`
- `modified`
- `executed_manually`
- `ignored`

## 4. 创建执行意图

```text
POST /api/v1/execution/intents
```

用途：

- 把 Agent 建议或策略信号转成执行意图。
- 执行意图必须进入风控，不能直接下单。

## 5. 获取账户/仓位汇总

```text
GET /api/v1/portfolios/summary
```

过滤参数：

- `run_env`
- `portfolio_id`
- `account_id`
- `asset_class`
- `symbol`
- `strategy_id`
- `position_group_id`
- `period`

## 6. 获取月度/年度统计

```text
GET /api/v1/analytics/performance?run_env=paper&period=month&year=2026
GET /api/v1/analytics/performance?run_env=live&period=year&year=2026
```

用途：

- 查看月度收益、年度收益、胜率、最大回撤、交易次数、平均盈亏。

---

# 八、记录模型设计

## 1. 统一维度字段

以下字段应出现在所有核心业务表中：

| 字段 | 说明 |
| --- | --- |
| `run_env` | `live` / `paper` / `backtest` |
| `portfolio_id` | 组合 ID，例如 `main_crypto` |
| `account_id` | 账户 ID，例如 `binance_live_001` |
| `strategy_id` | 策略 ID |
| `position_group_id` | 仓位组 ID，用于区分 BTC 不同仓 |
| `asset_class` | `crypto` / `stock` / `futures` / `commodity` / `forex` |
| `symbol` | 标的，例如 `BTC/USDT`、`ETH/USDT`、`CL`、`AAPL` |
| `exchange` | 交易所或数据源 |
| `currency` | 计价货币，例如 `USDT`、`USD`、`CNY` |
| `source_type` | `agent` / `strategy` / `manual` / `api` / `backtest` |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

## 2. accounts（账户）

| 字段 | 说明 |
| --- | --- |
| `id` | 主键 |
| `account_id` | 账户唯一 ID |
| `run_env` | 真实盘/模拟盘/回测 |
| `broker` | Binance、IBKR、OKX 等 |
| `account_name` | 展示名称 |
| `base_currency` | 账户基准币种 |
| `is_active` | 是否启用 |

## 3. portfolios（组合）

| 字段 | 说明 |
| --- | --- |
| `portfolio_id` | 组合 ID |
| `name` | 组合名称 |
| `run_env` | 环境 |
| `description` | 描述 |

## 4. position_groups（仓位组）

用于区分同一资产的不同仓。

| 字段 | 说明 |
| --- | --- |
| `position_group_id` | 仓位组 ID |
| `portfolio_id` | 所属组合 |
| `account_id` | 所属账户 |
| `symbol` | 标的 |
| `strategy_id` | 策略 |
| `group_name` | 例如 `BTC 趋势仓`、`BTC AI 仓` |
| `max_capital_ratio` | 最大资金占比 |
| `risk_budget` | 风险预算 |

## 5. agent_decisions（Agent 决策）

| 字段 | 说明 |
| --- | --- |
| `decision_id` | 决策 ID |
| `request_id` | 请求 ID |
| `run_env` | 环境 |
| `agent_id` | Agent ID |
| `portfolio_id` | 组合 |
| `account_id` | 账户 |
| `position_group_id` | 仓位组 |
| `strategy_id` | 策略 |
| `symbol` | 标的 |
| `action` | BUY / SELL / HOLD / REDUCE / CLOSE |
| `confidence` | 置信度 |
| `reasoning` | 决策理由 |
| `market_snapshot` | 行情快照 JSON |
| `portfolio_snapshot` | 账户/持仓快照 JSON |
| `risk_snapshot` | 风控快照 JSON |
| `prompt_version` | Prompt 版本 |
| `model_name` | 模型名称 |
| `status` | pending / accepted / rejected / executed / expired |

## 6. execution_intents（执行意图）

| 字段 | 说明 |
| --- | --- |
| `intent_id` | 执行意图 ID |
| `decision_id` | 来源决策，可为空 |
| `signal_id` | 来源策略信号，可为空 |
| `run_env` | 环境 |
| `action` | BUY / SELL / CLOSE |
| `order_type` | MARKET / LIMIT 等 |
| `requested_price` | 期望价格 |
| `requested_quantity` | 期望数量 |
| `requires_confirmation` | 是否需要人工确认 |
| `status` | created / risk_checked / approved / rejected / submitted |

## 7. risk_checks（风控记录）

| 字段 | 说明 |
| --- | --- |
| `risk_check_id` | 风控检查 ID |
| `intent_id` | 执行意图 ID |
| `passed` | 是否通过 |
| `reason` | 通过/拒绝原因 |
| `risk_rules` | 命中的规则 JSON |
| `risk_score` | 风险分 |
| `checked_at` | 检查时间 |

## 8. orders（订单）

订单记录要同时支持真实盘、模拟盘、回测撮合。

| 字段 | 说明 |
| --- | --- |
| `order_id` | 本地订单 ID |
| `external_order_id` | 交易所订单 ID |
| `intent_id` | 来源执行意图 |
| `run_env` | 环境 |
| `symbol` | 标的 |
| `side` | BUY / SELL |
| `order_type` | 订单类型 |
| `price` | 委托价格 |
| `quantity` | 委托数量 |
| `filled_quantity` | 成交数量 |
| `avg_fill_price` | 平均成交价 |
| `status` | new / submitted / partial / filled / canceled / rejected |

## 9. fills（成交）

| 字段 | 说明 |
| --- | --- |
| `fill_id` | 成交 ID |
| `order_id` | 订单 ID |
| `external_trade_id` | 交易所成交 ID |
| `price` | 成交价 |
| `quantity` | 成交数量 |
| `fee` | 手续费 |
| `fee_currency` | 手续费币种 |
| `filled_at` | 成交时间 |

## 10. positions（持仓）

现有 `positions` 表需要扩展，而不是只按 `symbol` 判断唯一持仓。

| 字段 | 说明 |
| --- | --- |
| `position_id` | 持仓 ID |
| `run_env` | 环境 |
| `portfolio_id` | 组合 |
| `account_id` | 账户 |
| `position_group_id` | 仓位组 |
| `strategy_id` | 策略 |
| `symbol` | 标的 |
| `side` | long / short |
| `entry_price` | 入场均价 |
| `quantity` | 当前数量 |
| `status` | open / closed |
| `opened_at` | 开仓时间 |
| `closed_at` | 平仓时间 |
| `realized_pnl` | 已实现盈亏 |
| `unrealized_pnl` | 未实现盈亏 |
| `max_drawdown` | 持仓最大回撤 |

## 11. performance_snapshots（绩效快照）

用于快速查看日/月/年统计。

| 字段 | 说明 |
| --- | --- |
| `snapshot_id` | 快照 ID |
| `run_env` | 环境 |
| `portfolio_id` | 组合 |
| `account_id` | 账户 |
| `position_group_id` | 仓位组，可为空 |
| `strategy_id` | 策略，可为空 |
| `symbol` | 标的，可为空 |
| `period_type` | day / week / month / year |
| `period_start` | 周期开始 |
| `period_end` | 周期结束 |
| `starting_equity` | 期初权益 |
| `ending_equity` | 期末权益 |
| `realized_pnl` | 已实现盈亏 |
| `unrealized_pnl` | 未实现盈亏 |
| `total_return` | 收益率 |
| `win_rate` | 胜率 |
| `trade_count` | 交易次数 |
| `max_drawdown` | 最大回撤 |

---

# 九、统计与查询口径

必须支持以下汇总：

## 1. 按环境

- 真实盘收益
- 模拟盘收益
- 回测收益

三者必须独立展示，不默认合并。

## 2. 按资产

- BTC 总收益
- ETH 总收益
- 原油总收益
- 股票总收益

## 3. 按仓位组

示例：

- BTC 趋势仓
- BTC AI 仓
- BTC 网格仓

每个仓位组单独统计：

- 当前持仓
- 累计盈亏
- 月度盈亏
- 年度盈亏
- 胜率
- 最大回撤
- 平均持仓时间

## 4. 按策略

- MA 交叉策略收益
- AI discretionary 策略收益
- 手动交易收益
- 回测策略收益

## 5. 按 Agent

- Agent 建议次数
- 采纳次数
- 拒绝次数
- 修改后执行次数
- 采纳率
- 采纳后胜率
- 采纳后总收益
- 按月表现

---

# 十、Agent 运行模式

## 1. 建议模式

```text
Agent -> 输出建议 -> 用户确认/拒绝 -> 记录反馈 -> 后续追踪结果
```

适合当前阶段。

## 2. 模拟盘模式

```text
Agent -> 风控 -> 模拟撮合 -> 模拟持仓 -> 统计结果
```

适合验证 Agent 是否稳定。

## 3. 回测模式

```text
历史数据 -> Agent/策略 -> 回测撮合 -> 回测持仓 -> 绩效统计
```

注意：

- 回测中使用 Agent 要控制成本和速度。
- 可以先用规则策略回测，Agent 只做关键节点分析。

## 4. 实盘模式

```text
Agent -> 风控 -> 人工确认或自动确认 -> 真实执行 -> 监控 -> 审计
```

实盘必须满足：

- 明确 `run_env=live`
- 强制启用风控
- 强制记录完整审计链路
- 支持全局熔断
- 支持手动接管
- 支持最大亏损限制

---

# 十一、改造实施路线

## 阶段 1：文档与模型定版

目标：

- 明确 Agent 边界。
- 明确数据库记录模型。
- 明确 API 口子。
- 明确真实盘、模拟盘、回测隔离方式。

交付：

- `AI_AGENT_REFACTOR_PLAN.md`
- `src/agent/schemas.py` 草案
- `src/journal/schemas.py` 草案
- 数据库迁移 SQL 草案

## 阶段 2：Agent 独立服务

目标：

- 新增 `src/agent/`。
- 将现有 `src/ai/` 能力包装为 `AgentService`。
- 支持 CLI 调用和 API 调用。

交付：

- `AgentService.create_decision()`
- `AgentService.submit_feedback()`
- `AgentService.review_result()`
- `/api/v1/agent/decisions`

## 阶段 3：统一记录系统

目标：

- 新增 `src/journal/`。
- 建立 Agent 决策、执行意图、风控、订单、成交、持仓、绩效快照的统一记录链路。
- 扩展现有表，保留历史兼容。

交付：

- JournalRepository
- 月度/年度统计查询
- 多环境、多账户、多资产、多仓位组过滤

## 阶段 4：模拟盘与回测接入

目标：

- 使用同一套记录模型区分 `paper` 和 `backtest`。
- 回测结果写入标准订单、成交、持仓、绩效表。
- 模拟盘生成模拟订单和模拟成交。

交付：

- PaperExecutionGateway
- BacktestExecutionGateway
- 回测绩效归档

## 阶段 5：实盘前安全加固

目标：

- 实盘开关隔离。
- 强制二次确认。
- 全局熔断。
- API 权限收紧。
- 订单/持仓和交易所状态一致性校验。

交付：

- LiveTradingGuard
- RiskPolicy
- 实盘模式集成测试

---

# 十二、当前改造进度

| 模块 | 当前状态 | 进度 | 说明 |
| --- | --- | --- | --- |
| 项目基础结构 | 已有 | 80% | 主流程、配置、日志、数据、策略、执行、API 已存在 |
| AI 分析模块 | 已有 | 60% | 需要封装成独立 AgentService |
| Agent 独立运行 | 未开始 | 0% | 待新增 `src/agent/runner.py` |
| Agent API | 未开始 | 0% | 待新增 `/api/v1/agent/*` |
| 统一记录模型 | 部分已有 | 35% | 已有交易、持仓、AI 分析表，但维度不足 |
| 多环境隔离 | 不完整 | 20% | 缺少统一 `run_env` 字段 |
| 多账户/多组合 | 不完整 | 10% | 缺少 account/portfolio 标准模型 |
| 多仓位组 | 不完整 | 10% | 当前持仓偏按 symbol 处理，需支持同一 symbol 多仓 |
| 模拟盘记录 | 部分已有 | 30% | 需要和真实盘、回测统一表结构 |
| 回测记录归档 | 部分已有 | 40% | 已有 backtest_results，但未统一到订单/成交/持仓链路 |
| 月度/年度统计 | 未完成 | 15% | 需要新增 analyzer 和绩效快照 |
| 实盘安全保护 | 待加强 | 35% | 风控已有基础，仍需实盘保护和熔断 |

---

# 十三、优先级

## P0：先做

1. 新增 `src/agent/schemas.py`，定义 Agent 输入输出模型。
2. 新增 `src/agent/service.py`，封装现有 AI 分析能力。
3. 新增 Agent 决策 API。
4. 新增 `run_env`、`portfolio_id`、`account_id`、`position_group_id`、`strategy_id` 标准字段。
5. 设计数据库迁移脚本，不破坏现有数据。

## P1：随后

1. 新增 `src/journal/repository.py`。
2. 扩展订单、成交、持仓记录。
3. 支持同一 symbol 多仓位组。
4. 实现月度、年度统计接口。
5. 把回测结果写入标准 Journal。

## P2：增强

1. Agent 记忆系统。
2. Agent 建议效果追踪。
3. 多 Agent 分工：Market Agent、Strategy Agent、Risk Agent、Review Agent。
4. 外部系统 SDK。
5. Web UI 增加 Agent 决策审计页和绩效归因页。

---

# 十四、下一步建议

下一步不要急着接真实盘，应先完成可移植 Agent 骨架：

1. 建 `src/agent/`。
2. 建 `src/journal/`。
3. 做数据库迁移草案。
4. 先让 Agent 在 `paper` 模式下跑完整链路。
5. 再把回测和真实盘接入同一套记录模型。

推荐第一批可交付文件：

```text
src/agent/schemas.py
src/agent/service.py
src/agent/runner.py
src/journal/schemas.py
src/journal/repository.py
src/journal/analyzer.py
src/journal/migrations/001_agent_journal.sql
```

---

# 十五、最终形态

最终系统应当达到：

- Agent 是独立模块，可以被 QuantAITrade 使用，也可以迁移到其他系统。
- 外部系统只需要接 Agent API，就能请求分析、获取建议、反馈结果。
- 真实盘、模拟盘、回测数据严格隔离。
- BTC、ETH、原油、股票等资产可以共用同一套记录模型。
- 同一 BTC 下的不同仓位可以独立管理和统计。
- 用户可以快速查看月度、年度、按账户、按策略、按 Agent 的结果。
- 每一次决策都能追溯到当时的数据、理由、风控和执行结果。

