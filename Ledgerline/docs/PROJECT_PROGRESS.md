# Ledgerline 项目进度

更新时间：2026-07-03

## 当前结论

本项目已按《观澜-AI交易工作台设计文档 v0.2》的方向重新初始化。旧版 QuantAITrade 已整体移入仓库根目录的 `old/`，后续停止在旧结构上继续开发。

新的主项目放在 `Ledgerline/`，当前完成的是 Phase 1 的项目骨架，不包含具体业务实现。

## 技术方案

### 前端

- 选型：Next.js + React + TypeScript。
- 形态：单一响应式前端，桌面和手机共用一套代码。
- PWA：先预留 manifest 和移动端体验约束，离线缓存与推送在后续 Phase 8 实现。
- UI 方向：深色、数据密集、工具型工作台，核心页面包括 Dashboard、Trade、Portfolio、Watch、AI Chat、Reports、Settings。
- 依赖基线：按 2026-07-03 官方文档，Next.js 使用 App Router 当前线，Node.js 至少 20.9。
- 状态管理：Phase 1 暂不引入全局状态库；进入交易记录和行情页后，再按实际复杂度选择 TanStack Query + 轻量本地 store。

### 后端

- 选型：FastAPI + Pydantic + SQLAlchemy。
- 任务调度：APScheduler，后续驱动行情增量更新、Watch 扫描、AI Scheduled Trigger。
- 模块边界：Trading、Market Data、Indicator、Strategy、AI Trigger、Report、Notification、News、Watch。
- 鉴权：单用户 token 鉴权先预留，后续接入配置化密钥。
- 包管理：建议后续使用 `uv` 管理 Python 环境和锁文件，当前先保留标准 `pyproject.toml`。
- 数据迁移：Phase 1 后半段补 Alembic；模型稳定前不手写大量迁移。

### 数据

- `trading.db`：业务事实库，保存 Workspace、Portfolio、Position、Transaction、Watchlist、Report、Notification、Note。
- `market.db`：市场事实库，保存 OHLCV、News、Funding、OpenInterest、MacroEvent 等。
- ChromaDB：AI 记忆库，保存日报、周报、月报、新闻摘要、策略说明、聊天历史等可检索上下文。
- 原则：数据库只保存事实，不保存可重算指标、盈亏率、AI 派生判断等结果。
- SQLite 适配单用户和低并发写入；后续若多设备同步、多人使用或高频写入明显增加，再迁移 PostgreSQL。
- 本地开发建议开启 WAL；业务库和行情库继续物理拆分，避免市场数据膨胀影响交易记录。

### AI

- 接口：OpenAI Compatible provider 抽象。
- 第一阶段只预留模块边界。
- 后续先实现 On-Demand Trigger，跑通 Context Assembler -> Prompt Builder -> AI Client -> Output Parser -> Persist/Delivery。
- 向量数据库先通过 `MemoryStore` 接口隔离，默认实现可用 ChromaDB；不要让业务模块直接依赖 Chroma API。

## 技术方案复核结论

当前方案足够支撑 MVP，不建议换成纯 Node 后端、Electron 桌面优先或重型微服务架构。

保留：

- Next.js + React：适合 PWA、响应式页面、后续移动端安装。
- FastAPI：适合 Python 数据处理、指标计算、AI 调用和 OpenAPI 接口。
- SQLite 双库：适合单用户、本地优先、交易事实和行情事实分离。
- ChromaDB：适合 AI 长期上下文检索，但需要放在抽象接口后面。

调整：

- 前端依赖从 Next 15 校准到 Next 16 当前线。
- Phase 1 增加 Alembic、WAL、Repository/Service 分层和 `MemoryStore` 抽象。
- 图表库、全局状态库、UI 组件库暂缓到 Trade/Portfolio 页面开始时再定，避免骨架期过度设计。

## 目录状态

- `Ledgerline/apps/web`：前端框架已创建。
- `Ledgerline/apps/api`：后端框架已创建。
- `Ledgerline/docs`：进度文档与架构说明已创建。
- `old/`：旧项目归档目录。

## Phase 计划

| Phase | 名称 | 状态 | 验收标准 |
| --- | --- | --- | --- |
| 1 | 项目框架 | 进行中 | FastAPI + Next.js 骨架、数据库配置、模块目录、基础健康检查 |
| 2 | 交易记录 | 未开始 | 能记录一笔真实 Transaction，能按 Position 聚合持仓 |
| 3 | 市场数据仓库 | 未开始 | 第一个数据源接入，OHLCV 增量落库，支持手动刷新 |
| 4 | 技术指标 | 未开始 | MA/EMA/MACD/RSI 等指标 API 可用 |
| 5 | 策略系统 | 未开始 | 插件化策略接口和统一 Signal 输出 |
| 6 | AI 聊天 | 未开始 | On-Demand Trigger 和 AI Chat 最小闭环 |
| 7 | 日报/周报 | 未开始 | Scheduled Trigger 生成 Report |
| 8 | PWA 优化 | 未开始 | 可安装、移动端记录交易流程压缩到 20-30 秒 |
| 9 | 图表 | 未开始 | K 线与指标可视化 |
| 10 | 回测 | 延后 | 复用 Market Data Warehouse 做策略回测 |
| 11 | 桌面版 | 可选 | 视需要用 Tauri 打包 |

## 下一步

1. 完成 Phase 1：补齐 SQLAlchemy 模型草稿、数据库初始化命令、基础鉴权中间件。
2. 进入 Phase 2：优先实现 Workspace / Portfolio / Position / Transaction。
3. 前端先做 Trade 快速记录和 Portfolio 汇总页，不先做大而全的 Dashboard。
