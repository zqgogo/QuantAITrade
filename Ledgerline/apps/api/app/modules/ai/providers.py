from abc import ABC, abstractmethod
from dataclasses import dataclass

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
    
    async def complete(self, messages: list[ChatMessage]) -> str:
        user_message = None
        for msg in messages:
            if msg.role == "user":
                user_message = msg.content
                break
        
        if not user_message:
            return "I'm ready to help with your trading analysis. What would you like to know?"
        
        user_lower = user_message.lower()
        
        if any(keyword in user_lower for keyword in ["portfolio", "持仓", "仓位"]):
            return """📊 **Portfolio Analysis**

Based on your current portfolio:

**Overview:**
- Total Value: $32,390
- Open Positions: 1
- Risk Level: Moderate

**Recommendations:**
1. **Diversification**: Consider adding positions in different asset classes to reduce risk
2. **Position Sizing**: Ensure no single position exceeds 2-3% of your total capital
3. **Stop Loss**: Set appropriate stop loss levels for all open positions

Would you like me to analyze a specific position or recommend entry/exit points?
"""
        
        if any(keyword in user_lower for keyword in ["signal", "信号", "策略", "strategy", "rsi", "macd"]):
            return """📈 **Signal Analysis**

**Current Market Conditions:**
- BTC/USDT: Recent RSI indicates oversold conditions (below 30)
- MACD: Bullish crossover potential forming
- Bollinger Bands: Price near lower band

**Trading Signals:**
1. 🟢 **RSI Strategy**: BUY signal detected (RSI crossed below 30)
2. 🟡 **Bollinger Bands**: HOLD - price within bands
3. 🟡 **MACD**: Awaiting confirmation

**Risk Assessment:**
- Volatility: Moderate
- Confidence: 75%
- Recommended Position Size: 2% of capital

**Action Plan:**
- Consider initiating a long position on BTC
- Set stop loss at recent swing low
- Target 2-3% gain before taking profits

Would you like me to run additional strategies or provide more detailed analysis?
"""
        
        if any(keyword in user_lower for keyword in ["market", "市场", "行情", "price", "价格"]):
            return """🌍 **Market Overview**

**Bitcoin (BTC/USDT):**
- Current Price: ~$60,000
- 24h Change: +2.3% 🟢
- Volume: High

**Market Sentiment:**
- Fear & Greed Index: 65 (Greed)
- Institutional Activity: Increasing
- Regulatory Environment: Stable

**Key Levels:**
- Support: $58,000 - $59,000
- Resistance: $62,000 - $64,000

**Outlook:**
Short-term: Bullish momentum continues
Medium-term: Watch for consolidation
Long-term: Positive fundamentals

Would you like detailed analysis on a specific asset?
"""
        
        if any(keyword in user_lower for keyword in ["help", "帮助", "功能", "capability"]):
            return """👋 Welcome to Ledgerline AI Trading Assistant!

**My Capabilities:**
- 📊 Portfolio Analysis & Optimization
- 📈 Signal Generation & Strategy Execution
- 🌍 Market Insights & News Analysis
- 🎯 Trade Recommendations & Risk Assessment
- 💡 Technical Indicator Analysis

**Available Strategies:**
- RSI (Overbought/Oversold)
- MACD (Crossover)
- MA Cross (Golden/Death Cross)
- Bollinger Bands (Breakout)

**Available Indicators:**
- SMA, EMA, MACD, RSI, Bollinger Bands, Momentum, ROC

**How to use:**
- "Analyze my portfolio" - Get portfolio assessment
- "Run RSI strategy on BTC" - Generate trading signals
- "What's the market outlook?" - Get market analysis

How can I assist you today?
"""
        
        return """📊 **Trading Analysis**

Thank you for your question! I'm here to help with:

1. **Portfolio Analysis** - Review your open positions and P&L
2. **Signal Generation** - Run technical analysis strategies
3. **Market Insights** - Get current market conditions
4. **Trade Recommendations** - Based on your strategy preferences

**Example queries:**
- "Analyze my portfolio"
- "Generate RSI signal for BTC"
- "What's the current market sentiment?"

Could you provide more details about what you'd like to analyze?
"""


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
