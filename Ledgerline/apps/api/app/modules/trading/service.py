from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import select

from app.db.session import TradingSessionLocal
from app.modules.trading.models import Position, Transaction, TransactionType
from app.modules.trading.repository import TradingRepository


class PositionAggregate:
    def __init__(self, position: Position, transactions: list[Transaction]):
        self.position = position
        self.transactions = sorted(transactions, key=lambda t: t.executed_at)
        self._calculate()

    def _calculate(self) -> None:
        if not self.transactions:
            self.total_quantity = Decimal(0)
            self.avg_price = Decimal(0)
            return

        buys = [t for t in self.transactions if t.type in (TransactionType.OPEN, TransactionType.ADD)]
        sells = [t for t in self.transactions if t.type in (TransactionType.REDUCE, TransactionType.CLOSE)]

        total_buy_quantity = sum(t.quantity for t in buys)
        total_buy_value = sum(t.price * t.quantity for t in buys)

        total_sell_quantity = sum(t.quantity for t in sells)

        self.total_quantity = total_buy_quantity - total_sell_quantity
        self.avg_price = total_buy_value / total_buy_quantity if total_buy_quantity > 0 else Decimal(0)
        self.total_fee = sum(t.fee for t in self.transactions)

    def to_dict(self, current_price: Decimal | None = None) -> dict[str, Any]:
        base = {
            "position_id": self.position.id,
            "portfolio_id": self.position.portfolio_id,
            "market": self.position.market,
            "symbol": self.position.symbol,
            "side": self.position.side,
            "status": self.position.status,
            "opened_at": self.position.opened_at.isoformat() if self.position.opened_at else None,
            "closed_at": self.position.closed_at.isoformat() if self.position.closed_at else None,
            "total_quantity": float(self.total_quantity),
            "avg_price": float(self.avg_price),
            "total_fee": float(self.total_fee),
        }

        if current_price is not None:
            if self.position.side == "buy":
                pnl = (current_price - self.avg_price) * self.total_quantity
                pnl_pct = ((current_price - self.avg_price) / self.avg_price * 100) if self.avg_price > 0 else Decimal(0)
            else:
                pnl = (self.avg_price - current_price) * self.total_quantity
                pnl_pct = ((self.avg_price - current_price) / self.avg_price * 100) if self.avg_price > 0 else Decimal(0)

            base.update({
                "current_price": float(current_price),
                "pnl": float(pnl),
                "pnl_percent": float(pnl_pct),
            })

        return base


QUOTE_CURRENCIES = ("USDT", "USDC", "USD", "CNYT", "CNY", "EUR", "JPY", "AUD", "HKD", "GBP")


def quote_currency_from_symbol(symbol: str) -> str:
    normalized = symbol.upper().replace("/", "")
    for quote in QUOTE_CURRENCIES:
        if normalized.endswith(quote):
            if quote in ("USDT", "USDC"):
                return "USD"
            return quote
    return "USD"


class TradingService:
    def __init__(self, repository: TradingRepository | None = None):
        self.repository = repository or TradingRepository()

    def convert_amount(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
    ) -> Decimal | None:
        if from_currency == to_currency or amount == 0:
            return amount
        rate = self.repository.get_fx_rate(from_currency, to_currency)
        if rate:
            return amount * rate.rate
        inverse = self.repository.get_fx_rate(to_currency, from_currency)
        if inverse and inverse.rate > 0:
            return amount / inverse.rate
        return None

    def ensure_default_workspace(self) -> int:
        workspace = self.repository.get_workspace_by_name("Trading")
        if not workspace:
            workspace = self.repository.create_workspace("Trading")
        return workspace.id

    def ensure_default_portfolio(self, workspace_id: int) -> int:
        portfolios = self.repository.get_portfolios_by_workspace(workspace_id)
        if not portfolios:
            portfolio = self.repository.create_portfolio(workspace_id, "Default")
            return portfolio.id
        return portfolios[0].id

    def record_transaction(
        self,
        portfolio_id: int,
        market: str,
        symbol: str,
        side: str,
        type: TransactionType,
        price: Decimal,
        quantity: Decimal,
        executed_at: datetime | None = None,
        fee: Decimal = Decimal(0),
        note: str | None = None,
    ) -> dict[str, Any]:
        if executed_at is None:
            executed_at = datetime.utcnow()
        if quantity <= 0:
            raise ValueError("Quantity must be greater than zero")
        if price <= 0:
            raise ValueError("Price must be greater than zero")

        open_positions = self.repository.get_open_positions(portfolio_id)
        position = None

        for pos in open_positions:
            if pos.market == market and pos.symbol == symbol and pos.side == side:
                position = pos
                break

        if not position and type != TransactionType.OPEN:
            raise ValueError("No open position found for this symbol and side")

        if type in (TransactionType.REDUCE, TransactionType.CLOSE) and position:
            txns = self.repository.get_transactions_by_position(position.id)
            agg = PositionAggregate(position, txns)
            if quantity > agg.total_quantity:
                raise ValueError(
                    f"Cannot {type.value} more than current position quantity: {agg.total_quantity}"
                )

        if not position:
            position = self.repository.create_position(
                portfolio_id=portfolio_id,
                market=market,
                symbol=symbol,
                side=side,
                opened_at=executed_at,
            )

        transaction = self.repository.create_transaction(
            position_id=position.id,
            type=type,
            price=price,
            quantity=quantity,
            fee=fee,
            executed_at=executed_at,
            note=note,
        )

        if type == TransactionType.CLOSE:
            position = self.repository.close_position(position.id, executed_at)

        return {
            "id": transaction.id,
            "portfolio_id": position.portfolio_id,
            "position_id": position.id,
            "market": position.market,
            "symbol": position.symbol,
            "side": position.side,
            "type": transaction.type,
            "quantity": float(transaction.quantity),
            "price": float(transaction.price),
            "amount": float(transaction.price * transaction.quantity),
            "fee": float(transaction.fee),
            "created_at": transaction.created_at.isoformat(),
        }

    def get_portfolio_summary(self, portfolio_id: int, current_prices: dict[str, float] | None = None) -> dict[str, Any]:
        portfolio = self.repository.get_portfolio(portfolio_id)
        base_currency = portfolio.currency if portfolio else "USD"
        open_positions = self.repository.get_open_positions(portfolio_id)
        aggregates = []
        total_value = Decimal(0)
        total_pnl = Decimal(0)

        for pos in open_positions:
            transactions = self.repository.get_transactions_by_position(pos.id)
            agg = PositionAggregate(pos, transactions)
            price_key = f"{pos.market}:{pos.symbol}"
            current_price = None
            if current_prices:
                if price_key in current_prices:
                    current_price = Decimal(str(current_prices[price_key]))
                elif pos.symbol in current_prices:
                    current_price = Decimal(str(current_prices[pos.symbol]))

            quote_currency = quote_currency_from_symbol(pos.symbol)
            total_amount = agg.total_quantity * agg.avg_price
            converted_amount = self.convert_amount(total_amount, quote_currency, base_currency)
            if converted_amount is None:
                converted_amount = total_amount

            agg_dict = agg.to_dict(current_price)
            agg_dict["total_amount"] = float(converted_amount)
            agg_dict["currency"] = base_currency
            aggregates.append(agg_dict)

            total_value += converted_amount
            if current_price is not None:
                if pos.side == "buy":
                    pnl = (current_price - agg.avg_price) * agg.total_quantity
                else:
                    pnl = (agg.avg_price - current_price) * agg.total_quantity
                converted_pnl = self.convert_amount(pnl, quote_currency, base_currency)
                total_pnl += converted_pnl if converted_pnl is not None else pnl

        total_cost = Decimal(0)
        for pos in open_positions:
            agg = PositionAggregate(pos, self.repository.get_transactions_by_position(pos.id))
            cost = agg.total_quantity * agg.avg_price
            converted_cost = self.convert_amount(cost, quote_currency_from_symbol(pos.symbol), base_currency)
            total_cost += converted_cost if converted_cost is not None else cost
        total_pnl_pct = float(total_pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            "portfolio_id": portfolio_id,
            "portfolio_name": portfolio.name if portfolio else "",
            "currency": base_currency,
            "total_value": float(total_value),
            "total_pnl": float(total_pnl),
            "total_pnl_percent": total_pnl_pct,
            "positions": aggregates,
        }

    def get_position_detail(self, position_id: int, current_price: Decimal | None = None) -> dict[str, Any]:
        position = self.repository.get_position_with_transactions(position_id)
        if not position:
            raise ValueError("Position not found")

        transactions = [
            {
                "id": t.id,
                "type": t.type,
                "price": float(t.price),
                "quantity": float(t.quantity),
                "executed_at": t.executed_at.isoformat(),
                "note": t.note,
            }
            for t in position.transactions
        ]

        agg = PositionAggregate(position, position.transactions)
        result = agg.to_dict(current_price)
        result["transactions"] = transactions

        return result

    def get_report_stats(self, period: str = "week") -> dict[str, Any]:
        db = TradingSessionLocal()
        try:
            now = datetime.utcnow()
            if period == "week":
                start = now - timedelta(days=now.weekday())
                start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == "month":
                start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            elif period == "all":
                start = datetime.min
            else:
                raise ValueError(f"Unsupported report period: {period}")

            stmt = (
                select(Transaction)
                .where(Transaction.executed_at >= start)
                .order_by(Transaction.executed_at)
            )
            transactions = db.execute(stmt).scalars().all()

            total_buy = Decimal(0)
            total_sell = Decimal(0)
            total_fee = Decimal(0)
            realized_pnl = Decimal(0)

            daily: dict[str, dict[str, Any]] = {}

            for t in transactions:
                day = t.executed_at.strftime("%Y-%m-%d")
                if day not in daily:
                    daily[day] = {"date": day, "trades": 0, "buy": 0.0, "sell": 0.0, "fee": 0.0}
                daily[day]["trades"] += 1
                daily[day]["fee"] += float(t.fee)
                total_fee += t.fee

                amount = t.price * t.quantity
                if t.type in (TransactionType.OPEN, TransactionType.ADD):
                    total_buy += amount
                    daily[day]["buy"] += float(amount)
                else:
                    total_sell += amount
                    daily[day]["sell"] += float(amount)

            closed_positions = db.execute(
                select(Position).where(Position.status == "closed")
            ).scalars().all()
            for pos in closed_positions:
                pos_tx = db.execute(
                    select(Transaction).where(Transaction.position_id == pos.id).order_by(Transaction.executed_at)
                ).scalars().all()
                buys = [t for t in pos_tx if t.type in (TransactionType.OPEN, TransactionType.ADD)]
                sells = [t for t in pos_tx if t.type in (TransactionType.REDUCE, TransactionType.CLOSE)]
                buy_cost = sum(t.price * t.quantity for t in buys)
                sell_revenue = sum(t.price * t.quantity for t in sells)
                position_fee = sum(t.fee for t in pos_tx)
                pnl = sell_revenue - buy_cost - position_fee
                if pnl != 0:
                    close_day = pos.closed_at.strftime("%Y-%m-%d") if pos.closed_at else None
                    if close_day and (period == "all" or close_day >= start.strftime("%Y-%m-%d")):
                        realized_pnl += pnl
                        if close_day in daily:
                            daily[close_day]["pnl"] = daily[close_day].get("pnl", 0.0) + float(pnl)

            daily_list = sorted(daily.values(), key=lambda d: d["date"])
            for d in daily_list:
                d.setdefault("pnl", 0.0)

            return {
                "period": period,
                "start_date": start.date().isoformat(),
                "end_date": now.date().isoformat(),
                "total_trades": len(transactions),
                "total_buy": float(total_buy),
                "total_sell": float(total_sell),
                "total_fee": float(total_fee),
                "realized_pnl": float(realized_pnl),
                "net_volume": float(total_sell - total_buy),
                "daily": daily_list,
            }
        finally:
            db.close()

    def get_fx_rates(self) -> list[dict[str, Any]]:
        return [
            {
                "from_currency": rate.from_currency,
                "to_currency": rate.to_currency,
                "rate": float(rate.rate),
                "updated_at": rate.updated_at.isoformat() if rate.updated_at else None,
            }
            for rate in self.repository.list_fx_rates()
        ]

    def set_fx_rate(self, from_currency: str, to_currency: str, rate: Decimal) -> dict[str, Any]:
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        if from_currency == to_currency:
            raise ValueError("from_currency and to_currency must differ")
        fx_rate = self.repository.upsert_fx_rate(from_currency, to_currency, rate)
        return {
            "from_currency": fx_rate.from_currency,
            "to_currency": fx_rate.to_currency,
            "rate": float(fx_rate.rate),
            "updated_at": fx_rate.updated_at.isoformat() if fx_rate.updated_at else None,
        }

    def delete_fx_rate(self, from_currency: str, to_currency: str) -> bool:
        return self.repository.delete_fx_rate(from_currency.upper(), to_currency.upper())
