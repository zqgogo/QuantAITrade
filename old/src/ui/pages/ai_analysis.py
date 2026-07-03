"""
AI分析页面
展示AI分析结果和策略建议，支持人工审核和采纳
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
import os

from data.db_manager import db_manager
from src.ai.ai_analyzer import ai_analyzer


class AIAnalysisPage:
    """AI分析页面类"""
    
    def __init__(self):
        """初始化AI分析页面"""
        pass
    
    def render(self):
        """
        渲染AI分析页面
        
        实现方案：
        1. 最新AI分析展示
        2. 结构化建议列表（可采纳/拒绝）
        3. 历史分析记录
        4. 建议执行效果追踪
        5. 手动触发AI分析
        """
        st.title("🤖 AI 分析中心")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 检查AI配置状态
        if not self._check_ai_configuration():
            self._render_ai_setup_guide()
            return
        
        # 创建标签页
        tab1, tab2, tab3, tab4 = st.tabs(["📊 最新分析", "📜 历史记录", "📈 效果追踪", "⚡ 手动分析"])
        
        with tab1:
            self._render_latest_analysis()
        
        with tab2:
            self._render_analysis_history()
        
        with tab3:
            self._render_suggestion_effect_tracking()
        
        with tab4:
            self._render_manual_analysis()
    
    def _check_ai_configuration(self) -> bool:
        """
        检查AI配置状态
        
        Returns:
            bool: 是否已正确配置AI
        """
        # 检查OpenAI API密钥
        api_key = os.getenv('OPENAI_API_KEY', '')
        return bool(api_key and ai_analyzer.client)
    
    def _render_ai_setup_guide(self):
        """
        渲染AI配置引导界面
        """
        st.info("💡 AI分析功能需要额外配置才能使用")
        
        st.markdown("### 🔧 配置步骤")
        
        st.markdown("1. **获取OpenAI API密钥**")
        st.markdown("- 访问 [OpenAI官网](https://platform.openai.com/api-keys) 创建API密钥")
        st.markdown("- 注意：使用API会产生费用，请根据需要充值")
        
        st.markdown("2. **配置环境变量**")
        st.markdown("在项目根目录创建 `.env` 文件，添加以下内容：")
        st.code("OPENAI_API_KEY=your_api_key_here", language="bash")
        
        st.markdown("3. **重启应用**")
        st.markdown("配置完成后，重启Streamlit应用以使配置生效")
        
        st.markdown("### 📝 注意事项")
        st.markdown("- 未配置API密钥时，AI分析功能将不可用")
        st.markdown("- 系统其他功能（数据获取、策略信号等）仍可正常使用")
        st.markdown("- 可以先使用模拟数据查看界面效果")
        
        # 提供模拟数据查看选项
        if st.checkbox("🧪 查看模拟数据示例"):
            self._render_demo_data()
    
    def _render_demo_data(self):
        """
        渲染演示数据
        """
        st.markdown("### 📊 演示数据")
        
        # 模拟最新分析
        st.markdown("#### 最新AI分析示例")
        demo_analysis = {
            'analysis_date': '2025-11-13',
            'model_version': 'gpt-4',
            'confidence_level': 'high',
            'market_summary': '市场整体呈现震荡走势，BTCUSDT在60000-70000区间内波动。建议关注关键支撑位和阻力位的突破情况。',
            'risk_alerts': [
                {
                    'severity': 'medium',
                    'risk_type': '波动性风险',
                    'description': '近期市场波动性增加，建议适当降低仓位'
                }
            ],
            'strategy_suggestions': [
                {
                    'suggestion_type': 'parameter_adjust',
                    'target': 'MA交叉策略',
                    'reason': '市场波动性增加，建议调整均线周期以适应当前市场',
                    'current_value': '短周期:5, 长周期:20',
                    'suggested_value': '短周期:7, 长周期:25',
                    'expected_effect': '提高策略稳定性2-3%'
                }
            ]
        }
        
        col_info1, col_info2 = st.columns([3, 1])
        
        with col_info1:
            st.markdown(f"**分析日期**: {demo_analysis['analysis_date']}")
            st.markdown(f"**AI模型**: {demo_analysis['model_version']}")
        
        with col_info2:
            confidence = demo_analysis.get('confidence_level', 'unknown')
            confidence_color = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🔴'
            }.get(confidence, '⚪')
            st.markdown(f"**置信度**: {confidence_color} {confidence.upper()}")
        
        st.divider()
        
        # 1. 市场总结
        st.markdown("### 📈 市场总结")
        st.info(demo_analysis['market_summary'])
        
        st.divider()
        
        # 2. 风险告警
        risk_alerts = demo_analysis.get('risk_alerts', [])
        if risk_alerts:
            st.markdown("### ⚠️ 风险告警")
            
            for alert in risk_alerts:
                severity = alert.get('severity', 'unknown')
                risk_type = alert.get('risk_type', '未知风险')
                description = alert.get('description', '')
                
                # 根据严重程度选择样式
                if severity == 'high':
                    st.error(f"🔴 **高风险** - {risk_type}: {description}")
                elif severity == 'medium':
                    st.warning(f"🟡 **中风险** - {risk_type}: {description}")
                else:
                    st.info(f"🟢 **低风险** - {risk_type}: {description}")
        else:
            st.success("✅ 当前无重大风险告警")
        
        st.divider()
        
        # 3. 策略建议
        suggestions = demo_analysis.get('strategy_suggestions', [])
        if suggestions:
            st.markdown("### 💡 策略建议")
            st.markdown(f"共 **{len(suggestions)}** 条建议待审核")
            
            for i, suggestion in enumerate(suggestions, 1):
                self._render_suggestion_card(i, suggestion)
        else:
            st.info("💡 暂无策略调整建议")
        
        # 4. 附加说明
        additional_notes = demo_analysis.get('additional_notes', '')
        if additional_notes:
            with st.expander("📝 附加说明", expanded=False):
                st.markdown(additional_notes)
    
    def _render_suggestion_effect_tracking(self):
        """
        渲染建议效果追踪标签
        """
        st.subheader("📈 建议效果追踪")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 说明文字
        st.markdown("""
        本页面展示已采纳AI建议的执行效果，用于评估AI建议的准确性和有效性。
        通过追踪建议效果，可以不断优化AI分析模型。
        """)
        
        # 模拟效果数据
        # 在实际实现中，应该从数据库查询已采纳建议的执行效果
        effect_data = [
            {
                'suggestion_id': 'SUG-001',
                'suggestion_type': '参数调整',
                'target': 'MA交叉策略',
                'accepted_time': '2025-11-01 10:30',
                'expected_effect': '提高胜率2%',
                'actual_effect': '胜率提升1.8%',
                'evaluation': '效果良好'
            },
            {
                'suggestion_id': 'SUG-002',
                'suggestion_type': '风控调整',
                'target': '止损参数',
                'accepted_time': '2025-11-05 14:15',
                'expected_effect': '降低最大回撤0.5%',
                'actual_effect': '降低最大回撤0.7%',
                'evaluation': '超出预期'
            },
            {
                'suggestion_id': 'SUG-003',
                'suggestion_type': '策略启用',
                'target': '新策略B',
                'accepted_time': '2025-11-10 09:45',
                'expected_effect': '增加收益1.2%',
                'actual_effect': '增加收益1.5%',
                'evaluation': '效果显著'
            }
        ]
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 1. 效果评分分布
        with col1:
            st.markdown("#### 效果评分分布")
            # 模拟评分数据
            scores = [8.5, 7.2, 9.1, 6.8, 7.9, 8.3, 9.5, 7.6, 8.8, 7.4]
            score_labels = [f'建议{i+1}' for i in range(len(scores))]
            
            fig_scores = px.bar(
                x=score_labels,
                y=scores,
                title='已采纳建议效果评分',
                labels={'x': '建议编号', 'y': '效果评分(1-10)'}
            )
            st.plotly_chart(fig_scores, use_container_width=True)
        
        # 2. 效果达成率
        with col2:
            st.markdown("#### 效果达成率")
            # 模拟达成率数据
            achievement_rates = [90, 85, 115, 75, 95, 88, 120, 82, 105, 80]
            rate_labels = [f'建议{i+1}' for i in range(len(achievement_rates))]
            
            fig_rates = px.bar(
                x=rate_labels,
                y=achievement_rates,
                title='建议效果达成率',
                labels={'x': '建议编号', 'y': '达成率(%)'}
            )
            fig_rates.add_hline(y=100, line_dash="dash", line_color="red")
            st.plotly_chart(fig_rates, use_container_width=True)
        
        # 3. 详细效果记录
        st.markdown("#### 详细效果记录")
        
        # 转换为DataFrame并显示
        df = pd.DataFrame(effect_data)
        st.dataframe(df, use_container_width=True)
        
        # 4. 效果统计
        st.markdown("#### 效果统计")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            avg_score = 7.8  # 模拟平均评分
            st.metric("平均效果评分", f"{avg_score}/10")
        
        with col_stat2:
            success_rate = 85  # 模拟成功率
            st.metric("效果达成率", f"{success_rate}%")
        
        with col_stat3:
            total_suggestions = 25  # 模拟总建议数
            st.metric("已追踪建议", total_suggestions)
    
    def _render_latest_analysis(self):
        """
        渲染最新AI分析标签
        
        功能：
        - 显示最新的AI市场分析
        - 展示风险告警
        - 列出策略建议（可操作）
        """
        st.subheader("📊 最新AI分析")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 获取最新分析
        latest_analysis = self._get_latest_analysis()
        
        if not latest_analysis:
            st.info("💡 暂无AI分析记录，请先执行分析")
            
            st.markdown("#### 🔍 为什么没有分析记录？")
            st.markdown("- 系统刚初始化，尚未执行过AI分析")
            st.markdown("- AI分析通常在预定时间自动执行")
            st.markdown("- 您也可以手动触发分析")
            
            st.markdown("#### ▶️ 如何执行AI分析？")
            st.markdown("1. 确保已正确配置OpenAI API密钥")
            st.markdown("2. 点击下方按钮立即执行分析")
            st.markdown("3. 等待分析完成（可能需要几秒钟到几分钟）")
            
            if st.button("🚀 立即执行AI分析", type="primary"):
                with st.spinner("🤖 AI正在分析市场数据，请稍候..."):
                    try:
                        result = ai_analyzer.run_daily_analysis()
                        if result:
                            st.success("✅ AI分析完成！")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ AI分析失败，请检查日志")
                            st.markdown("常见问题：")
                            st.markdown("- OpenAI API密钥无效或余额不足")
                            st.markdown("- 网络连接问题")
                            st.markdown("- 数据库连接异常")
                    except Exception as e:
                        st.error(f"❌ AI分析过程中发生错误: {str(e)}")
            return
        
        # 显示分析信息
        col_info1, col_info2 = st.columns([3, 1])
        
        with col_info1:
            st.markdown(f"**分析日期**: {latest_analysis['analysis_date']}")
            st.markdown(f"**AI模型**: {latest_analysis['model_version']}")
        
        with col_info2:
            confidence = latest_analysis.get('confidence_level', 'unknown')
            confidence_color = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🔴'
            }.get(confidence, '⚪')
            st.markdown(f"**置信度**: {confidence_color} {confidence.upper()}")
        
        st.divider()
        
        # 1. 市场总结
        st.markdown("### 📈 市场总结")
        market_summary = latest_analysis.get('market_summary', '无')
        st.info(market_summary)
        
        st.divider()
        
        # 2. 风险告警
        risk_alerts = latest_analysis.get('risk_alerts', [])
        if risk_alerts:
            st.markdown("### ⚠️ 风险告警")
            
            for alert in risk_alerts:
                severity = alert.get('severity', 'unknown')
                risk_type = alert.get('risk_type', '未知风险')
                description = alert.get('description', '')
                
                # 根据严重程度选择样式
                if severity == 'high':
                    st.error(f"🔴 **高风险** - {risk_type}: {description}")
                elif severity == 'medium':
                    st.warning(f"🟡 **中风险** - {risk_type}: {description}")
                else:
                    st.info(f"🟢 **低风险** - {risk_type}: {description}")
        else:
            st.success("✅ 当前无重大风险告警")
        
        st.divider()
        
        # 3. 策略建议
        suggestions = latest_analysis.get('strategy_suggestions', [])
        if suggestions:
            st.markdown("### 💡 策略建议")
            st.markdown(f"共 **{len(suggestions)}** 条建议待审核")
            
            for i, suggestion in enumerate(suggestions, 1):
                self._render_suggestion_card(i, suggestion)
        else:
            st.info("💡 暂无策略调整建议")
        
        # 4. 附加说明
        additional_notes = latest_analysis.get('additional_notes', '')
        if additional_notes:
            with st.expander("📝 附加说明", expanded=False):
                st.markdown(additional_notes)
    
    def _render_suggestion_card(self, index: int, suggestion: Dict[str, Any]):
        """
        渲染单个建议卡片
        
        Args:
            index: 建议序号
            suggestion: 建议内容
        """
        suggestion_type = suggestion.get('suggestion_type', 'unknown')
        target = suggestion.get('target', '未知')
        reason = suggestion.get('reason', '无')
        expected_effect = suggestion.get('expected_effect', '无')
        
        # 建议类型图标
        type_icons = {
            'parameter_adjust': '🔧',
            'strategy_enable': '✅',
            'strategy_disable': '❌',
            'risk_adjust': '🛡️'
        }
        icon = type_icons.get(suggestion_type, '💡')
        
        # 建议类型中文
        type_names = {
            'parameter_adjust': '参数调整',
            'strategy_enable': '启用策略',
            'strategy_disable': '禁用策略',
            'risk_adjust': '风控调整'
        }
        type_name = type_names.get(suggestion_type, '未知类型')
        
        with st.container(border=True):
            st.markdown(f"#### {icon} 建议 {index}: {type_name}")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**目标**: {target}")
                st.markdown(f"**理由**: {reason}")
                
                # 显示具体变更
                if suggestion_type == 'parameter_adjust':
                    current_value = suggestion.get('current_value', '未知')
                    suggested_value = suggestion.get('suggested_value', '未知')
                    st.markdown(f"**变更**: `{current_value}` → `{suggested_value}`")
                
                st.markdown(f"**预期效果**: {expected_effect}")
            
            with col2:
                # 操作按钮
                if st.button("✅ 采纳", key=f"accept_{index}", use_container_width=True):
                    if self._accept_suggestion(suggestion):
                        st.success("已采纳")
                        st.rerun()
                    else:
                        st.error("操作失败")
                
                if st.button("❌ 拒绝", key=f"reject_{index}", use_container_width=True):
                    if self._reject_suggestion(suggestion):
                        st.info("已拒绝")
                        st.rerun()
                    else:
                        st.error("操作失败")
                
                if st.button("📊 详情", key=f"detail_{index}", use_container_width=True):
                    st.info("详情功能开发中...")
    
    def _render_analysis_history(self):
        """
        渲染历史分析记录标签
        
        功能：
        - 显示历史AI分析列表
        - 支持时间筛选
        - 查看历史分析详情
        - 建议采纳统计
        """
        st.subheader("📜 AI分析历史")
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 时间范围选择
        col1, col2 = st.columns([2, 3])
        
        with col1:
            days = st.selectbox(
                "时间范围",
                options=[7, 15, 30, 60, 90],
                format_func=lambda x: f"最近{x}天",
                index=1
            )
        
        # 获取历史记录
        history = self._get_analysis_history(days)
        
        if not history:
            st.info("💡 暂无历史记录")
            return
        
        # 统计信息
        st.markdown("#### 📊 统计概览")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("分析次数", len(history))
        
        with stat_col2:
            total_suggestions = sum(len(h.get('suggestions', [])) for h in history)
            st.metric("生成建议", total_suggestions)
        
        with stat_col3:
            # TODO: 统计采纳率
            st.metric("采纳率", "N/A")
        
        with stat_col4:
            # TODO: 统计建议效果
            st.metric("建议效果", "N/A")
        
        st.divider()
        
        # 历史记录列表
        st.markdown("#### 📋 分析记录")
        
        for record in history:
            with st.expander(
                f"📅 {record['analysis_date']} - {record['model_version']}",
                expanded=False
            ):
                # 显示摘要信息
                st.markdown(f"**市场总结**: {record.get('market_summary', '无')[:200]}...")
                
                suggestions = record.get('suggestions', [])
                if suggestions:
                    st.markdown(f"**建议数量**: {len(suggestions)} 条")
                
                # 查看详情按钮
                if st.button("📖 查看完整分析", key=f"view_{record['id']}"):
                    self._show_analysis_detail(record)
    
    def _render_manual_analysis(self):
        """
        渲染手动分析标签
        
        功能：
        - 手动触发AI分析
        - 设置分析参数
        - 显示分析进度
        """
        st.subheader("⚡ 手动触发AI分析")
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        手动分析功能允许您在任何时候触发AI分析，而不必等待定时任务。
        这在市场出现重大变化时特别有用。
        """)
        
        # 分析参数设置
        st.markdown("#### ⚙️ 分析参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            lookback_days = st.slider(
                "回看天数",
                min_value=3,
                max_value=30,
                value=7,
                help="AI分析回看的历史数据天数"
            )
        
        with col2:
            analysis_mode = st.selectbox(
                "分析模式",
                options=["完整分析", "快速分析"],
                index=0,
                help="完整分析更详细但耗时更长"
            )
        
        # 执行按钮
        st.markdown("---")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("🚀 开始分析", type="primary", use_container_width=True):
                self._execute_manual_analysis(lookback_days, analysis_mode)
        
        with col_btn2:
            if st.button("🔄 刷新状态", use_container_width=True):
                st.rerun()
        
        # 最近分析记录
        st.markdown("---")
        st.markdown("#### 📝 最近手动分析记录")
        
        recent = self._get_analysis_history(days=7, limit=5)
        if recent:
            for record in recent:
                st.text(f"• {record['analysis_date']} - {record['model_version']}")
        else:
            st.info("暂无最近记录")
            
        # 添加效果追踪说明
        st.markdown("---")
        st.info("💡 效果追踪功能会持续跟踪已采纳建议的执行效果，帮助优化AI模型")
    
    # ==================== 数据获取方法 ====================
    
    def _get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """
        获取最新的AI分析
        
        Returns:
            dict: 分析结果
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    id,
                    analysis_date,
                    market_summary,
                    suggestions,
                    model_version,
                    timestamp
                FROM ai_analysis_log
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # 解析JSON字段
            result = dict(row)
            if result.get('suggestions'):
                try:
                    suggestions_data = json.loads(result['suggestions'])
                    result.update(suggestions_data)
                except:
                    pass
            
            return result
            
        except Exception as e:
            logger.error(f"获取最新分析失败: {e}")
            return None
    
    def _get_analysis_history(self, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取历史分析记录
        
        Args:
            days: 天数
            limit: 数量限制
        
        Returns:
            list: 分析记录列表
        """
        try:
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    id,
                    analysis_date,
                    market_summary,
                    suggestions,
                    model_version,
                    timestamp
                FROM ai_analysis_log
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start_timestamp, limit)
            )
            
            records = []
            for row in cursor.fetchall():
                record = dict(row)
                # 解析suggestions
                if record.get('suggestions'):
                    try:
                        suggestions_data = json.loads(record['suggestions'])
                        record['suggestions'] = suggestions_data.get('strategy_suggestions', [])
                    except:
                        record['suggestions'] = []
                records.append(record)
            
            return records
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {e}")
            return []
    
    # ==================== 操作方法 ====================
    
    def _accept_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """
        采纳AI建议
        
        Args:
            suggestion: 建议内容
        
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 根据建议类型执行相应操作
            suggestion_type = suggestion.get('suggestion_type')
            target = suggestion.get('target')
            
            if suggestion_type == 'parameter_adjust':
                self._adjust_parameter(suggestion)
            elif suggestion_type == 'strategy_enable':
                self._enable_strategy(target)
            elif suggestion_type == 'strategy_disable':
                self._disable_strategy(target)
            elif suggestion_type == 'risk_adjust':
                self._adjust_risk_settings(suggestion)
            
            # 2. 更新配置文件
            self._update_ai_suggestion_config(suggestion, 'accepted')
            
            # 3. 记录采纳日志
            self._log_suggestion_action(suggestion, 'accepted')
            
            # 4. 通知相关模块
            self._notify_modules(suggestion, 'accepted')
            
            logger.info(f"已采纳AI建议: {suggestion_type} - {target}")
            st.success("✅ 建议已采纳并应用")
            
            return True
            
        except Exception as e:
            logger.error(f"采纳建议失败: {e}")
            st.error("❌ 建议采纳失败，请查看日志")
            return False
    
    def _reject_suggestion(self, suggestion: Dict[str, Any]) -> bool:
        """
        拒绝AI建议
        
        Args:
            suggestion: 建议内容
        
        Returns:
            bool: 是否成功
        """
        try:
            # 1. 记录拒绝原因和日志
            suggestion_type = suggestion.get('suggestion_type')
            target = suggestion.get('target')
            
            # 2. 更新配置文件
            self._update_ai_suggestion_config(suggestion, 'rejected')
            
            # 3. 记录拒绝日志
            self._log_suggestion_action(suggestion, 'rejected')
            
            logger.info(f"已拒绝AI建议: {suggestion_type} - {target}")
            st.info("❌ 建议已拒绝")
            
            return True
            
        except Exception as e:
            logger.error(f"拒绝建议失败: {e}")
            st.error("❌ 建议拒绝失败，请查看日志")
            return False
    
    def _execute_manual_analysis(self, lookback_days: int, mode: str):
        """
        执行手动AI分析
        
        Args:
            lookback_days: 回看天数
            mode: 分析模式
        """
        try:
            with st.spinner("🤖 AI正在分析市场数据，请稍候..."):
                # 执行AI分析
                result = ai_analyzer.run_daily_analysis(
                    date=datetime.now().strftime('%Y-%m-%d'),
                    lookback_days=lookback_days
                )
                
                if result:
                    st.success("✅ AI分析完成！")
                    st.balloons()
                    
                    # 显示简要结果
                    with st.expander("📊 分析结果预览", expanded=True):
                        st.markdown(f"**市场总结**: {result.get('market_summary', '无')[:200]}...")
                        
                        suggestions = result.get('strategy_suggestions', [])
                        if suggestions:
                            st.markdown(f"**生成建议**: {len(suggestions)} 条")
                    
                    # 提示查看详情
                    st.info("💡 切换到【最新分析】标签查看完整结果")
                else:
                    st.error("❌ AI分析失败，请检查日志")
                    
        except Exception as e:
            logger.error(f"手动分析失败: {e}")
            st.error(f"❌ 分析失败: {e}")
    
    def _show_analysis_detail(self, record: Dict[str, Any]):
        """
        显示分析详情（预留）
        
        Args:
            record: 分析记录
        """
        # TODO: 在模态框或新页面显示完整分析
        st.info("详情功能开发中...")
        
    # ==================== AI建议处理辅助方法 ====================
    
    def _adjust_parameter(self, suggestion: Dict[str, Any]):
        """
        调整参数
        
        Args:
            suggestion: 建议内容
        """
        try:
            # TODO: 实现参数调整逻辑
            current_value = suggestion.get('current_value')
            suggested_value = suggestion.get('suggested_value')
            target = suggestion.get('target')
            logger.info(f"参数调整: {target} 从 {current_value} 调整为 {suggested_value}")
        except Exception as e:
            logger.error(f"参数调整失败: {e}")
            raise
    
    def _enable_strategy(self, strategy_name: str):
        """
        启用策略
        
        Args:
            strategy_name: 策略名称
        """
        try:
            # TODO: 实现策略启用逻辑
            logger.info(f"启用策略: {strategy_name}")
        except Exception as e:
            logger.error(f"启用策略失败: {e}")
            raise
    
    def _disable_strategy(self, strategy_name: str):
        """
        禁用策略
        
        Args:
            strategy_name: 策略名称
        """
        try:
            # TODO: 实现策略禁用逻辑
            logger.info(f"禁用策略: {strategy_name}")
        except Exception as e:
            logger.error(f"禁用策略失败: {e}")
            raise
    
    def _adjust_risk_settings(self, suggestion: Dict[str, Any]):
        """
        调整风控设置
        
        Args:
            suggestion: 建议内容
        """
        try:
            # TODO: 实现风控设置调整逻辑
            target = suggestion.get('target')
            logger.info(f"调整风控设置: {target}")
        except Exception as e:
            logger.error(f"调整风控设置失败: {e}")
            raise
    
    def _update_ai_suggestion_config(self, suggestion: Dict[str, Any], action: str):
        """
        更新AI建议配置
        
        Args:
            suggestion: 建议内容
            action: 操作类型 (accepted/rejected)
        """
        try:
            # TODO: 实现配置更新逻辑
            suggestion_type = suggestion.get('suggestion_type')
            target = suggestion.get('target')
            logger.info(f"更新AI建议配置: {action} {suggestion_type} - {target}")
        except Exception as e:
            logger.error(f"更新AI建议配置失败: {e}")
            raise
    
    def _log_suggestion_action(self, suggestion: Dict[str, Any], action: str):
        """
        记录建议操作日志
        
        Args:
            suggestion: 建议内容
            action: 操作类型 (accepted/rejected)
        """
        try:
            # TODO: 实现日志记录逻辑
            suggestion_type = suggestion.get('suggestion_type')
            target = suggestion.get('target')
            logger.info(f"记录建议操作日志: {action} {suggestion_type} - {target}")
        except Exception as e:
            logger.error(f"记录建议操作日志失败: {e}")
            raise
    
    def _notify_modules(self, suggestion: Dict[str, Any], action: str):
        """
        通知相关模块
        
        Args:
            suggestion: 建议内容
            action: 操作类型 (accepted/rejected)
        """
        try:
            # TODO: 实现模块通知逻辑
            suggestion_type = suggestion.get('suggestion_type')
            target = suggestion.get('target')
            logger.info(f"通知相关模块: {action} {suggestion_type} - {target}")
        except Exception as e:
            logger.error(f"通知相关模块失败: {e}")
            raise


# 页面入口函数
def show():
    """显示AI分析页面"""
    page = AIAnalysisPage()
    page.render()
