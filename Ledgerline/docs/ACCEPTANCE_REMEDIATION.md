# Ledgerline Acceptance and Remediation Checklist

更新时间：2026-07-24

## 当前结论

Ledgerline 当前已经完成主要模块骨架和核心功能原型，但还不能视为可交付完成。后端、前端、AI Mock、交易记录、市场数据、技术指标、策略、回测、监控告警等模块均已存在；阻塞验收的主要问题是前后端接口契约漂移、默认配置不一致、测试过时、文档与实现不一致。

完成下面的 Must Fix 项后，项目可进入完整功能验收。

## Must Fix

### 1. 统一 API Key 默认值

现状：

- 后端默认 `LEDGERLINE_API_KEY` 为 `dev-secret-key`。
- 前端默认 `NEXT_PUBLIC_API_KEY` 为 `dev-key`。
- README 中还出现过 `ledgerline-secret-key`。

整改：

- 选择一个开发默认值，建议统一为 `dev-secret-key`。
- 修改前端默认值。
- 同步 README、TEST_GUIDE 和所有 curl 示例。

验收：

- 不额外配置环境变量时，前端能正常访问后端受保护 API。
- `curl -H "X-API-Key: dev-secret-key" http://localhost:8000/api/v1/ai/status` 返回 200。

### 2. 修复前端 Trade 页面仓位接口

现状：

- `apps/web/src/app/trade/page.tsx` 使用 `tradingApi.positions.list(portfolioId)`。
- `apps/web/src/lib/api.ts` 声明该方法请求 `/trading/positions`。
- 后端当前没有 `GET /api/v1/trading/positions?portfolio_id=...`。
- 前端把返回值当作 `PositionAggregate[]` 使用，但类型声明是 `Position[]`。

整改：

- 推荐改为从 `GET /api/v1/trading/portfolios/{portfolio_id}/summary` 读取 `positions`。
- 或者后端补充 `GET /api/v1/trading/positions?portfolio_id=...`，并返回与前端一致的聚合结构。
- `PositionAggregate` 类型应包含后端实际返回的 `portfolio_id`、`market`、`current_price` 字段。

验收：

- `npm run typecheck:web` 通过。
- Trade 页面 Existing Position 模式可列出已有 open position。
- 选择已有仓位后，加仓、减仓、平仓记录请求可提交成功。

### 3. 修复前端 Watchlist 和 Notification 调用

现状：

- 前端声明了 `/trading/watchlist` 列表接口，但后端列表接口是 `/trading/portfolios/{portfolio_id}/watchlist`。
- 前端声明了 `/trading/notifications` 列表接口，但后端列表接口是 `/trading/portfolios/{portfolio_id}/notifications`。

整改：

- 前端 API client 增加 `portfolioId` 参数并调用真实后端路径。
- 或者后端补充全局列表接口，但要明确默认 portfolio 规则。

验收：

- Watchlist 创建、列表、更新、删除完整可用。
- Notification 列表、单条已读、全部已读完整可用。

### 4. 修复 AI 配置测试

现状：

- `config/llm.config.demo.json` 当前默认 `active_provider` 是 `mock`。
- `apps/api/tests/test_ai_config.py` 仍断言默认值为 `ollama`。

整改：

- 若开发默认策略是 Mock，则测试改为断言 `mock`。
- 若产品默认策略改回 Ollama，则修改 demo config 和文档。
- 建议保留 Mock 默认，保证无本地 LLM 时也能跑通。

验收：

- `PYTHONPATH=. pytest -q` 通过。
- `pytest -q` 也应通过，不依赖手动设置 `PYTHONPATH`。

### 5. 配置后端测试导入路径

现状：

- 在 `apps/api` 下直接执行 `pytest -q` 会报 `ModuleNotFoundError: No module named 'app'`。
- 使用 `PYTHONPATH=. pytest -q` 才能进入真实测试。

整改：

- 在 `apps/api/pyproject.toml` 增加 pytest 配置，设置 `pythonpath = ["."]`。
- 或调整测试启动脚本，固定使用可编辑安装后的环境。

验收：

- 在 `apps/api` 目录直接执行 `pytest -q` 通过。

### 6. 更新测试指南中的接口

现状：

- `docs/TEST_GUIDE.md` 中部分接口方法、路径、请求体与实际实现不一致。
- 指标、策略、市场价格、watchlist、notifications 等章节需要重新对齐。

整改：

- 以 FastAPI `/docs` 和真实 router 为准，逐项更新 TEST_GUIDE。
- 删除不存在接口，或标注为待实现。
- 每个模块保留最小可执行 curl 示例。

验收：

- 按 TEST_GUIDE 从头执行，不应遇到路径不存在、方法错误或鉴权 key 错误。

## Should Fix

### 1. 增加交易模块自动化测试

建议覆盖：

- 创建 workspace。
- 创建 portfolio。
- open 创建仓位。
- add 增加仓位。
- reduce 减少仓位。
- close 平仓。
- portfolio summary 聚合数量、均价、金额、状态。

完成标准：

- 交易主流程有 API 级测试。
- 聚合逻辑有边界测试，例如减仓超过持仓、无效 type、无效 portfolio。

### 2. 增加市场、指标、策略、回测测试

建议覆盖：

- Mock market OHLCV 可生成稳定数据。
- SMA、EMA、RSI、MACD、Bollinger 等接口返回结构正确。
- 策略输出只包含规范 signal。
- 回测返回收益、回撤、交易次数等核心指标。

完成标准：

- 不依赖真实交易所网络也能通过测试。

### 3. 明确生产构建命令

现状：

- `npm run build:web` 在当前受限环境中触发 Turbopack sandbox panic。
- 类型检查未通过前，生产构建也不能作为通过标准。

整改：

- 先修复 TypeScript 错误。
- 在正常本机环境执行 `npm run build:web`。
- 如果 Turbopack 仍不稳定，评估是否切换 Next.js 构建配置或固定版本。

完成标准：

- `npm run typecheck:web` 通过。
- `npm run build:web` 在本机非沙箱环境通过。

### 4. 补齐或调整 Watch 页面

现状：

- 架构文档写有 Watch 页面。
- 当前 `apps/web/src/app` 下没有 `watch/page.tsx`。

整改：

- 若 Watch 是 MVP 必需，新增 Watch 页面并接入 watchlist/alert rules。
- 若不属于当前 MVP，从架构文档和导航中移除或标注为后续功能。

完成标准：

- 文档、导航、实际页面三者一致。

## 验收测试步骤

### 1. 环境准备

```bash
cd /Volumes/sansun/work/QuantAITrade/Ledgerline
cp config/llm.config.demo.json config/llm.config.json
```

### 2. 后端测试

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest -q
```

通过标准：

- 所有测试通过。
- 无需手动设置 `PYTHONPATH`。

### 3. 后端启动

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
curl -H "X-API-Key: dev-secret-key" http://localhost:8000/api/v1/ai/status
```

### 4. 前端检查

```bash
cd /Volumes/sansun/work/QuantAITrade/Ledgerline
npm install
NEXT_PUBLIC_API_KEY=dev-secret-key npm run typecheck:web
NEXT_PUBLIC_API_KEY=dev-secret-key npm run dev:web
```

通过标准：

- TypeScript 无错误。
- 浏览器访问 `http://localhost:3000` 正常。
- Dashboard、Trade、Portfolio、Chat、Reports、Notifications、Settings 页面无控制台 API 鉴权错误。

### 5. 核心功能手工验收

按顺序验证：

1. 创建 workspace。
2. 创建 portfolio。
3. 记录 open 交易。
4. 查看 portfolio summary，确认生成 open position。
5. 在 Trade 页面 Existing Position 选择已有仓位。
6. 记录 add/reduce/close 交易。
7. 查询交易列表和持仓详情。
8. 添加 watchlist，更新价格阈值，删除 watchlist。
9. 调用 AI Chat，确认 Mock 模式返回内容。
10. 调用指标、策略、回测接口，确认返回结构完整。
11. 创建 monitoring alert rule，查询规则和通知。

## 最终完成标准

项目达到基本完成需要同时满足：

- `pytest -q` 通过。
- `npm run typecheck:web` 通过。
- `npm run build:web` 在正常本机环境通过。
- README、PROJECT_PROGRESS、TEST_GUIDE 与实际接口一致。
- 前端所有页面无默认鉴权错误。
- 交易主流程、AI Mock、指标、策略、回测、监控告警至少有最小可执行验收记录。
- 明确声明项目边界：Ledgerline 是个人 AI 交易工作台，不自动下单，不执行真实交易。
