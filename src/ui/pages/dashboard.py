"""
仪表盘页面
展示系统运行状态、账户信息、持仓和交易记录
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger

from data.db_manager import db_manager
from src.execution.exchange_connector import exchange_connector
from src.execution.position_tracker import position_tracker


class DashboardPage:
    """仪表盘页面类"""
    
    def __init__(self):
        """初始化仪表盘页面"""
        self.refresh_interval = 60  # 数据刷新间隔（秒）
    
    def render(self):
        """
        渲染仪表盘页面
        
        实现方案：
        1. 账户总览卡片（总资产、持仓数、盈亏等）
        2. 持仓列表表格（可排序、可筛选）
        3. 最近交易记录
        4. 策略绩效图表
        5. 资产曲线图
        """
        st.title("📊 系统仪表盘")
        
        # 添加刷新按钮和自动刷新设置
        col_refresh1, col_refresh2 = st.columns([6, 1])
        with col_refresh2:
            if st.button("🔄 刷新", use_container_width=True):
                st.rerun()
        
        # 1. 账户总览
        self._render_account_overview()
        
        st.divider()
        
        # 2. 持仓列表
        self._render_positions_list()
        
        st.divider()
        
        # 3. 最近交易
        self._render_recent_trades()
        
        st.divider()
        
        # 4. 策略绩效（预留）
        with st.expander("📈 策略绩效分析", expanded=False):
            self._render_strategy_performance()
        
        # 5. 资产曲线（预留）
        with st.expander("💰 资产曲线", expanded=False):
            self._render_equity_curve()
    
    def _render_account_overview(self):
        """
        渲染账户总览卡片
        
        显示内容：
        - 总资产（USDT）
        - 可用余额
        - 持仓数量
        - 今日盈亏
        - 总收益率
        """
        st.subheader("💰 账户总览")
        
        # 获取账户数据
        account_data = self._get_account_data()
        
        # 创建4列布局
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_balance = account_data.get('total_balance', 0)
            st.metric(
                label="总资产", 
                value=f"{total_balance:.2f} USDT",
                delta=None  # TODO: 计算24小时变化
            )
        
        with col2:
            available_balance = account_data.get('available_balance', 0)
            position_count = account_data.get('position_count', 0)
            st.metric(
                label="可用余额",
                value=f"{available_balance:.2f} USDT",
                delta=None
            )
        
        with col3:
            st.metric(
                label="持仓数量",
                value=position_count,
                delta=None  # TODO: 与昨日对比
            )
        
        with col4:
            total_pnl = account_data.get('total_unrealized_pnl', 0)
            pnl_percent = account_data.get('total_pnl_percent', 0)
            st.metric(
                label="浮动盈亏",
                value=f"{total_pnl:.2f} USDT",
                delta=f"{pnl_percent:.2f}%"
            )
        
        # 风险指标（第二行）
        st.markdown("#### 风险指标")
        col5, col6, col7, col8 = st.columns(4)
        
        with col5:
            position_ratio = account_data.get('position_ratio', 0)
            st.metric(
                label="仓位占比",
                value=f"{position_ratio:.1f}%",
                delta=None
            )
        
        with col6:
            max_drawdown = account_data.get('max_drawdown', 0)
            st.metric(label="最大回撤", value=f"{max_drawdown:.2f}%", delta=None)
        
        with col7:
            win_rate = account_data.get('win_rate', 0)
            st.metric(label="交易胜率", value=f"{win_rate:.1f}%", delta=None)
        
        with col8:
            sharpe_ratio = account_data.get('sharpe_ratio', 0)
            st.metric(label="夏普比率", value=f"{sharpe_ratio:.2f}", delta=None)
    
    def _render_positions_list(self):
        """
        渲染持仓列表
        
        功能：
        - 显示所有开仓持仓
        - 支持按盈亏排序
        - 显示止损价格
        - 提供快速平仓按钮（预留）
        """
        st.subheader("📈 当前持仓")
        
        # 获取持仓数据
        positions = self._get_positions_data()
        
        if not positions:
            st.info("💡 当前无持仓")
            return
        
        # 转换为DataFrame
        df = pd.DataFrame(positions)
        
        # 格式化列
        if not df.empty:
            # 添加颜色标记
            def color_pnl(val):
                color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                return f'color: {color}'
            
            # 显示表格
            st.dataframe(
                df.style.applymap(color_pnl, subset=['unrealized_pnl', 'unrealized_pnl_percent']),
                use_container_width=True,
                height=300
            )
            
            # 操作按钮区域
            st.markdown("##### 批量操作")
            col_op1, col_op2, col_op3 = st.columns([1, 1, 4])
            
            with col_op1:
                if st.button("📤 导出持仓", use_container_width=True):
                    self._export_positions_to_csv()
            
            with col_op2:
                if st.button("⚠️ 全部止损", use_container_width=True):
                    self._close_all_positions()
    
    def _render_recent_trades(self):
        """
        渲染最近交易记录
        
        功能：
        - 显示最近N笔交易
        - 支持时间筛选
        - 显示交易状态
        - 计算盈亏统计
        """
        st.subheader("💼 最近交易")
        
        # 时间范围选择
        col_time1, col_time2, col_time3 = st.columns([2, 2, 2])
        
        with col_time1:
            time_range = st.selectbox(
                "时间范围",
                options=["今天", "最近3天", "最近7天", "最近30天"],
                index=1
            )
        
        with col_time2:
            limit = st.number_input("显示条数", min_value=5, max_value=100, value=20)
        
        # 获取交易记录
        trades = self._get_trade_records(time_range, limit)
        
        if not trades:
            st.info("💡 暂无交易记录")
            return
        
        # 显示统计信息
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric("总交易次数", len(trades))
        
        with stats_col2:
            successful = len([t for t in trades if t.get('status') == 'FILLED'])
            st.metric("成功执行", successful)
        
        with stats_col3:
            success_rate = (successful / len(trades) * 100) if trades else 0
            st.metric("成功率", f"{success_rate:.1f}%")
        
        with stats_col4:
            total_pnl = self._calculate_total_pnl(trades)
            st.metric("总盈亏", f"{total_pnl:.2f} USDT")
        
        # 显示交易表格
        df = pd.DataFrame(trades)
        if not df.empty:
            st.dataframe(df, use_container_width=True, height=400)
    
    def _render_strategy_performance(self):
        """
        渲染策略绩效分析
        
        实现功能：
        - 各策略收益对比
        - 策略信号统计
        - 策略胜率分析
        """
        st.markdown("### 📊 策略绩效对比")
        
        # 从数据库获取策略绩效数据
        strategy_stats = self._get_strategy_performance()
        
        if strategy_stats.empty:
            st.info("💡 暂无策略绩效数据")
            return
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 1. 收益对比柱状图
        with col1:
            st.markdown("#### 收益对比")
            fig_return = px.bar(
                strategy_stats, 
                x='strategy_name', 
                y='total_return', 
                title='各策略收益对比',
                labels={'strategy_name': '策略名称', 'total_return': '总收益(%)'}
            )
            st.plotly_chart(fig_return, use_container_width=True)
        
        # 2. 胜率对比柱状图
        with col2:
            st.markdown("#### 胜率对比")
            fig_win_rate = px.bar(
                strategy_stats, 
                x='strategy_name', 
                y='win_rate', 
                title='各策略胜率对比',
                labels={'strategy_name': '策略名称', 'win_rate': '胜率(%)'}
            )
            st.plotly_chart(fig_win_rate, use_container_width=True)
        
        # 3. 信号数量饼图
        st.markdown("#### 信号分布")
        fig_signals = px.pie(
            strategy_stats, 
            values='signal_count', 
            names='strategy_name', 
            title='各策略信号数量分布'
        )
        st.plotly_chart(fig_signals, use_container_width=True)
        
        # 4. 数据表格
        st.markdown("#### 详细数据")
        st.dataframe(strategy_stats, use_container_width=True)
    
    def _render_equity_curve(self):
        """
        渲染资产曲线图
        
        实现功能：
        - 账户权益历史曲线
        - 回撤区域标注
        - 关键事件标记
        """
        st.markdown("### 💰 账户权益曲线")
        
        # 计算权益曲线
        equity_data = self._calculate_equity_curve()
        
        if equity_data.empty:
            st.info("💡 暂无权益曲线数据")
            return
        
        # 创建图表
        fig = go.Figure()
        
        # 添加权益曲线
        fig.add_trace(
            go.Scatter(
                x=equity_data['date'], 
                y=equity_data['equity'], 
                mode='lines',
                name='账户权益',
                line=dict(color='blue')
            )
        )
        
        # 添加回撤曲线
        fig.add_trace(
            go.Scatter(
                x=equity_data['date'], 
                y=equity_data['drawdown'], 
                mode='lines',
                name='回撤(%)',
                line=dict(color='red'),
                yaxis='y2'
            )
        )
        
        # 设置图表布局
        fig.update_layout(
            title='账户权益与回撤曲线',
            xaxis_title='日期',
            yaxis_title='账户权益',
            yaxis2=dict(
                title='回撤(%)',
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0, y=1)
        )
        
        # 显示图表
        st.plotly_chart(fig, use_container_width=True)
        
        # 显示数据表格
        st.markdown("#### 详细数据")
        st.dataframe(equity_data, use_container_width=True)
    
    # ==================== 数据获取方法 ====================
    
    def _get_account_data(self) -> Dict[str, Any]:
        """
        获取账户数据
        
        Returns:
            dict: 包含账户余额、持仓等信息
        """
        try:
            # 1. 获取交易所余额
            balance_info = exchange_connector.get_account_balance()
            usdt_info = balance_info.get('USDT', {}) if balance_info else {}
            
            total_balance = usdt_info.get('total', 10000.0)  # 默认值
            available_balance = usdt_info.get('free', total_balance)
            
            # 2. 获取持仓信息
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as position_count,
                    SUM(entry_price * quantity) as total_exposure,
                    SUM(unrealized_pnl) as total_pnl
                FROM positions
                WHERE status = 'OPEN'
                """
            )
            
            position_data = cursor.fetchone()
            position_count = position_data['position_count'] or 0
            total_exposure = position_data['total_exposure'] or 0
            total_pnl = position_data['total_pnl'] or 0
            
            # 3. 计算派生指标
            position_ratio = (total_exposure / total_balance * 100) if total_balance > 0 else 0
            pnl_percent = (total_pnl / total_balance * 100) if total_balance > 0 else 0
            
            # 计算额外的风险指标
            max_drawdown = self._calculate_max_drawdown()
            win_rate = self._calculate_win_rate()
            sharpe_ratio = self._calculate_sharpe_ratio()
            
            return {
                'total_balance': total_balance,
                'available_balance': available_balance,
                'position_count': position_count,
                'total_exposure': total_exposure,
                'total_unrealized_pnl': total_pnl,
                'total_pnl_percent': pnl_percent,
                'position_ratio': position_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'sharpe_ratio': sharpe_ratio
            }
            
        except Exception as e:
            logger.error(f"获取账户数据失败: {e}")
            return {
                'total_balance': 0,
                'available_balance': 0,
                'position_count': 0,
                'total_unrealized_pnl': 0,
                'total_pnl_percent': 0,
                'position_ratio': 0
            }
    
    def _get_positions_data(self) -> List[Dict[str, Any]]:
        """
        获取持仓数据
        
        Returns:
            list: 持仓列表
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    symbol,
                    entry_price,
                    quantity,
                    unrealized_pnl,
                    unrealized_pnl_percent,
                    stop_loss_price,
                    stop_loss_type,
                    datetime(entry_time, 'unixepoch') as entry_time,
                    highest_price
                FROM positions
                WHERE status = 'OPEN'
                ORDER BY entry_time DESC
                """
            )
            
            positions = [dict(row) for row in cursor.fetchall()]
            return positions
            
        except Exception as e:
            logger.error(f"获取持仓数据失败: {e}")
            return []
    
    def _get_trade_records(self, time_range: str, limit: int) -> List[Dict[str, Any]]:
        """
        获取交易记录
        
        Args:
            time_range: 时间范围
            limit: 记录数量
        
        Returns:
            list: 交易记录列表
        """
        try:
            # 计算时间范围
            days_map = {
                "今天": 1,
                "最近3天": 3,
                "最近7天": 7,
                "最近30天": 30
            }
            days = days_map.get(time_range, 7)
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT 
                    symbol,
                    side,
                    price,
                    quantity,
                    status,
                    order_id,
                    datetime(timestamp, 'unixepoch') as time
                FROM trade_records
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start_timestamp, limit)
            )
            
            trades = [dict(row) for row in cursor.fetchall()]
            return trades
            
        except Exception as e:
            logger.error(f"获取交易记录失败: {e}")
            return []
    
    # ==================== 预留的扩展方法 ====================
    
    def _get_strategy_performance(self) -> pd.DataFrame:
        """
        获取策略绩效数据（待实现）
        
        计划返回：
        - 策略名称
        - 交易次数
        - 胜率
        - 总收益
        - 夏普比率
        """
        # TODO: 实现策略绩效统计
        pass
    
    def _calculate_equity_curve(self) -> pd.DataFrame:
        """
        计算账户权益曲线（待实现）
        
        计划返回：
        - 日期
        - 权益值
        - 回撤值
        """
        # TODO: 实现权益曲线计算
        pass
    
    def _export_positions_to_csv(self) -> str:
        """
        导出持仓到CSV
        
        Returns:
            str: CSV文件路径
        """
        try:
            # 获取当前持仓数据
            positions = self._get_positions_data()
            
            # 转换为DataFrame
            df = pd.DataFrame(positions)
            
            # 生成文件名
            filename = f"positions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # 导出到CSV
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            st.success(f"✅ 持仓已导出到 {filename}")
            return filename
        except Exception as e:
            logger.error(f"导出持仓失败: {e}")
            st.error("❌ 导出失败，请查看日志")
            return ""
    
    def _close_all_positions(self):
        """
        全部平仓操作
        """
        try:
            # TODO: 调用交易执行模块进行全部平仓
            st.info("⚠️ 全部平仓功能开发中...")
            # 这里需要与交易执行模块集成
        except Exception as e:
            logger.error(f"全部平仓操作失败: {e}")
            st.error("❌ 全部平仓操作失败，请查看日志")
    
    # ==================== 风险指标计算方法 ====================
    
    def _calculate_max_drawdown(self) -> float:
        """
        计算最大回撤
        
        Returns:
            float: 最大回撤百分比
        """
        try:
            # TODO: 从数据库获取历史净值数据并计算最大回撤
            # 这里暂时返回默认值
            return 0.0
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return 0.0
    
    def _calculate_win_rate(self) -> float:
        """
        计算交易胜率
        
        Returns:
            float: 胜率百分比
        """
        try:
            # TODO: 从数据库获取交易记录并计算胜率
            # 这里暂时返回默认值
            return 0.0
        except Exception as e:
            logger.error(f"计算交易胜率失败: {e}")
            return 0.0
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        计算夏普比率
        
        Returns:
            float: 夏普比率
        """
        try:
            # TODO: 基于历史收益数据计算夏普比率
            # 这里暂时返回默认值
            return 0.0
        except Exception as e:
            logger.error(f"计算夏普比率失败: {e}")
            return 0.0
    
    def _calculate_total_pnl(self, trades: List[Dict[str, Any]]) -> float:
        """
        计算总盈亏
        
        Args:
            trades: 交易记录列表
        
        Returns:
            float: 总盈亏
        """
        try:
            # TODO: 基于交易记录计算总盈亏
            # 这里暂时返回默认值
            return 0.0
        except Exception as e:
            logger.error(f"计算总盈亏失败: {e}")
            return 0.0


# 页面入口函数
def show():
    """显示仪表盘页面"""
    dashboard = DashboardPage()
    dashboard.render()
