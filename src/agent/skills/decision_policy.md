# Agent Decision Policy

- Keep execution separate from decision making.
- Prefer `HOLD` or `OBSERVE` when market data is missing or confidence is low.
- In `live` mode, require human confirmation unless an external risk policy explicitly overrides it.
- Every decision must include reasoning, risk notes and a stored snapshot.
- Never call exchange order APIs directly from the agent package.
- Analyze both long and short scenarios. The final action may be `BUY`, `SELL`, `HOLD`, `REDUCE`, or `OBSERVE`, but the reasoning should still include both long and short plans when data is available.
- Use latest and historical market context together: trend, volatility, support/resistance, momentum, volume and prior agent records.
- A suggestion is invalid without an invalidation level or condition.
