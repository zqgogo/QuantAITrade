"""
AI建议解析器
解析和验证AI生成的策略建议
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from loguru import logger

from config import get_config


class AISuggestionParser:
    """AI建议解析器类"""
    
    def __init__(self):
        """初始化解析器"""
        self.config = get_config()
        logger.info("AI建议解析器初始化完成")
    
    def parse_analysis_result(self, ai_response: str) -> Optional[Dict[str, Any]]:
        """
        解析AI分析结果
        
        Args:
            ai_response: AI返回的文本
        
        Returns:
            dict: 解析后的结构化数据
        """
        try:
            # 提取JSON部分
            json_str = self._extract_json(ai_response)
            if not json_str:
                logger.error("未找到JSON格式的响应")
                return None
            
            # 解析JSON
            data = json.loads(json_str)
            
            # 验证格式
            if not self._validate_format(data):
                logger.error("AI响应格式验证失败")
                return None
            
            logger.success("AI分析结果解析成功")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"解析AI响应失败: {e}")
            return None
    
    def validate_suggestions(self, suggestions: List[Dict[str, Any]]) -> Tuple[List[Dict], List[str]]:
        """
        验证建议的可行性
        
        Args:
            suggestions: 建议列表
        
        Returns:
            tuple: (有效建议列表, 拒绝原因列表)
        """
        valid_suggestions = []
        rejected_reasons = []
        
        for suggestion in suggestions:
            is_valid, reason = self._validate_single_suggestion(suggestion)
            
            if is_valid:
                valid_suggestions.append(suggestion)
            else:
                rejected_reasons.append(reason)
                logger.warning(f"建议被拒绝: {reason}")
        
        logger.info(f"建议验证完成: {len(valid_suggestions)} 有效, {len(rejected_reasons)} 被拒绝")
        return valid_suggestions, rejected_reasons
    
    def _extract_json(self, text: str) -> Optional[str]:
        """从文本中提取JSON部分"""
        try:
            # 尝试直接解析
            json.loads(text)
            return text
        except:
            # 尝试从代码块中提取
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end != -1:
                    return text[start:end].strip()
            
            # 尝试查找JSON对象
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                return text[start:end+1]
        
        return None
    
    def _validate_format(self, data: Dict[str, Any]) -> bool:
        """验证数据格式"""
        required_fields = ['market_summary', 'risk_alerts', 'strategy_suggestions']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"缺少必需字段: {field}")
                return False
        
        # 验证risk_alerts是列表
        if not isinstance(data['risk_alerts'], list):
            logger.error("risk_alerts 必须是列表")
            return False
        
        # 验证strategy_suggestions是列表
        if not isinstance(data['strategy_suggestions'], list):
            logger.error("strategy_suggestions 必须是列表")
            return False
        
        return True
    
    def _validate_single_suggestion(self, suggestion: Dict[str, Any]) -> Tuple[bool, str]:
        """
        验证单个建议
        
        Returns:
            tuple: (是否有效, 拒绝原因或空字符串)
        """
        # 检查必需字段
        required_fields = ['suggestion_type', 'target', 'reason']
        for field in required_fields:
            if field not in suggestion:
                return False, f"建议缺少必需字段: {field}"
        
        suggestion_type = suggestion['suggestion_type']
        
        # 根据类型验证
        if suggestion_type == 'parameter_adjust':
            return self._validate_parameter_adjust(suggestion)
        elif suggestion_type == 'strategy_enable':
            return self._validate_strategy_toggle(suggestion, enable=True)
        elif suggestion_type == 'strategy_disable':
            return self._validate_strategy_toggle(suggestion, enable=False)
        elif suggestion_type == 'risk_adjust':
            return self._validate_risk_adjust(suggestion)
        else:
            return False, f"未知的建议类型: {suggestion_type}"
    
    def _validate_parameter_adjust(self, suggestion: Dict[str, Any]) -> Tuple[bool, str]:
        """验证参数调整建议"""
        if 'suggested_value' not in suggestion:
            return False, "参数调整建议缺少suggested_value"
        
        # 检查参数是否存在且合理
        target = suggestion['target']
        suggested_value = suggestion['suggested_value']
        
        # 简单的合理性检查（可以根据实际情况扩展）
        if isinstance(suggested_value, (int, float)):
            if suggested_value <= 0:
                return False, f"参数值必须大于0: {suggested_value}"
        
        return True, ""
    
    def _validate_strategy_toggle(self, suggestion: Dict[str, Any], enable: bool) -> Tuple[bool, str]:
        """验证策略启停建议"""
        target_strategy = suggestion['target']
        
        # 检查策略是否存在
        # TODO: 检查策略是否在可用策略列表中
        
        return True, ""
    
    def _validate_risk_adjust(self, suggestion: Dict[str, Any]) -> Tuple[bool, str]:
        """验证风控调整建议"""
        if 'suggested_value' not in suggestion:
            return False, "风控调整建议缺少suggested_value"
        
        # 风控参数通常是百分比，检查范围
        suggested_value = suggestion.get('suggested_value')
        
        if isinstance(suggested_value, (int, float)):
            if not (0 < suggested_value <= 1):
                return False, f"风控参数必须在0-1之间: {suggested_value}"
        
        return True, ""


# 全局实例
ai_suggestion_parser = AISuggestionParser()
