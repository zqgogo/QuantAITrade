# QuantAITrade 项目进度

更新时间：2026-05-06

## 总体判断

当前项目已经从早期原型推进到“可运行闭环雏形”阶段。主干模块基本齐全，但还不能按生产级实盘系统看待：风控细节、订单/持仓同步、Web 图表、AI 建议效果追踪、集成测试和部署监控仍需要继续补强。

综合完成度按代码现状估计：约 75%-85%。

## 已完成

### 基础设施

- 项目结构、配置管理、日志系统、SQLite 数据库。
- `.env.example`、`requirements.txt`、`quickstart.sh` 已存在。
- 主入口 `main.py` 支持初始化数据库、获取数据和三种运行模式。

### 数据模块

- 行情获取模块 `data/fetcher.py`。
- 数据模型 `data/models.py`。
- 数据库管理 `data/db_manager.py`。
- 支持 K 线数据存储、查询、增量更新和历史回补相关能力。

### 策略与回测

- 策略基类 `src/strategy/base_strategy.py`。
- MA 交叉策略 `src/strategy/ma_cross_strategy.py`。
- 回测引擎 `src/backtest/engine.py`。
- 基础绩效指标、交易记录和权益曲线逻辑已经具备。

### 风控与交易执行

- 风控控制器 `src/execution/risk_controller.py`。
- 交易所连接器、订单管理器、持仓跟踪器、统一交易执行器。
- 支持风控检查、止损计算、信号提交、订单处理和持仓监控的主流程。

### 调度与状态管理

- APScheduler 调度器 `src/orchestrator/scheduler.py`。
- 系统状态、任务日志、信号队列、恢复管理、健康检查等工具模块。
- 主程序中已经接入心跳、数据获取、策略分析、订单同步、持仓监控、AI 分析等定时任务。

### AI 分析

- AI 数据准备、Prompt 构建、OpenAI 分析、建议解析模块已存在。
- 支持每日分析、快速分析/深度分析框架、分析结果存储。

### Web 与 API

- Streamlit UI 已有仪表盘、策略控制、AI 分析和设置页面。
- FastAPI 服务已存在，包含健康检查、JWT token、策略、订单、持仓、AI、系统状态等基础接口。

### 测试

- `test_system.py` 覆盖配置、数据库、策略、风控、回测引擎的基础冒烟测试。
- `test_task_state_management.py` 覆盖任务状态管理相关能力。

## 主要问题

### P0：实盘前必须处理

1. 风控模块仍有关键 TODO：
   - 市场价格获取与价格偏差检查。
   - 关键点位止损从历史数据计算。
   - ATR 止损从历史数据计算。
   - 今日交易次数从数据库查询。

2. 订单与持仓一致性还需要落地：
   - `main.py` 中订单同步和持仓验证任务仍是框架逻辑。
   - API 下单接口目前偏模拟返回，没有完整穿透到真实订单生命周期。

3. 生产安全配置不足：
   - API 默认密码和默认 JWT secret 需要强制配置。
   - CORS 当前放开为 `*`，生产环境需要收紧。
   - 实盘模式需要明确保护开关和二次确认机制。

### P1：本周优先

1. Web UI 的核心图表和统计仍有预留：
   - 策略绩效图表。
   - 权益曲线。
   - 最大回撤、胜率、夏普比率、总盈亏。
   - 信号分析图表和参数修改历史。

2. AI 建议闭环未完成：
   - 建议采纳率统计。
   - 建议效果追踪。
   - 参数调整、策略启停、风控设置调整等建议动作还未真正落地。

3. 测试覆盖不足：
   - 缺少端到端交易流程测试。
   - 缺少三种运行模式测试。
   - 缺少异常恢复、订单失败、交易所不可用等场景测试。

### P2：后续增强

1. 策略数量较少：
   - 目前主要是 MA 交叉策略。
   - MACD、布林带、均值回归、策略动态加载器仍可补充。

2. 性能和数据层优化：
   - 数据库索引和查询性能需要复查。
   - 可加入缓存、批处理、异步任务和数据归档。

3. 部署和监控：
   - 缺少 Docker/部署文档。
   - 缺少 Prometheus/Grafana 或等效监控。
   - 通知告警模块需要完整验证。

## 建议下一步

### 第一步：先跑通本地环境

```bash
source venv/bin/activate
pip install -r requirements.txt
python test_system.py
python test_task_state_management.py
python main.py --init-db
```

如果要验证行情获取：

```bash
python main.py --fetch-data
```

### 第二步：补齐核心风控

优先修改 `src/execution/risk_controller.py`：

- 接入交易所当前价格或最新 K 线价格，完成价格偏差检查。
- 复用策略基类里的支撑位/ATR 计算逻辑，补齐关键点位和 ATR 止损。
- 从 `trade_records` 查询今日交易次数。
- 增加针对风控拒绝/通过的单元测试。

### 第三步：把订单同步和持仓验证做实

优先修改：

- `main.py`
- `src/execution/order_manager.py`
- `src/execution/position_tracker.py`
- `src/execution/exchange_connector.py`

目标：

- 系统启动时恢复未完成订单。
- 定时同步交易所订单状态。
- 对比本地持仓和交易所持仓。
- 对异常状态给出告警或自动修复策略。

### 第四步：完善 UI 与 AI 闭环

优先修改：

- `src/ui/pages/dashboard.py`
- `src/ui/pages/strategy_control.py`
- `src/ui/pages/ai_analysis.py`
- `src/ai/ai_suggestion_parser.py`

目标：

- 用真实数据库数据生成仪表盘指标和图表。
- 实现参数修改历史。
- 追踪 AI 建议是否采纳、采纳后效果如何。
- 将可执行建议映射到配置更新或策略控制。

### 第五步：补集成测试

建议新增：

- 模拟交易所连接器测试。
- 信号生成到风控到下单的端到端测试。
- manual/auto/hybrid 三种模式调度测试。
- 异常中断后的状态恢复测试。

## 当前保留文档

- `README.md`：最新项目说明、运行方式和安全提示。
- `PROJECT_STATUS.md`：最新进度、问题和下一步计划。
- `AI_AGENT_REFACTOR_PLAN.md`：AI Agent 独立化改造设计、API 口子、记录模型和阶段进度。

历史实施报告、旧计划和旧状态文档已清理，避免与当前状态冲突。
