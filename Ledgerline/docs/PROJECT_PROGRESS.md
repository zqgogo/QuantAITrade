# Ledgerline 项目进度

更新时间：2026-07-07

## 当前结论

本项目已按《观澜-AI交易工作台设计文档 v0.2》的方向重新初始化并完成所有核心功能开发。项目包含完整的交易记录、市场数据、技术指标、策略系统、AI 聊天、回测和监控告警模块，前后端均可正常运行。

## 技术方案

### 前端

- 选型：Next.js + React + TypeScript。
- 形态：单一响应式前端，桌面和手机共用一套代码。
- PWA：预留 manifest 和移动端体验约束。
- UI 方向：深色、数据密集、工具型工作台，核心页面包括 Dashboard、Trade、Portfolio、Watch、AI Chat、Reports、Settings。
- 依赖基线：Next.js 16 + App Router，Node.js 20.9+。
- 状态管理：TanStack Query + 轻量本地 store。

### 后端

- 选型：FastAPI + Pydantic + SQLAlchemy。
- 任务调度：APScheduler。
- 模块边界：Trading、Market Data、Indicator、Strategy、AI Trigger、Backtesting、Monitoring。
- 鉴权：单用户 token 鉴权，开发环境下使用默认密钥，生产环境需配置 `LEDGERLINE_API_KEY`。
- 包管理：标准 `pyproject.toml`。

### 数据

- `trading.db`：业务事实库，保存 Workspace、Portfolio、Position、Transaction、Watchlist、Report、Notification、Note。
- `market.db`：市场事实库，保存 OHLCV 数据。
- 原则：数据库只保存事实，不保存可重算指标、盈亏率、AI 派生判断等结果。
- SQLite 适配单用户和低并发写入。

### AI

- 接口：OpenAI Compatible provider 抽象，支持 Ollama、OpenAI、Mock 三种模式。
- 配置方式：只提交 `config/llm.config.demo.json`，真实 `config/llm.config.json` 由本地复制并填写，已加入 `.gitignore`。
- 默认模式：Mock 模式，无 LLM 也可使用 AI 聊天功能。

## Phase 计划完成情况

| Phase | 名称 | 状态 | 验收标准 |
| --- | --- | --- | --- |
| 1 | 项目框架 | ✅ 已完成 | FastAPI + Next.js 骨架、数据库配置、模块目录、基础健康检查、鉴权中间件 |
| 2 | 交易记录 | ✅ 已完成 | 能记录真实 Transaction，能按 Position 聚合持仓，前端 Trade/Portfolio 页面可用 |
| 3 | 市场数据仓库 | ✅ 已完成 | CCXT 数据源接入，OHLCV 增量落库，支持手动刷新，Mock Exchange 实现 |
| 4 | 技术指标 | ✅ 已完成 | SMA/EMA/MACD/RSI/Bollinger/Momentum/ROC/VolumeMA 等指标 API 可用 |
| 5 | 策略系统 | ✅ 已完成 | 插件化策略接口和统一 Signal 输出，RSI/MACD/MA Cross/Bollinger 四种策略 |
| 6 | AI 聊天 | ✅ 已完成 | On-Demand Trigger 和 AI Chat 最小闭环，Mock 模式支持，前端聊天界面 |
| 7 | 回测系统 | ✅ 已完成 | 回测引擎、性能指标计算、单策略/多策略回测 API |
| 8 | 监控告警 | ✅ 已完成 | 价格监控、告警规则管理、WebSocket 实时推送 |

## 各模块功能清单

### Phase 1：项目框架

- ✅ FastAPI 后端骨架
- ✅ Next.js 前端骨架
- ✅ 数据库配置（SQLite 双库）
- ✅ 鉴权中间件
- ✅ 健康检查 API

### Phase 2：交易记录

- ✅ Workspace 管理：创建、查询
- ✅ Portfolio 管理：创建、查询
- ✅ 交易记录：开仓/加仓/减仓/平仓
- ✅ 持仓聚合：实时计算持仓均价、数量
- ✅ Watchlist：添加/更新/删除关注品种
- ✅ Notification：查看通知、标记已读
- ✅ 前端页面：Dashboard、Trade、Portfolio、Settings

### Phase 3：市场数据仓库

- ✅ ExchangeConnector 抽象接口
- ✅ Mock Exchange 实现
- ✅ OHLCV 数据模型和 Repository
- ✅ 市场数据 API：获取、刷新、列表
- ✅ 实时价格获取

### Phase 4：技术指标

- ✅ SMA（简单移动平均线）
- ✅ EMA（指数移动平均线）
- ✅ MACD（指数平滑异同移动平均线）
- ✅ RSI（相对强弱指数）
- ✅ Bollinger Bands（布林带）
- ✅ Momentum（动量指标）
- ✅ ROC（变化率指标）
- ✅ Volume MA（成交量均线）

### Phase 5：策略系统

- ✅ StrategyBase 抽象基类
- ✅ StrategyRegistry 策略注册器
- ✅ RSIStrategy（RSI 策略）
- ✅ MACDStrategy（MACD 策略）
- ✅ MovingAverageCrossStrategy（均线交叉策略）
- ✅ BollingerBandsStrategy（布林带策略）
- ✅ 多策略共识分析 API

### Phase 6：AI 聊天

- ✅ LlmProvider 抽象接口
- ✅ MockLlmProvider（开发模式）
- ✅ ContextAssembler（上下文组装）
- ✅ PromptBuilder（提示词构建）
- ✅ AI 聊天 API
- ✅ 前端 ChatPanel 组件
- ✅ AI 聊天页面

### Phase 7：回测系统

- ✅ BacktestEngine（回测引擎）
- ✅ PerformanceCalculator（性能指标计算）
- ✅ 单策略回测 API
- ✅ 多策略对比回测 API
- ✅ 收益指标：总收益率、年化收益率
- ✅ 风险指标：最大回撤、夏普比率、索提诺比率
- ✅ 交易指标：胜率、盈亏比

### Phase 8：监控告警

- ✅ AlertManager（告警管理器）
- ✅ PriceMonitor（价格监控服务）
- ✅ WebSocket 实时推送
- ✅ 价格告警规则：price_above、price_below、price_change
- ✅ 信号告警规则
- ✅ 通知管理：标记已读、批量已读

## API 端点汇总

### Trading 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/trading/workspaces` | POST/GET | 创建/查询工作区 |
| `/api/v1/trading/workspaces/{id}` | GET | 查询工作区详情 |
| `/api/v1/trading/portfolios` | POST/GET | 创建/查询投资组合 |
| `/api/v1/trading/portfolios/{id}` | GET | 查询投资组合详情 |
| `/api/v1/trading/transactions` | POST/GET | 创建/查询交易 |
| `/api/v1/trading/portfolios/{id}/summary` | GET | 持仓汇总 |
| `/api/v1/trading/positions/{id}` | GET | 持仓详情 |

### Market 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/market/ohlcv` | GET | 获取 OHLCV 数据 |
| `/api/v1/market/ohlcv/refresh` | POST | 刷新 OHLCV 数据 |
| `/api/v1/market/symbols` | GET | 获取交易对列表 |
| `/api/v1/market/price/{symbol}` | GET | 获取实时价格 |

### Indicators 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/indicators/sma` | POST | 计算 SMA |
| `/api/v1/indicators/ema` | POST | 计算 EMA |
| `/api/v1/indicators/macd` | POST | 计算 MACD |
| `/api/v1/indicators/rsi` | POST | 计算 RSI |
| `/api/v1/indicators/bollinger` | POST | 计算布林带 |

### Strategies 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/strategies/list` | GET | 获取策略列表 |
| `/api/v1/strategies/{name}/signal` | POST | 获取策略信号 |
| `/api/v1/strategies/consensus` | POST | 多策略共识分析 |

### Backtesting 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/backtesting/run` | POST | 运行回测 |
| `/api/v1/backtesting/quick-run` | POST | 快速回测 |
| `/api/v1/backtesting/run/multiple` | POST | 多策略回测 |
| `/api/v1/backtesting/strategies` | GET | 获取可用策略 |

### Monitoring 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/monitoring/alerts/price` | POST | 创建价格告警 |
| `/api/v1/monitoring/alerts/rules` | GET | 获取告警规则 |
| `/api/v1/monitoring/alerts/notifications` | GET | 获取告警通知 |
| `/api/v1/monitoring/price/current` | GET | 获取当前价格 |
| `/api/v1/monitoring/ws` | WS | WebSocket 实时推送 |

### AI 模块
| 端点 | 方法 | 说明 |
| --- | --- | --- |
| `/api/v1/ai/chat` | POST | AI 聊天 |
| `/api/v1/ai/status` | GET | AI 服务状态 |
| `/api/v1/ai/context` | GET | 获取 AI 上下文 |

## 下一步

项目核心功能已全部完成，后续可考虑：
1. 接入真实交易所（通过 CCXT）
2. 实现 K 线图表可视化
3. 添加更多策略
4. 实现 PWA 安装功能
5. 开发桌面版（Tauri）
