from typing import Any, Dict, List, Optional

from app.modules.trading.repository import TradingRepository
from app.modules.trading.service import TradingService


class ContextAssembler:
    def __init__(self):
        self.repository = TradingRepository()
        self.service = TradingService()
    
    def assemble_trading_context(self) -> Dict[str, Any]:
        try:
            workspace_id = self.service.ensure_default_workspace()
            portfolio_id = self.service.ensure_default_portfolio(workspace_id)
            summary = self.service.get_portfolio_summary(portfolio_id)
            
            positions_summary = []
            total_value = 0.0
            
            for pos in summary["positions"]:
                positions_summary.append({
                    "symbol": pos["symbol"],
                    "market": pos["market"],
                    "quantity": pos["total_quantity"],
                    "avg_price": pos["avg_price"],
                    "current_price": pos.get("current_price") or pos["avg_price"],
                    "side": pos["side"],
                    "pnl": pos.get("pnl", 0),
                    "pnl_percent": pos.get("pnl_pct", 0),
                })
                total_value += float(pos.get("current_price") or pos["avg_price"]) * float(pos["total_quantity"])
            
            return {
                "positions": positions_summary,
                "positions_count": len(positions_summary),
                "total_value": total_value,
                "recent_trades": [],
                "recent_trades_count": 0,
            }
        except Exception:
            return {
                "positions": [],
                "positions_count": 0,
                "total_value": 0.0,
                "recent_trades": [],
                "recent_trades_count": 0,
            }
    
    def assemble_market_context(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        if not symbols:
            return {"symbols": [], "prices": {}}
        
        prices = {}
        for symbol in symbols:
            try:
                from app.modules.market.service import market_service
                ticker = market_service.get_ticker(symbol, "crypto")
                if ticker:
                    prices[symbol] = {
                        "price": float(ticker.last_price),
                        "change_24h": float(ticker.change_24h),
                        "volume_24h": float(ticker.volume_24h),
                    }
            except Exception:
                continue
        
        return {"symbols": symbols, "prices": prices}
    
    def assemble_strategy_context(self) -> Dict[str, Any]:
        return {"strategies": [], "recent_signals": []}
    
    def get_full_context(self) -> str:
        trading_ctx = self.assemble_trading_context()
        market_ctx = self.assemble_market_context()
        
        context_str = "=== Trading Context ===\n"
        context_str += f"Open Positions: {trading_ctx['positions_count']}\n"
        context_str += f"Total Portfolio Value: ${trading_ctx['total_value']:,.2f}\n\n"
        
        if trading_ctx["positions"]:
            context_str += "Open Positions:\n"
            for pos in trading_ctx["positions"]:
                pnl_color = "🟢" if pos["pnl"] >= 0 else "🔴"
                context_str += f"  - {pos['symbol']}: {pos['side']} {pos['quantity']} @ ${pos['avg_price']:.2f} (PnL: {pnl_color} ${pos['pnl']:.2f} / {pos['pnl_percent']:.2f}%)\n"
            context_str += "\n"
        
        if trading_ctx["recent_trades"]:
            context_str += "Recent Trades:\n"
            for trade in trading_ctx["recent_trades"][:5]:
                context_str += f"  - {trade['timestamp'][:10]}: {trade['symbol']} {trade['side']} {trade['quantity']} @ ${trade['price']:.2f}\n"
            context_str += "\n"
        
        if market_ctx["prices"]:
            context_str += "Market Prices:\n"
            for symbol, data in market_ctx["prices"].items():
                change_color = "🟢" if data["change_24h"] >= 0 else "🔴"
                context_str += f"  - {symbol}: ${data['price']:.2f} {change_color} {data['change_24h']:.2f}%\n"
        
        return context_str


context_assembler = ContextAssembler()
