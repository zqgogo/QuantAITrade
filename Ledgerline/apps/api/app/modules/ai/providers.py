import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from openai import AsyncOpenAI

from app.core.ai_config import EmbeddingConfig, LlmProviderConfig


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class LlmProvider(ABC):
    @abstractmethod
    async def complete(self, messages: list[ChatMessage]) -> str:
        raise NotImplementedError


class OpenAICompatibleLlmProvider(LlmProvider):
    def __init__(self, config: LlmProviderConfig) -> None:
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)

    async def complete(self, messages: list[ChatMessage]) -> str:
        response = await self.client.chat.completions.create(
            model=self.config.default_model,
            messages=[{"role": message.role, "content": message.content} for message in messages],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return response.choices[0].message.content or ""


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class LocalEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self._model = None

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from FlagEmbedding import BGEM3FlagModel

            use_fp16 = self.config.device != "cpu"
            self._model = BGEM3FlagModel(self.config.model, use_fp16=use_fp16)

        output = self._model.encode(texts, return_dense=True)
        return output["dense_vecs"].tolist()


class OpenAICompatibleEmbeddingProvider(EmbeddingProvider):
    def __init__(self, config: EmbeddingConfig) -> None:
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key or "", base_url=config.base_url)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(model=self.config.model, input=texts)
        return [item.embedding for item in response.data]


class MockLlmProvider(LlmProvider):
    def __init__(self, config: LlmProviderConfig) -> None:
        self.config = config
        self._seed = datetime.now().microsecond
    
    def _extract_context(self, messages: list[ChatMessage]) -> dict:
        context = {
            "positions_count": 0,
            "total_value": 0.0,
            "positions": [],
            "raw": "",
        }
        for msg in messages:
            if msg.role == "system":
                text = msg.content
                context["raw"] = text
                
                count_match = re.search(r"Open Positions:\s*(\d+)", text)
                if count_match:
                    context["positions_count"] = int(count_match.group(1))
                
                value_match = re.search(r"Total Portfolio Value:\s*\$([\d,]+\.?\d*)", text)
                if value_match:
                    context["total_value"] = float(value_match.group(1).replace(",", ""))
                
                pos_pattern = r"-\s*(\S+):\s*(\w+)\s+([\d.]+)\s*@\s*\$([\d.]+)\s*\(PnL:\s*(\S+)\s*\$([\d.]+)"
                for m in re.finditer(pos_pattern, text):
                    context["positions"].append({
                        "symbol": m.group(1),
                        "side": m.group(2),
                        "quantity": float(m.group(3)),
                        "avg_price": float(m.group(4)),
                        "pnl_sign": m.group(5),
                        "pnl": float(m.group(6)),
                    })
                break
        return context
    
    async def complete(self, messages: list[ChatMessage]) -> str:
        user_message = None
        for msg in messages:
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            return "I'm ready to help with your trading analysis. What would you like to know?"
        
        context = self._extract_context(messages)
        user_lower = user_message.lower()
        
        rng = random.Random(self._seed + len(user_message))
        
        if any(kw in user_lower for kw in ["portfolio", "持仓", "仓位", "组合", "我的"]):
            return self._portfolio_response(context, rng)
        
        if any(kw in user_lower for kw in ["signal", "信号", "策略", "strategy", "rsi", "macd", "指标", "indicator"]):
            return self._signal_response(context, rng, user_lower)
        
        if any(kw in user_lower for kw in ["market", "市场", "行情", "price", "价格", "行情"]):
            return self._market_response(context, rng)
        
        if any(kw in user_lower for kw in ["help", "帮助", "功能", "capability", "你好", "hi", "hello"]):
            return self._help_response(context)
        
        if any(kw in user_lower for kw in ["buy", "sell", "交易", "下单", "trade", "recommend"]):
            return self._trade_recommend_response(context, rng)
        
        return self._generic_response(context, rng, user_message)
    
    def _portfolio_response(self, ctx: dict, rng: random.Random) -> str:
        pos_count = ctx["positions_count"]
        total_value = ctx["total_value"]
        positions = ctx["positions"]
        
        lines = [f"📊 **Portfolio Analysis**\n"]
        lines.append(f"**Overview:**")
        lines.append(f"- Total Value: ${total_value:,.2f}")
        lines.append(f"- Open Positions: {pos_count}")
        lines.append(f"- Risk Level: {'Low' if pos_count <= 1 else 'Moderate' if pos_count <= 3 else 'High'}")
        lines.append("")
        
        if positions:
            lines.append("**Position Details:**")
            for p in positions:
                pnl_str = f"${p['pnl']:,.2f}"
                emoji = "🟢" if p["pnl"] >= 0 else "🔴"
                lines.append(f"- {p['symbol']}: {p['side'].upper()} {p['quantity']} @ ${p['avg_price']:,.2f} (PnL: {emoji} {pnl_str})")
            lines.append("")
        
        recs = [
            "Consider diversifying across different asset classes to reduce concentration risk.",
            "Ensure no single position exceeds 2-3% of your total capital.",
            "Set appropriate stop loss levels for all open positions.",
            "Review your risk-reward ratio before entering new trades.",
            "Consider taking partial profits on positions with large unrealized gains.",
        ]
        lines.append("**Recommendations:**")
        for r in rng.sample(recs, min(3, len(recs))):
            lines.append(f"- {r}")
        
        return "\n".join(lines)
    
    def _signal_response(self, ctx: dict, rng: random.Random, user_lower: str) -> str:
        symbol = "BTC/USDT"
        for p in ctx["positions"]:
            symbol = p["symbol"]
            break
        
        indicators = []
        if "rsi" in user_lower:
            indicators.append(("RSI", rng.choice(["Oversold (below 30)", "Overbought (above 70)", "Neutral"]), "🟢" if rng.random() > 0.5 else "🔴"))
        if "macd" in user_lower:
            indicators.append(("MACD", rng.choice(["Bullish crossover forming", "Bearish crossover", "Awaiting confirmation"]), "🟡"))
        if "bollinger" in user_lower or "band" in user_lower:
            indicators.append(("Bollinger Bands", rng.choice(["Price near lower band", "Price near upper band", "Price within bands"]), "🟡"))
        if not indicators:
            indicators = [
                ("RSI", rng.choice(["Oversold (below 30)", "Overbought (above 70)", "Neutral"]), "🟢"),
                ("MACD", rng.choice(["Bullish crossover", "Bearish crossover", "Neutral"]), "🟡"),
                ("Bollinger Bands", rng.choice(["Price near lower band", "Price near upper band", "Within bands"]), "🟡"),
            ]
        
        lines = [f"📈 **Signal Analysis for {symbol}**\n"]
        lines.append("**Trading Signals:**")
        for name, desc, emoji in indicators:
            lines.append(f"- {name}: {desc} {emoji}")
        lines.append("")
        lines.append(f"**Risk Assessment:**")
        lines.append(f"- Volatility: {rng.choice(['Low', 'Moderate', 'High'])}")
        lines.append(f"- Confidence: {rng.randint(55, 85)}%")
        lines.append(f"- Recommended Position Size: {rng.choice(['1-2%', '2-3%', '3-5%'])} of capital")
        
        return "\n".join(lines)
    
    def _market_response(self, ctx: dict, rng: random.Random) -> str:
        lines = ["🌍 **Market Overview**\n"]
        
        symbols = [p["symbol"] for p in ctx["positions"]] or ["BTC/USDT"]
        
        for sym in symbols[:3]:
            price = rng.uniform(50000, 120000)
            change = rng.uniform(-5, 5)
            emoji = "🟢" if change >= 0 else "🔴"
            lines.append(f"**{sym}:**")
            lines.append(f"- Price: ~${price:,.2f}")
            lines.append(f"- 24h Change: {change:+.2f}% {emoji}")
            lines.append(f"- Volume: {rng.choice(['Low', 'Moderate', 'High'])}")
            lines.append("")
        
        lines.append("**Key Levels:**")
        for sym in symbols[:2]:
            lines.append(f"- {sym}: Support ~${rng.uniform(50000, 100000):,.0f} / Resistance ~${rng.uniform(60000, 120000):,.0f}")
        
        return "\n".join(lines)
    
    def _help_response(self, ctx: dict) -> str:
        return """👋 **Ledgerline AI Trading Assistant**

**Capabilities:**
- 📊 Portfolio Analysis & Optimization
- 📈 Signal Generation & Strategy Analysis
- 🌍 Market Insights & Price Monitoring
- 🎯 Trade Recommendations & Risk Assessment

**How to use:**
- "分析我的持仓" - Portfolio analysis with real data
- "给我 RSI 信号" - Strategy signal generation
- "市场行情怎么样" - Market overview
- "帮我做交易决策" - Trade recommendations

Note: I'm running in **Mock mode** with simulated data. Connect a real LLM (Ollama/OpenAI) for actual AI analysis."""
    
    def _trade_recommend_response(self, ctx: dict, rng: random.Random) -> str:
        lines = ["🎯 **Trade Recommendation**\n"]
        
        symbols = [p["symbol"] for p in ctx["positions"]] or ["BTC/USDT"]
        sym = rng.choice(symbols)
        
        action = rng.choice(["LONG", "SHORT", "HOLD"])
        emoji = "🟢" if action == "LONG" else "🔴" if action == "SHORT" else "🟡"
        
        lines.append(f"**Recommendation:** {emoji} {action} on {sym}")
        lines.append(f"**Confidence:** {rng.randint(60, 85)}%")
        lines.append(f"**Suggested Position Size:** {rng.choice(['1-2%', '2-3%'])} of capital")
        lines.append("")
        lines.append("**Key Levels:**")
        lines.append(f"- Entry: ~${rng.uniform(55000, 100000):,.2f}")
        lines.append(f"- Stop Loss: ~${rng.uniform(50000, 95000):,.2f}")
        lines.append(f"- Take Profit: ~${rng.uniform(60000, 110000):,.2f}")
        lines.append("")
        lines.append("⚠️ Remember: This is a simulated recommendation. Always do your own research before trading.")
        
        return "\n".join(lines)
    
    def _generic_response(self, ctx: dict, rng: random.Random, user_msg: str) -> str:
        templates = [
            f"""📊 **Analysis: "{user_msg[:50]}"**

Based on your current portfolio ({ctx['positions_count']} positions, ${ctx['total_value']:,.2f} total value), here's my perspective:

The market is showing mixed signals across different timeframes. Key factors to watch:

1. **Short-term momentum** suggests {rng.choice(['bullish', 'bearish', 'neutral'])} bias
2. **Volume analysis** indicates {rng.choice(['accumulation', 'distribution', 'consolidation'])}
3. **Technical patterns** are forming {rng.choice(['continuation', 'reversal', 'breakout'])} setup

Would you like me to dive deeper into a specific aspect? For example:
- "分析我的持仓" for portfolio-specific advice
- "跑一下 RSI 策略" for signal generation""",
            f"""💡 **Quick Analysis**

Your question touches on an important trading topic. Here are some thoughts:

- Current portfolio has **{ctx['positions_count']} open positions** worth **${ctx['total_value']:,.2f}**
- Market sentiment appears {rng.choice(['bullish', 'bearish', 'neutral'])}
- Consider reviewing position sizes and risk exposure

For more specific analysis, try asking:
- "看看我的组合"
- "给我一些交易建议"
- "市场行情如何" """,
        ]
        return rng.choice(templates)


def build_llm_provider(config: LlmProviderConfig) -> LlmProvider:
    if config.name == "mock":
        return MockLlmProvider(config)
    return OpenAICompatibleLlmProvider(config)


def build_embedding_provider(config: EmbeddingConfig) -> EmbeddingProvider:
    if config.provider == "local":
        return LocalEmbeddingProvider(config)
    if config.provider in {"openai", "ollama", "custom"}:
        return OpenAICompatibleEmbeddingProvider(config)
    raise ValueError(f"Unsupported embedding provider: {config.provider}")
