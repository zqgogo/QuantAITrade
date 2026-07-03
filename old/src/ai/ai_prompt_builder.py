"""
AI提示词构建器
为AI分析构建结构化的提示词
"""

from typing import Dict, Any
from loguru import logger


class AIPromptBuilder:
    """AI提示词构建器类"""
    
    def __init__(self):
        """初始化提示词构建器"""
        logger.info("AI提示词构建器初始化完成")
    
    def build_daily_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """
        构建每日分析的提示词
        
        Args:
            data: 准备好的分析数据
        
        Returns:
            str: 结构化的提示词
        """
        prompt = self._build_system_prompt()
        prompt += "\n\n" + self._build_data_section(data)
        prompt += "\n\n" + self._build_task_section()
        prompt += "\n\n" + self._build_output_format()
        
        return prompt
    
    def _build_system_prompt(self) -> str:
        """构建系统角色定义"""
        return """你是一位专业的加密货币量化交易分析师，具备以下能力：
1. 深入理解技术分析和市场趋势
2. 熟练掌握各种量化交易策略
3. 能够识别市场风险和机会
4. 提供基于数据的客观建议

请基于提供的数据进行专业分析。"""
    
    def _build_data_section(self, data: Dict[str, Any]) -> str:
        """构建数据展示部分"""
        sections = []
        
        # 1. 市场概况
        market_data = data.get('market_data', {})
        if market_data:
            market_section = "## 📊 市场数据概况\n\n"
            for symbol, info in market_data.items():
                market_section += f"**{symbol}**:\n"
                market_section += f"- 最新价格: ${info['latest_price']:.2f}\n"
                market_section += f"- 24小时涨跌: {info['price_change_24h']:.2f}%\n"
                market_section += f"- 7天涨跌: {info['price_change_7d']:.2f}%\n"
                market_section += f"- 波动率: {info['volatility']:.2f}%\n"
                market_section += f"- 成交量趋势: {info['volume_trend']}\n\n"
            sections.append(market_section)
        
        # 2. 技术指标
        indicators = data.get('technical_indicators', {})
        if indicators:
            tech_section = "## 📈 技术指标\n\n"
            for symbol, ind in indicators.items():
                tech_section += f"**{symbol}**:\n"
                tech_section += f"- MA5: ${ind.get('ma5', 0):.2f}\n"
                if ind.get('ma20'):
                    tech_section += f"- MA20: ${ind['ma20']:.2f}\n"
                if ind.get('rsi'):
                    tech_section += f"- RSI(14): {ind['rsi']:.2f}\n"
                tech_section += f"- 趋势: {ind.get('trend', 'unknown')}\n\n"
            sections.append(tech_section)
        
        # 3. 交易记录
        trading = data.get('trading_records', {})
        if trading.get('total_trades', 0) > 0:
            trade_section = "## 💼 交易统计\n\n"
            trade_section += f"- 总交易次数: {trading['total_trades']}\n"
            trade_section += f"- 成功执行: {trading['successful_trades']}\n"
            trade_section += f"- 成功率: {trading['success_rate']*100:.1f}%\n"
            
            if trading.get('trades_by_symbol'):
                trade_section += "\n**各币种交易次数**:\n"
                for symbol, count in trading['trades_by_symbol'].items():
                    trade_section += f"- {symbol}: {count}次\n"
            sections.append(trade_section)
        
        # 4. 持仓情况
        positions = data.get('position_data', {})
        if positions.get('total_positions', 0) > 0:
            pos_section = "## 💰 当前持仓\n\n"
            pos_section += f"- 持仓数量: {positions['total_positions']}\n"
            pos_section += f"- 总敞口: ${positions['total_exposure']:.2f}\n"
            pos_section += f"- 浮动盈亏: ${positions['total_unrealized_pnl']:.2f}\n\n"
            
            pos_section += "**持仓明细**:\n"
            for pos in positions.get('positions', [])[:5]:  # 最多显示5个
                pos_section += f"- {pos['symbol']}: {pos['quantity']} @ ${pos['entry_price']:.2f} "
                pos_section += f"(盈亏: {pos['unrealized_pnl_percent']:.2f}%)\n"
            sections.append(pos_section)
        
        # 5. 市场事件
        events = data.get('market_events', [])
        if events:
            event_section = "## ⚠️ 市场异常事件\n\n"
            for event in events[:5]:  # 最多显示5个
                event_section += f"- {event['description']}\n"
            sections.append(event_section)
        
        return "\n".join(sections)
    
    def _build_task_section(self) -> str:
        """构建分析任务说明"""
        return """## 📋 分析任务

请基于以上数据，完成以下分析：

1. **市场总结**: 简要概括当前市场状况和主要特征
2. **风险识别**: 识别当前存在的主要风险因素
3. **策略建议**: 提供具体的策略调整建议（如果需要）

注意事项：
- 保持客观，基于数据分析
- 建议要具体可执行
- 风险评估要全面"""
    
    def _build_output_format(self) -> str:
        """构建输出格式要求"""
        return """## 📝 输出格式要求

请以JSON格式输出分析结果，包含以下字段：

```json
{
  "market_summary": "市场总结文本",
  "risk_alerts": [
    {
      "risk_type": "风险类型",
      "severity": "high/medium/low",
      "description": "风险描述"
    }
  ],
  "strategy_suggestions": [
    {
      "suggestion_type": "parameter_adjust/strategy_enable/strategy_disable/risk_adjust",
      "target": "目标策略或参数名称",
      "current_value": "当前值",
      "suggested_value": "建议值",
      "reason": "调整理由",
      "expected_effect": "预期效果"
    }
  ],
  "confidence_level": "high/medium/low",
  "additional_notes": "其他补充说明"
}
```

请严格按照此JSON格式输出，不要添加其他格式或注释。"""


# 全局实例
ai_prompt_builder = AIPromptBuilder()
