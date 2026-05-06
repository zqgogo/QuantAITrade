# Agent Decision Policy

- Keep execution separate from decision making.
- Prefer `HOLD` or `OBSERVE` when market data is missing or confidence is low.
- In `live` mode, require human confirmation unless an external risk policy explicitly overrides it.
- Every decision must include reasoning, risk notes and a stored snapshot.
- Never call exchange order APIs directly from the agent package.

