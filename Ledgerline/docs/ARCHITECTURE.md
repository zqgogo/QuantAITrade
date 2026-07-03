# Ledgerline Architecture

## Product Boundary

Ledgerline is a personal trading workspace:

- It records user-entered trading facts.
- It stores market facts for reuse.
- It computes indicators and portfolio state on read.
- It uses AI for analysis, reports, and chat.
- It does not execute trades or automate orders in the MVP.

## Layers

```text
Frontend: Next.js / React / PWA
    |
API: FastAPI
    |
Core Modules
    |-- Trading
    |-- Market Data
    |-- Indicators
    |-- Strategies
    |-- AI Trigger
    |-- Reports
    |-- Watch
    |-- News
    |-- Notifications
    |
Persistence
    |-- trading.db
    |-- market.db
    |-- ChromaDB
```

## Backend Module Rules

- Trading owns user facts and portfolio aggregation.
- Market owns OHLCV/news ingestion and storage.
- Indicators never persist computed values.
- Strategies emit normalized signals only.
- AI consumes context from other modules but core modules do not depend on AI.
- Reports persist generated snapshots and can also be indexed in vector storage.

## AI Configuration

Ledgerline uses a private local config file for AI settings:

- Commit: `config/llm.config.demo.json`
- Local only: `config/llm.config.json`

The config keeps LLM providers, embedding provider, vector store, and agent runtime separate. The default path is local-first:

- LLM: Ollama-compatible OpenAI endpoint.
- Embedding: `BAAI/bge-m3`.
- Vector store: ChromaDB.
- Agent runtime: built-in `ledgerline`, with `pi_coding_agent` reserved as a switchable runtime.

## Frontend Pages

- Dashboard: overview and today context.
- Trade: fast transaction entry.
- Portfolio: positions and derived metrics.
- Watch: alerts and signal rules.
- AI Chat: on-demand analysis.
- Reports: daily, weekly, monthly reviews.
- Settings: data sources, AI provider, token settings.
