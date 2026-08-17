from decimal import Decimal
import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from app.modules.trading.models import TransactionType
from app.modules.trading.repository import TradingRepository
from app.modules.trading.schemas import (
    FxRateCreate,
    FxRateResponse,
    NotificationResponse,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioSummaryResponse,
    PositionDetailResponse,
    TransactionCreate,
    TransactionResponse,
    WatchlistCreate,
    WatchlistResponse,
    WatchlistUpdate,
    WorkspaceCreate,
    WorkspaceResponse,
)
from app.modules.trading.service import TradingService

router = APIRouter()
service = TradingService()
repository = TradingRepository()


@router.post("/workspaces", response_model=WorkspaceResponse)
async def create_workspace(data: WorkspaceCreate):
    workspace = repository.create_workspace(data.name)
    return {
        "id": workspace.id,
        "name": workspace.name,
        "created_at": workspace.created_at.isoformat(),
    }


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces():
    workspaces = repository.get_workspaces()
    return [
        {
            "id": w.id,
            "name": w.name,
            "created_at": w.created_at.isoformat(),
        }
        for w in workspaces
    ]


@router.get("/workspaces/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: int):
    workspace = repository.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "id": workspace.id,
        "name": workspace.name,
        "created_at": workspace.created_at.isoformat(),
    }


@router.post("/portfolios", response_model=PortfolioResponse)
async def create_portfolio(data: PortfolioCreate):
    portfolio = repository.create_portfolio(data.workspace_id, data.name, data.currency)
    return {
        "id": portfolio.id,
        "workspace_id": portfolio.workspace_id,
        "name": portfolio.name,
        "currency": portfolio.currency,
        "created_at": portfolio.created_at.isoformat(),
    }


@router.get("/portfolios", response_model=list[PortfolioResponse])
async def list_portfolios(workspace_id: int | None = Query(None, description="Filter by workspace")):
    portfolios = repository.get_portfolios(workspace_id)
    return [
        {
            "id": p.id,
            "workspace_id": p.workspace_id,
            "name": p.name,
            "currency": p.currency,
            "created_at": p.created_at.isoformat(),
        }
        for p in portfolios
    ]


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(portfolio_id: int):
    portfolio = repository.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {
        "id": portfolio.id,
        "workspace_id": portfolio.workspace_id,
        "name": portfolio.name,
        "currency": portfolio.currency,
        "created_at": portfolio.created_at.isoformat(),
    }


@router.post("/transactions", response_model=TransactionResponse)
async def record_transaction(data: TransactionCreate):
    try:
        transaction_type = TransactionType(data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid transaction type")

    try:
        result = service.record_transaction(
            portfolio_id=data.portfolio_id,
            market=data.market,
            symbol=data.symbol,
            side=data.side,
            type=transaction_type,
            price=Decimal(str(data.price)),
            quantity=Decimal(str(data.quantity)),
            fee=Decimal(str(data.fee)),
            executed_at=data.executed_at,
            note=data.note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(portfolio_id: int | None = None):
    transactions = repository.get_transactions(portfolio_id)
    return [
        {
            "id": t.id,
            "portfolio_id": t.position.portfolio_id if t.position else None,
            "position_id": t.position_id,
            "market": t.position.market if t.position else "",
            "symbol": t.position.symbol if t.position else "",
            "side": t.position.side if t.position else "",
            "type": t.type,
            "quantity": float(t.quantity),
            "price": float(t.price),
            "amount": float(t.price * t.quantity),
            "fee": float(t.fee),
            "created_at": t.created_at.isoformat(),
        }
        for t in transactions
    ]


@router.get("/portfolios/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(portfolio_id: int, current_prices: str | None = Query(None, description="JSON dict of current prices")):
    portfolio = repository.get_portfolio(portfolio_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    prices_dict = None
    if current_prices:
        try:
            prices_dict = json.loads(current_prices)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="current_prices must be valid JSON")

    return service.get_portfolio_summary(portfolio_id, prices_dict)


@router.get("/positions/{position_id}", response_model=PositionDetailResponse)
async def get_position_detail(position_id: int, current_price: float | None = None):
    try:
        price = Decimal(str(current_price)) if current_price else None
        return service.get_position_detail(position_id, price)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/portfolios/{portfolio_id}/watchlist", response_model=list[WatchlistResponse])
async def get_watchlist(portfolio_id: int):
    items = repository.get_watchlist_items(portfolio_id)
    return [
        {
            "id": item.id,
            "portfolio_id": item.portfolio_id,
            "market": item.market,
            "symbol": item.symbol,
            "alert_price_high": float(item.alert_price_high) if item.alert_price_high else None,
            "alert_price_low": float(item.alert_price_low) if item.alert_price_low else None,
            "enabled": item.enabled,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.post("/watchlist", response_model=WatchlistResponse)
async def create_watchlist_item(data: WatchlistCreate):
    item = repository.create_watchlist_item(
        portfolio_id=data.portfolio_id,
        market=data.market,
        symbol=data.symbol,
        alert_price_high=Decimal(str(data.alert_price_high)) if data.alert_price_high else None,
        alert_price_low=Decimal(str(data.alert_price_low)) if data.alert_price_low else None,
        enabled=data.enabled,
    )
    return {
        "id": item.id,
        "portfolio_id": item.portfolio_id,
        "market": item.market,
        "symbol": item.symbol,
        "alert_price_high": float(item.alert_price_high) if item.alert_price_high else None,
        "alert_price_low": float(item.alert_price_low) if item.alert_price_low else None,
        "enabled": item.enabled,
        "created_at": item.created_at.isoformat(),
    }


@router.put("/watchlist/{watchlist_id}", response_model=WatchlistResponse)
async def update_watchlist_item(watchlist_id: int, data: WatchlistUpdate):
    item = repository.update_watchlist_item(
        watchlist_id=watchlist_id,
        alert_price_high=Decimal(str(data.alert_price_high)) if data.alert_price_high is not None else None,
        alert_price_low=Decimal(str(data.alert_price_low)) if data.alert_price_low is not None else None,
        enabled=data.enabled,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")
    return {
        "id": item.id,
        "portfolio_id": item.portfolio_id,
        "market": item.market,
        "symbol": item.symbol,
        "alert_price_high": float(item.alert_price_high) if item.alert_price_high else None,
        "alert_price_low": float(item.alert_price_low) if item.alert_price_low else None,
        "enabled": item.enabled,
        "created_at": item.created_at.isoformat(),
    }


@router.delete("/watchlist/{watchlist_id}")
async def delete_watchlist_item(watchlist_id: int):
    repository.delete_watchlist_item(watchlist_id)
    return {"status": "deleted"}


@router.get("/portfolios/{portfolio_id}/notifications", response_model=list[NotificationResponse])
async def get_notifications(portfolio_id: int, status: str | None = None):
    items = repository.get_notifications(portfolio_id, status)
    return [
        {
            "id": item.id,
            "portfolio_id": item.portfolio_id,
            "type": item.type,
            "status": item.status,
            "title": item.title,
            "message": item.message,
            "symbol": item.symbol,
            "created_at": item.created_at.isoformat(),
        }
        for item in items
    ]


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: int):
    notification = repository.mark_notification_as_read(notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "marked_as_read"}


@router.put("/portfolios/{portfolio_id}/notifications/read-all")
async def mark_all_notifications_as_read(portfolio_id: int):
    repository.mark_all_notifications_as_read(portfolio_id)
    return {"status": "all_marked_as_read"}


@router.get("/reports/stats")
async def get_report_stats(
    period: Literal["week", "month", "all"] = Query("week", description="week, month, or all"),
):
    return service.get_report_stats(period)


@router.get("/exchange-rates", response_model=list[FxRateResponse])
async def list_fx_rates():
    return service.get_fx_rates()


@router.post("/exchange-rates", response_model=FxRateResponse)
async def set_fx_rate(data: FxRateCreate):
    try:
        return service.set_fx_rate(data.from_currency, data.to_currency, Decimal(str(data.rate)))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/exchange-rates", response_model=dict)
async def delete_fx_rate(
    from_currency: str = Query(description="Source currency"),
    to_currency: str = Query(description="Target currency"),
):
    deleted = service.delete_fx_rate(from_currency, to_currency)
    return {"success": deleted, "message": "Rate deleted" if deleted else "Rate not found"}
