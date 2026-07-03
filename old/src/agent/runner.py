"""Standalone agent CLI runner."""

import argparse
import json

from .service import agent_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the self-contained QuantAITrade agent")
    parser.add_argument("--init-db", action="store_true", help="initialize agent-local database")
    parser.add_argument("--symbol", default="BTC/USDT", help="symbol to analyze")
    parser.add_argument("--run-env", default="paper", choices=["paper", "live", "backtest"])
    parser.add_argument("--portfolio-id", default="default_portfolio")
    parser.add_argument("--account-id", default="default_account")
    parser.add_argument("--position-group-id", default="default_group")
    parser.add_argument("--strategy-id", default="agent_discretionary_v1")
    parser.add_argument("--json", action="store_true", help="print raw JSON")
    args = parser.parse_args()

    if args.init_db:
        print(json.dumps(agent_service.init_database(), ensure_ascii=False, indent=2))
        return

    decision = agent_service.create_decision(
        {
            "run_env": args.run_env,
            "portfolio_id": args.portfolio_id,
            "account_id": args.account_id,
            "position_group_id": args.position_group_id,
            "strategy_id": args.strategy_id,
            "asset": {"symbol": args.symbol},
        }
    )

    if args.json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
        return

    print(f"decision_id: {decision['decision_id']}")
    print(f"symbol: {decision['symbol']}")
    print(f"action: {decision['action']} confidence={decision['confidence']}")
    print(f"reasoning: {decision['reasoning']}")
    print(f"risk_notes: {decision['risk_notes']}")


if __name__ == "__main__":
    main()

