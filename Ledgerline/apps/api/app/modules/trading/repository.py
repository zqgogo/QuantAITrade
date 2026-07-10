from datetime import datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.session import TradingSessionLocal
from app.modules.trading.models import (
    Notification,
    NotificationStatus,
    Position,
    PositionStatus,
    Portfolio,
    Report,
    Transaction,
    TransactionType,
    Watchlist,
    Workspace,
)


class TradingRepository:
    def __init__(self, db: Session | None = None):
        self.db = db or TradingSessionLocal()

    def get_workspace(self, workspace_id: int) -> Workspace | None:
        return self.db.get(Workspace, workspace_id)

    def get_workspace_by_name(self, name: str) -> Workspace | None:
        return self.db.scalar(select(Workspace).where(Workspace.name == name))

    def create_workspace(self, name: str) -> Workspace:
        workspace = Workspace(name=name)
        self.db.add(workspace)
        self.db.commit()
        self.db.refresh(workspace)
        return workspace

    def get_portfolio(self, portfolio_id: int) -> Portfolio | None:
        return self.db.get(Portfolio, portfolio_id)

    def get_portfolios_by_workspace(self, workspace_id: int) -> Sequence[Portfolio]:
        return self.db.scalars(select(Portfolio).where(Portfolio.workspace_id == workspace_id)).all()

    def create_portfolio(self, workspace_id: int, name: str, currency: str = "USD") -> Portfolio:
        portfolio = Portfolio(workspace_id=workspace_id, name=name, currency=currency)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get_position(self, position_id: int) -> Position | None:
        return self.db.get(Position, position_id)

    def get_open_positions(self, portfolio_id: int) -> Sequence[Position]:
        return self.db.scalars(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.status == PositionStatus.OPEN)
        ).all()

    def get_all_positions(self, portfolio_id: int) -> Sequence[Position]:
        return self.db.scalars(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(Position.opened_at.desc())
        ).all()

    def get_position_with_transactions(self, position_id: int) -> Position | None:
        return self.db.scalar(
            select(Position)
            .options(joinedload(Position.transactions))
            .where(Position.id == position_id)
        )

    def create_position(
        self,
        portfolio_id: int,
        market: str,
        symbol: str,
        side: str,
        opened_at: datetime,
    ) -> Position:
        position = Position(
            portfolio_id=portfolio_id,
            market=market,
            symbol=symbol,
            side=side,
            status=PositionStatus.OPEN,
            opened_at=opened_at,
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def close_position(self, position_id: int, closed_at: datetime) -> Position:
        position = self.get_position(position_id)
        if position:
            position.status = PositionStatus.CLOSED
            position.closed_at = closed_at
            self.db.commit()
            self.db.refresh(position)
        return position

    def create_transaction(
        self,
        position_id: int,
        type: TransactionType,
        price: Decimal,
        quantity: Decimal,
        executed_at: datetime,
        fee: Decimal = Decimal(0),
        note: str | None = None,
    ) -> Transaction:
        transaction = Transaction(
            position_id=position_id,
            type=type,
            price=price,
            quantity=quantity,
            fee=fee,
            executed_at=executed_at,
            note=note,
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def get_transactions_by_position(self, position_id: int) -> Sequence[Transaction]:
        return self.db.scalars(
            select(Transaction)
            .where(Transaction.position_id == position_id)
            .order_by(Transaction.executed_at)
        ).all()

    def get_transactions(self, portfolio_id: int | None = None) -> Sequence[Transaction]:
        query = select(Transaction).options(joinedload(Transaction.position)).order_by(Transaction.created_at.desc())
        if portfolio_id:
            query = query.join(Position).where(Position.portfolio_id == portfolio_id)
        return self.db.scalars(query).all()


    def get_watchlist_items(self, portfolio_id: int) -> Sequence[Watchlist]:
        return self.db.scalars(
            select(Watchlist)
            .where(Watchlist.portfolio_id == portfolio_id)
            .order_by(Watchlist.created_at.desc())
        ).all()

    def get_watchlist_item(self, watchlist_id: int) -> Watchlist | None:
        return self.db.get(Watchlist, watchlist_id)

    def create_watchlist_item(
        self,
        portfolio_id: int,
        market: str,
        symbol: str,
        alert_price_high: Decimal | None = None,
        alert_price_low: Decimal | None = None,
        enabled: bool = True,
    ) -> Watchlist:
        watchlist = Watchlist(
            portfolio_id=portfolio_id,
            market=market,
            symbol=symbol,
            alert_price_high=alert_price_high,
            alert_price_low=alert_price_low,
            enabled=enabled,
        )
        self.db.add(watchlist)
        self.db.commit()
        self.db.refresh(watchlist)
        return watchlist

    def update_watchlist_item(
        self,
        watchlist_id: int,
        alert_price_high: Decimal | None = None,
        alert_price_low: Decimal | None = None,
        enabled: bool | None = None,
    ) -> Watchlist:
        watchlist = self.get_watchlist_item(watchlist_id)
        if watchlist:
            if alert_price_high is not None:
                watchlist.alert_price_high = alert_price_high
            if alert_price_low is not None:
                watchlist.alert_price_low = alert_price_low
            if enabled is not None:
                watchlist.enabled = enabled
            self.db.commit()
            self.db.refresh(watchlist)
        return watchlist

    def delete_watchlist_item(self, watchlist_id: int) -> None:
        watchlist = self.get_watchlist_item(watchlist_id)
        if watchlist:
            self.db.delete(watchlist)
            self.db.commit()

    def create_report(
        self,
        portfolio_id: int,
        type: str,
        title: str,
        content: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Report:
        report = Report(
            portfolio_id=portfolio_id,
            type=type,
            title=title,
            content=content,
            period_start=period_start,
            period_end=period_end,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports_by_portfolio(self, portfolio_id: int) -> Sequence[Report]:
        return self.db.scalars(
            select(Report)
            .where(Report.portfolio_id == portfolio_id)
            .order_by(Report.generated_at.desc())
        ).all()

    def create_notification(
        self,
        portfolio_id: int,
        type: str,
        title: str,
        message: str,
        symbol: str | None = None,
    ) -> Notification:
        notification = Notification(
            portfolio_id=portfolio_id,
            type=type,
            title=title,
            message=message,
            symbol=symbol,
            status=NotificationStatus.UNREAD,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_notifications(self, portfolio_id: int, status: str | None = None) -> Sequence[Notification]:
        query = select(Notification).where(Notification.portfolio_id == portfolio_id)
        if status:
            query = query.where(Notification.status == status)
        return self.db.scalars(query.order_by(Notification.created_at.desc())).all()

    def mark_notification_as_read(self, notification_id: int) -> Notification:
        notification = self.db.get(Notification, notification_id)
        if notification:
            notification.status = NotificationStatus.READ
            self.db.commit()
            self.db.refresh(notification)
        return notification

    def mark_all_notifications_as_read(self, portfolio_id: int) -> None:
        self.db.execute(
            Notification.__table__.update()
            .where(Notification.portfolio_id == portfolio_id)
            .where(Notification.status == NotificationStatus.UNREAD)
            .values(status=NotificationStatus.READ)
        )
        self.db.commit()