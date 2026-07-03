"""
AI分析器 - 增强版
"""
import os
import json
from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger
from openai import OpenAI

from data.db_manager import db_manager
from config import get_config
from src.ai.ai_data_preparer import ai_data_preparer
from src.ai.ai_prompt_builder import ai_prompt_builder
from src.ai.ai_suggestion_parser import ai_suggestion_parser


class AIAnalyzer:
    def __init__(self):
        self.config = get_config()
        self.ai_config = self.config.get('ai', {})
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        model = os.getenv('OPENAI_MODEL') or self.ai_config.get('model', 'gpt-4')
        if api_key:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            self.model = model
            logger.info(f"AI分析器初始化完成, 模型: {self.model}")
        else:
            self.client = None
            self.model = None
            logger.warning("未配置OPENAI_API_KEY")
    
    def run_daily_analysis(self, date: Optional[str] = None, lookback_days: int = 7) -> Optional[Dict[str, Any]]:
        if not self.client:
            logger.error("OpenAI客户端未初始化")
            return None
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        try:
            logger.info(f"开始AI分析: {date}")
            analysis_data = ai_data_preparer.prepare_daily_analysis_data(date, lookback_days)
            if not analysis_data:
                return None
            prompt = ai_prompt_builder.build_daily_analysis_prompt(analysis_data)
            ai_response = self._call_openai_api(prompt)
            if not ai_response:
                return None
            parsed_result = ai_suggestion_parser.parse_analysis_result(ai_response)
            if parsed_result:
                self._save_to_database(date, parsed_result, ai_response)
            logger.success("AI分析完成")
            return parsed_result
        except Exception as e:
            logger.exception(f"AI分析失败: {e}")
            return None
    
    def _call_openai_api(self, prompt: str, max_tokens: Optional[int] = None) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的量化交易分析师。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens or self.ai_config.get('max_tokens', 3000),
                temperature=self.ai_config.get('temperature', 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI调用失败: {e}")
            return None
    
    def _save_to_database(self, date: str, parsed_result: Dict[str, Any], raw_response: str):
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ai_analysis_log (analysis_date, market_summary, suggestions, model_version, raw_response) VALUES (?, ?, ?, ?, ?)",
                (date, parsed_result.get('market_summary', ''), json.dumps(parsed_result, ensure_ascii=False), self.ai_config.get('model', 'gpt-4'), raw_response)
            )
            conn.commit()
        except Exception as e:
            logger.error(f"保存失败: {e}")

ai_analyzer = AIAnalyzer()
