import asyncio
from typing import List

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.websockets import WebSocket, WebSocketDisconnect

from app.modules.monitoring.schemas import (
    AlertRule,
    AlertRuleListResponse,
    AlertListResponse,
    PriceAlertRequest,
    PriceUpdate,
    SignalAlertRequest,
)
from app.modules.monitoring.service import monitoring_service
from app.modules.monitoring.alert_manager import alert_manager
from app.modules.monitoring.price_monitor import price_monitor

router = APIRouter()

active_connections: List[WebSocket] = []


async def notify_clients(message: dict):
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except Exception:
            active_connections.remove(connection)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    
    def alert_callback(alert):
        asyncio.create_task(notify_clients({
            "type": "alert",
            "data": alert.dict(),
        }))
    
    def price_callback(update):
        asyncio.create_task(notify_clients({
            "type": "price",
            "data": update.dict(),
        }))
    
    alert_manager.subscribe(alert_callback)
    price_monitor.subscribe(price_callback)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        alert_manager.unsubscribe(alert_callback)
        price_monitor.unsubscribe(price_callback)


@router.post("/alerts/price", response_model=AlertRule)
async def create_price_alert(request: PriceAlertRequest) -> AlertRule:
    return monitoring_service.create_price_alert(request)


@router.post("/alerts/signal", response_model=AlertRule)
async def create_signal_alert(request: SignalAlertRequest) -> AlertRule:
    return monitoring_service.create_signal_alert(request)


@router.get("/alerts/rules", response_model=AlertRuleListResponse)
async def get_alert_rules() -> AlertRuleListResponse:
    return monitoring_service.get_all_rules()


@router.get("/alerts/rules/{rule_id}", response_model=AlertRule)
async def get_alert_rule(rule_id: str) -> AlertRule | None:
    return monitoring_service.get_rule(rule_id)


@router.delete("/alerts/rules/{rule_id}", response_model=dict)
async def delete_alert_rule(rule_id: str) -> dict:
    success = monitoring_service.delete_rule(rule_id)
    return {"success": success, "message": "Rule deleted" if success else "Rule not found"}


@router.patch("/alerts/rules/{rule_id}/toggle", response_model=dict)
async def toggle_alert_rule(rule_id: str) -> dict:
    success = monitoring_service.toggle_rule(rule_id)
    return {"success": success, "message": "Rule toggled" if success else "Rule not found"}


@router.get("/alerts/notifications", response_model=AlertListResponse)
async def get_alert_notifications(limit: int = Query(20, description="Max alerts to return")) -> AlertListResponse:
    return monitoring_service.get_alerts(limit)


@router.patch("/alerts/notifications/{alert_id}/read", response_model=dict)
async def mark_alert_read(alert_id: str) -> dict:
    success = monitoring_service.mark_alert_read(alert_id)
    return {"success": success, "message": "Alert marked as read" if success else "Alert not found"}


@router.patch("/alerts/notifications/read-all", response_model=dict)
async def mark_all_alerts_read() -> dict:
    count = monitoring_service.mark_all_alerts_read()
    return {"success": True, "message": f"Marked {count} alerts as read"}


@router.post("/monitor/start", response_model=dict)
async def start_price_monitor(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
    interval: int = Query(5, description="Check interval in seconds"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
) -> dict:
    background_tasks.add_task(monitoring_service.start_price_monitor, market, symbol, interval)
    return {"success": True, "message": f"Started monitoring {market}:{symbol}"}


@router.post("/monitor/stop", response_model=dict)
async def stop_price_monitor(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
) -> dict:
    await monitoring_service.stop_price_monitor(market, symbol)
    return {"success": True, "message": f"Stopped monitoring {market}:{symbol}"}


@router.get("/monitor/symbols", response_model=dict)
async def get_monitored_symbols() -> dict:
    symbols = monitoring_service.get_monitored_symbols()
    return {"success": True, "symbols": symbols}


@router.get("/price/current")
async def get_current_price(
    market: str = Query(description="Market type"),
    symbol: str = Query(description="Trading symbol"),
) -> PriceUpdate | dict:
    result = await monitoring_service.get_current_price(market, symbol)
    if result is None:
        return {"success": False, "message": "No price data available"}
    return result
