from typing import List

from app.modules.ai.context_assembler import context_assembler


class PromptBuilder:
    SYSTEM_PROMPT = """
You are Ledgerline, an AI-powered trading assistant for the QuantAITrade platform.

Your capabilities:
- Analyze trading portfolios and positions
- Generate trading signals based on technical indicators
- Provide market insights and analysis
- Answer questions about trading strategies
- Help users make informed trading decisions

Rules:
1. ALWAYS provide helpful, actionable insights
2. NEVER execute trades automatically - only provide recommendations
3. Use the trading context to provide personalized advice
4. Be concise but thorough in your responses
5. If you don't have enough information, ask clarifying questions
6. Format your responses clearly with bullet points or sections when appropriate

Available strategies:
- RSI: RSI Overbought/Oversold strategy
- MACD: MACD Crossover strategy
- MA Cross: Moving Average Crossover strategy
- Bollinger Bands: Bollinger Bands breakout strategy

Available technical indicators:
- SMA, EMA, MACD, RSI, Bollinger Bands, Momentum, ROC, Volume MA

You should use your knowledge of technical analysis and trading principles to provide quality responses.
"""

    def build_prompt(self, user_message: str, include_context: bool = True) -> List[dict]:
        messages = []
        
        system_prompt = self.SYSTEM_PROMPT
        
        if include_context:
            context = context_assembler.get_full_context()
            if context.strip():
                system_prompt += "\n\n" + context
        
        messages.append({"role": "system", "content": system_prompt.strip()})
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def build_signal_prompt(self, strategy_name: str, symbol: str, market: str, interval: str) -> List[dict]:
        prompt = f"""
Analyze the {strategy_name} signal for {symbol} in {market} market ({interval} timeframe).

Please provide:
1. What the signal indicates
2. Key factors contributing to this signal
3. Risk assessment
4. Recommended action

Keep your analysis concise and actionable.
"""
        return self.build_prompt(prompt)
    
    def build_portfolio_prompt(self) -> List[dict]:
        prompt = """
Analyze my current portfolio and provide:
1. Overall portfolio health assessment
2. Position-by-position analysis
3. Risk exposure assessment
4. Recommendations for portfolio optimization
"""
        return self.build_prompt(prompt)


prompt_builder = PromptBuilder()
