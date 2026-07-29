# Ledgerline

基于观澜设计文档的个人 AI 交易工作台。

Ledgerline 不是自动交易机器人，不执行下单操作。它是一个单用户工作台，用于记录交易、积累市场数据、查看持仓，并使用 AI 作为分析辅助工具。

## 架构

- `apps/web`: Next.js + React + TypeScript 前端。
- `apps/api`: FastAPI 后端，包含模块化核心服务。
- `docs`: 产品、架构和进度文档。
- `config`: LLM 配置文件。

## 功能特性

- **交易模块**：工作区管理、投资组合跟踪、交易记录、持仓聚合计算
- **市场数据**：OHLCV 数据存储、实时价格获取、交易所连接器抽象
- **技术指标**：SMA、EMA、MACD、RSI、布林带、动量指标、ROC、成交量均线
- **策略系统**：插件化策略架构，包含 RSI、MACD、均线交叉、布林带策略
- **AI 聊天**：AI 驱动的交易助手，支持上下文感知分析
- **回测系统**：策略回测，包含全面的性能指标
- **监控告警**：实时价格监控、告警规则、WebSocket 实时推送

## 本地开发

### 前置条件

- Python 3.12+
- Node.js 20.9+

### 环境设置

**1. 复制 AI 配置文件**

```bash
cp config/llm.config.demo.json config/llm.config.json
```

`llm.config.json` 已加入 Git 忽略列表。请在此文件中保存真实的 API 密钥、本地模型名称和代理运行时配置。

**2. 安装后端依赖**

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**3. 安装前端依赖**

```bash
cd apps/web
npm install
```

### 启动应用

**启动后端服务**

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端服务**

```bash
cd apps/web
npm run dev
```

### 默认访问地址

- Web 前端: http://localhost:3000
- API 接口: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## API 认证

所有 API 端点都需要在 `X-API-Key` 请求头中提供 API 密钥：

```bash
curl -H "X-API-Key: dev-secret-key" http://localhost:8000/api/v1/trading/portfolios
```

生产环境中，请设置 `LEDGERLINE_API_KEY` 环境变量。

## API 端点

### 交易模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/trading/workspaces` | POST/GET | 创建/查询工作区 |
| `/api/v1/trading/workspaces/{id}` | GET | 查询工作区详情 |
| `/api/v1/trading/portfolios` | POST/GET | 创建/查询投资组合 |
| `/api/v1/trading/portfolios/{id}` | GET | 查询投资组合详情 |
| `/api/v1/trading/portfolios/{id}/summary` | GET | 获取投资组合汇总 |
| `/api/v1/trading/transactions` | POST/GET | 创建/查询交易记录 |
| `/api/v1/trading/positions/{id}` | GET | 查询持仓详情 |
| `/api/v1/trading/watchlist` | POST | 添加关注品种 |

### 市场模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/market/ohlcv` | GET | 获取 OHLCV 数据 |
| `/api/v1/market/ohlcv/refresh` | POST | 刷新 OHLCV 数据 |
| `/api/v1/market/symbols` | GET | 获取可用交易对列表 |
| `/api/v1/market/price/{symbol}` | GET | 获取实时价格 |

### 指标模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/indicators/sma` | POST | 计算 SMA 指标 |
| `/api/v1/indicators/ema` | POST | 计算 EMA 指标 |
| `/api/v1/indicators/macd` | POST | 计算 MACD 指标 |
| `/api/v1/indicators/rsi` | POST | 计算 RSI 指标 |
| `/api/v1/indicators/bollinger` | POST | 计算布林带指标 |
| `/api/v1/indicators/all` | POST | 计算所有指标 |

### 策略模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/strategies/list` | GET | 获取可用策略列表 |
| `/api/v1/strategies/{name}/signal` | POST | 获取策略信号 |
| `/api/v1/strategies/consensus` | POST | 多策略共识分析 |

### 回测模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/backtesting/run` | POST | 运行回测 |
| `/api/v1/backtesting/quick-run` | POST | 快速回测 |
| `/api/v1/backtesting/run/multiple` | POST | 多策略回测 |
| `/api/v1/backtesting/strategies` | GET | 获取可用策略列表 |

### 监控模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/monitoring/alerts/price` | POST | 创建价格告警 |
| `/api/v1/monitoring/alerts/rules` | GET | 获取告警规则列表 |
| `/api/v1/monitoring/alerts/notifications` | GET | 获取告警通知列表 |
| `/api/v1/monitoring/price/current` | GET | 获取当前价格 |
| `/api/v1/monitoring/ws` | WS | WebSocket 实时推送 |

### AI 模块

| 端点 | 方法 | 描述 |
| --- | --- | --- |
| `/api/v1/ai/chat` | POST | AI 聊天 |
| `/api/v1/ai/status` | GET | AI 服务状态 |
| `/api/v1/ai/context` | GET | 获取 AI 上下文 |

## 使用示例

### 1. 创建投资组合

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "我的投资组合", "description": "主要交易组合"}' \
  http://localhost:8000/api/v1/trading/portfolios
```

### 2. 记录交易

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "market": "crypto",
    "symbol": "BTC/USDT",
    "action": "open",
    "type": "buy",
    "quantity": 0.1,
    "price": 60000,
    "amount": 6000
  }' \
  http://localhost:8000/api/v1/trading/transactions
```

### 3. 获取市场数据

```bash
curl -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/market/ohlcv?market=crypto&symbol=BTC/USDT&interval=1d&limit=30"
```

### 4. 计算 RSI 指标

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"market": "crypto", "symbol": "BTC/USDT", "interval": "1d", "period": 14}' \
  http://localhost:8000/api/v1/indicators/rsi
```

### 5. 获取策略信号

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"market": "crypto", "symbol": "BTC/USDT", "interval": "1d"}' \
  http://localhost:8000/api/v1/strategies/rsi/signal
```

### 6. 运行回测

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/backtesting/quick-run?strategy=rsi&market=crypto&symbol=BTC/USDT&interval=1d&initial_capital=10000"
```

### 7. AI 聊天

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "分析我的投资组合", "include_context": true}' \
  http://localhost:8000/api/v1/ai/chat
```

### 8. 创建价格告警

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BTC 价格告警",
    "market": "crypto",
    "symbol": "BTC/USDT",
    "type": "price_below",
    "threshold": 50000,
    "severity": "critical"
  }' \
  http://localhost:8000/api/v1/monitoring/alerts/price
```

## 配置

### LLM 配置

编辑 `config/llm.config.json` 来配置 AI 提供商：

```json
{
  "providers": {
    "mock": {
      "name": "mock",
      "base_url": "http://localhost:11434/v1",
      "api_key": "mock",
      "models": [{"id": "mock", "name": "Mock Provider"}],
      "default_model": "mock"
    },
    "ollama": {
      "name": "ollama",
      "base_url": "http://localhost:11434/v1",
      "api_key": "ollama",
      "models": [{"id": "llama3", "name": "Llama 3"}],
      "default_model": "llama3"
    },
    "openai": {
      "name": "openai",
      "base_url": "https://api.openai.com/v1",
      "api_key": "your-api-key",
      "models": [{"id": "gpt-4o", "name": "GPT-4o"}],
      "default_model": "gpt-4o"
    }
  },
  "active_provider": "mock"
}
```

## 项目结构

```
Ledgerline/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── db/
│   │   │   ├── modules/
│   │   │   │   ├── ai/
│   │   │   │   ├── backtesting/
│   │   │   │   ├── indicators/
│   │   │   │   ├── market/
│   │   │   │   ├── monitoring/
│   │   │   │   ├── strategies/
│   │   │   │   └── trading/
│   │   │   └── main.py
│   │   └── requirements.txt
│   └── web/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   └── lib/
│       └── package.json
├── config/
│   └── llm.config.demo.json
├── docs/
│   ├── PROJECT_PROGRESS.md
│   └── ARCHITECTURE.md
└── README.md
```

## 技术栈

### 后端

- FastAPI 0.115+
- SQLAlchemy 2.0+
- Pydantic 2.0+
- APScheduler
- CCXT
- NumPy

### 前端

- Next.js 16+
- React 19+
- TypeScript
- Tailwind CSS 3.4+
- Lucide React
- Axios

## 许可证

MIT License
