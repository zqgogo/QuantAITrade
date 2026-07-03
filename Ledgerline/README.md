# Ledgerline

Personal AI Trading Workspace based on the GuanLan design document.

Ledgerline is not an auto-trading bot and does not place orders. It is a single-user workspace for recording trades, accumulating market data, reviewing positions, and using AI as analysis support.

## Architecture

- `apps/web`: Next.js + React + PWA-ready frontend.
- `apps/api`: FastAPI backend with modular core services.
- `docs`: product, architecture, and progress documents.
- `scripts`: local development helpers.

## Local Development

AI config:

```bash
cp config/llm.config.demo.json config/llm.config.json
```

`llm.config.json` is ignored by Git. Keep real API keys, local model names, and agent runtime choices there.

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

For local bge-m3 embeddings:

```bash
pip install -e ".[local-ai]"
```

Frontend:

```bash
cd apps/web
npm install
npm run dev
```

Default URLs:

- Web: http://localhost:3000
- API: http://localhost:8000
- API health: http://localhost:8000/health
