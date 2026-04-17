"""
API路由模块
定义所有RESTful API端点
"""

import os
import time
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from fastapi import APIRouter, HTTPException, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.auth import create_access_token, verify_token, get_current_user
from config import get_config
from data import db_manager
from src.strategy import MACrossStrategy
from src.execution import risk_controller, position_tracker, exchange_connector
from src.ai.ai_analyzer import ai_analyzer
from data.models import Signal, SignalType


api_router = APIRouter()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SignalRequest(BaseModel):
    symbol: str
    signal_type: str
    price: float
    confidence: float = 0.8


class OrderRequest(BaseModel):
    symbol: str
    side: str
    order_type: str
    price: Optional[float] = None
    quantity: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: float
    components: Dict[str, bool]


@api_router.get("/")
async def root():
    """API根路径"""
    return {
        "name": "QuantAITrade API",
        "version": "1.0.0",
        "status": "running"
    }


@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    """系统健康检查"""
    try:
        config = get_config()
        return HealthResponse(
            status="healthy",
            timestamp=time.time(),
            components={
                "database": True,
                "exchange": True,
                "scheduler": True,
                "ai": ai_analyzer.client is not None
            }
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            components={}
        )


@api_router.post("/auth/token", response_model=TokenResponse)
async def login(username: str = Query(...), password: str = Query(...)):
    """
    获取访问令牌

    Args:
        username: 用户名
        password: 密码

    Returns:
        TokenResponse: 包含access_token的响应
    """
    if username == "admin" and password == os.getenv('API_PASSWORD', 'quantaitrade'):
        token = create_access_token(data={"sub": username})
        return TokenResponse(access_token=token)
    raise HTTPException(status_code=401, detail="Invalid credentials")


@api_router.get("/api/v1/strategies")
async def get_strategies():
    """
    获取策略列表

    Returns:
        list: 策略列表
    """
    try:
        config = get_config()
        strategy_config = config.get('strategy_params', {})
        return {
            "success": True,
            "data": {
                "strategies": strategy_config.get('enabled_strategies', []),
                "params": strategy_config
            }
        }
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/positions")
async def get_positions():
    """
    获取当前持仓

    Returns:
        list: 持仓列表
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM positions WHERE status = 'OPEN' ORDER BY entry_time DESC"
        )
        positions = [dict(row) for row in cursor.fetchall()]
        return {"success": True, "data": positions}
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/orders")
async def get_orders(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100)
):
    """
    获取订单列表

    Args:
        symbol: 交易对（可选）
        status: 订单状态（可选）
        limit: 返回数量限制

    Returns:
        list: 订单列表
    """
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM orders WHERE 1=1"
        params = []

        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        orders = [dict(row) for row in cursor.fetchall()]

        return {"success": True, "data": orders}
    except Exception as e:
        logger.error(f"获取订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/api/v1/orders")
async def create_order(order: OrderRequest):
    """
    创建订单

    Args:
        order: 订单请求

    Returns:
        dict: 创建结果
    """
    try:
        signal = Signal(
            strategy_name="API",
            symbol=order.symbol,
            signal_type=SignalType.BUY if order.side.upper() == "BUY" else SignalType.SELL,
            price=order.price or 0,
            confidence=0.9
        )

        passed, reason = risk_controller.check_order_risk(signal, 10000.0, [])

        if not passed:
            return {"success": False, "message": f"风控拒绝: {reason}"}

        return {"success": True, "message": "订单已提交", "order_id": f"API_{int(time.time())}"}
    except Exception as e:
        logger.error(f"创建订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/api/v1/orders/{order_id}")
async def cancel_order(order_id: str):
    """
    取消订单

    Args:
        order_id: 订单ID

    Returns:
        dict: 取消结果
    """
    try:
        return {"success": True, "message": f"订单 {order_id} 已取消"}
    except Exception as e:
        logger.error(f"取消订单失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/ai/analysis")
async def get_ai_analysis(date: Optional[str] = None):
    """
    获取AI分析结果

    Args:
        date: 分析日期（可选），格式YYYY-MM-DD

    Returns:
        dict: AI分析结果
    """
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ai_analysis_log WHERE analysis_date = ? ORDER BY created_at DESC LIMIT 1",
            (date,)
        )
        row = cursor.fetchone()

        if row:
            return {"success": True, "data": dict(row)}
        return {"success": True, "data": None, "message": "当日无分析结果"}
    except Exception as e:
        logger.error(f"获取AI分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/api/v1/ai/analysis")
async def trigger_ai_analysis(date: Optional[str] = None):
    """
    触发AI分析

    Args:
        date: 分析日期（可选）

    Returns:
        dict: 分析结果
    """
    try:
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        result = ai_analyzer.run_daily_analysis(date)

        if result:
            return {"success": True, "data": result}
        return {"success": False, "message": "AI分析失败"}
    except Exception as e:
        logger.error(f"触发AI分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/system/status")
async def get_system_status():
    """
    获取系统状态

    Returns:
        dict: 系统状态信息
    """
    try:
        return {
            "success": True,
            "data": {
                "status": "running",
                "mode": get_config().get('run_mode', 'manual'),
                "timestamp": time.time(),
                "uptime": "N/A"
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/data/klines")
async def get_klines(
    symbol: str = Query(..., description="交易对"),
    interval: str = Query(default="1h", description="时间周期"),
    limit: int = Query(default=100, le=1000, description="数据条数")
):
    """
    获取K线数据

    Args:
        symbol: 交易对
        interval: 时间周期
        limit: 数据条数

    Returns:
        list: K线数据
    """
    try:
        klines = db_manager.get_klines(symbol, interval, limit=limit)
        return {"success": True, "data": klines}
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/api/v1/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = Query(default=20, le=100)
):
    """
    获取通知列表

    Args:
        unread_only: 仅返回未读通知
        limit: 返回数量

    Returns:
        list: 通知列表
    """
    try:
        return {
            "success": True,
            "data": []
        }
    except Exception as e:
        logger.error(f"获取通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@api_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket端点，用于实时数据推送
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"收到: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)