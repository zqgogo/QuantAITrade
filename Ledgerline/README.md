# Ledgerline

Personal AI Trading Workspace based on the GuanLan design document.

Ledgerline is not an auto-trading bot and does not place orders. It is a single-user workspace for recording trades, accumulating market data, reviewing positions, and using AI as analysis support.

## Architecture

- `apps/web`: Next.js + React + TypeScript frontend.
- `apps/api`: FastAPI backend with modular core services.
- `docs`: product, architecture, and progress documents.
- `config`: LLM configuration files.

## Features

- **Trading Module**: Workspace management, portfolio tracking with multi-currency support, transaction recording (open/add/reduce/close), position aggregation
- **Market Data**: OHLCV data storage, real-time price fetching, exchange connector abstraction
- **Technical Indicators**: SMA, EMA, MACD, RSI, Bollinger Bands, Momentum, ROC, Volume MA
- **Strategy System**: Plugin-based strategy architecture with RSI, MACD, MA Cross, Bollinger strategies
- **AI Chat**: AI-powered trading assistant with context-aware analysis
- **Backtesting**: Strategy backtesting with comprehensive performance metrics
- **Monitoring & Alerting**: Real-time price monitoring, alert rules, WebSocket notifications

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20.9+

### Setup

**1. Copy AI Configuration**

```bash
cp config/llm.config.demo.json config/llm.config.json
```

`llm.config.json` is ignored by Git. Keep real API keys, local model names, and agent runtime choices there.

**2. Install Backend Dependencies**

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**3. Install Frontend Dependencies**

```bash
cd apps/web
npm install
```

### Running the Application

**Start Backend**

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend**

```bash
cd apps/web
npm run dev
```

### Default URLs

- Web: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- API Health: http://localhost:8000/health

## API Authentication

All API endpoints require an API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: dev-secret-key" http://localhost:8000/api/v1/trading/portfolios
```

For production, set the `LEDGERLINE_API_KEY` environment variable.

## API Endpoints

### Trading Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/trading/workspaces` | POST/GET | Create/List workspaces |
| `/api/v1/trading/workspaces/{id}` | GET | Get workspace detail |
| `/api/v1/trading/portfolios` | POST/GET | Create/List portfolios |
| `/api/v1/trading/portfolios/{id}` | GET | Get portfolio detail |
| `/api/v1/trading/portfolios/{id}/summary` | GET | Get portfolio summary (positions + P&L) |
| `/api/v1/trading/transactions` | POST/GET | Record/List transactions |
| `/api/v1/trading/positions/{id}` | GET | Get position detail |
| `/api/v1/trading/watchlist` | POST | Add to watchlist |
| `/api/v1/trading/watchlist/{id}` | PUT/DELETE | Update/Delete watchlist item |
| `/api/v1/trading/portfolios/{id}/watchlist` | GET | List watchlist items |
| `/api/v1/trading/portfolios/{id}/notifications` | GET | List notifications |
| `/api/v1/trading/notifications/{id}/read` | PUT | Mark notification read |
| `/api/v1/trading/portfolios/{id}/notifications/read-all` | PUT | Mark all notifications read |
| `/api/v1/trading/reports/stats` | GET | Report stats (period=week/month/all) |

### Market Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/market/ohlcv` | GET | Get OHLCV data |
| `/api/v1/market/ohlcv/refresh` | POST | Refresh OHLCV data |
| `/api/v1/market/price` | GET | Get current price (`?market=...&symbol=...`) |
| `/api/v1/market/progress` | GET | Data download progress |
| `/api/v1/market/status` | GET | Market module status |

### Indicators Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/indicators/available` | GET | List available indicators |
| `/api/v1/indicators/sma` | GET | Calculate SMA |
| `/api/v1/indicators/ema` | GET | Calculate EMA |
| `/api/v1/indicators/macd` | GET | Calculate MACD |
| `/api/v1/indicators/rsi` | GET | Calculate RSI |
| `/api/v1/indicators/bollinger` | GET | Calculate Bollinger Bands |
| `/api/v1/indicators/momentum` | GET | Calculate Momentum |
| `/api/v1/indicators/roc` | GET | Calculate ROC |
| `/api/v1/indicators/volume-ma` | GET | Calculate Volume MA |
| `/api/v1/indicators/calculate` | GET | Generic indicator calculation |

### Strategies Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/strategies/available` | GET | List available strategies |
| `/api/v1/strategies/run` | POST | Run strategy (query params) |
| `/api/v1/strategies/run/{name}` | GET | Run strategy by name |
| `/api/v1/strategies/run/multiple` | POST | Multi-strategy run |

### Backtesting Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/backtesting/run` | POST | Run backtest |
| `/api/v1/backtesting/quick-run` | POST | Quick backtest |
| `/api/v1/backtesting/run/multiple` | POST | Multi-strategy backtest |
| `/api/v1/backtesting/strategies` | GET | List available strategies |
| `/api/v1/backtesting/results` | GET | Recent backtest results |

### Monitoring Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/monitoring/alerts/price` | POST | Create price alert |
| `/api/v1/monitoring/alerts/signal` | POST | Create signal alert |
| `/api/v1/monitoring/alerts/rules` | GET | List alert rules |
| `/api/v1/monitoring/alerts/rules/{id}` | GET/DELETE | Get/Delete alert rule |
| `/api/v1/monitoring/alerts/rules/{id}/toggle` | PATCH | Enable/Disable alert rule |
| `/api/v1/monitoring/alerts/notifications` | GET | List alert notifications |
| `/api/v1/monitoring/alerts/notifications/{id}/read` | PATCH | Mark notification read |
| `/api/v1/monitoring/alerts/notifications/read-all` | PATCH | Mark all notifications read |
| `/api/v1/monitoring/monitor/start` | POST | Start price monitor |
| `/api/v1/monitoring/monitor/stop` | POST | Stop price monitor |
| `/api/v1/monitoring/monitor/symbols` | GET | List monitored symbols |
| `/api/v1/monitoring/price/current` | GET | Get current price |
| `/api/v1/monitoring/ws` | WS | WebSocket for real-time updates |

### AI Module

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/v1/ai/chat` | POST | AI chat (auto-creates session) |
| `/api/v1/ai/chat/portfolio` | POST | Portfolio analysis |
| `/api/v1/ai/chat/signal` | POST | Strategy signal analysis |
| `/api/v1/ai/status` | GET | AI service status |
| `/api/v1/ai/context` | GET | Get AI context |
| `/api/v1/ai/sessions` | GET/POST | List/Create chat sessions |
| `/api/v1/ai/sessions/{id}` | GET/DELETE | Get/Delete chat session |

## Usage Examples

### 1. Create a Workspace and Portfolio

```bash
# Create a workspace
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"name": "Trading"}' \
  http://localhost:8000/api/v1/trading/workspaces

# Create a portfolio inside the workspace
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": 1, "name": "My Portfolio", "currency": "USD"}' \
  http://localhost:8000/api/v1/trading/portfolios
```

### 2. Record a Transaction

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_id": 1,
    "market": "crypto",
    "symbol": "BTCUSDT",
    "side": "buy",
    "type": "open",
    "price": 60000,
    "quantity": 0.1,
    "fee": 0
  }' \
  http://localhost:8000/api/v1/trading/transactions
```

`type` is one of `open`/`add`/`reduce`/`close`; `side` is `buy`/`sell`.

### 3. Get Market Data

```bash
curl -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/market/ohlcv?market=crypto&symbol=BTCUSDT&interval=1d&limit=30"
```

### 4. Calculate RSI

```bash
curl -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/indicators/rsi?market=crypto&symbol=BTCUSDT&interval=1d&period=14"
```

### 5. Get Strategy Signal

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/strategies/run?market=crypto&symbol=BTCUSDT&interval=1d&strategy=rsi"
```

### 6. Run Backtest

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  "http://localhost:8000/api/v1/backtesting/quick-run?strategy=rsi&market=crypto&symbol=BTCUSDT&interval=1d&initial_capital=10000"
```

### 7. AI Chat

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze my portfolio", "include_context": true}' \
  http://localhost:8000/api/v1/ai/chat
```

### 8. Create Price Alert

```bash
curl -X POST -H "X-API-Key: dev-secret-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "BTC Price Alert",
    "market": "crypto",
    "symbol": "BTC/USDT",
    "type": "price_below",
    "threshold": 50000,
    "severity": "critical"
  }' \
  http://localhost:8000/api/v1/monitoring/alerts/price
```

## Configuration

### LLM Configuration

Edit `config/llm.config.json` to configure AI providers:

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

## Project Structure

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

## Technology Stack

### Backend

- FastAPI 0.115+
- SQLAlchemy 2.0+
- Pydantic 2.0+
- APScheduler
- CCXT
- NumPy

### Frontend

- Next.js 16+
- React 19+
- TypeScript
- Tailwind CSS 3.4+
- Lucide React
- Axios

## License

MIT License
