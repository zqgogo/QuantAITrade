"""
策略控制页面
管理策略的启停、参数调整和信号查看
"""

import streamlit as st
import pandas as pd
import yaml
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from loguru import logger
from pathlib import Path

from config import get_config, get_strategy_config
from data.db_manager import db_manager
from strategy import MACrossStrategy


class StrategyControlPage:
    """策略控制页面类"""
    
    def __init__(self):
        """初始化策略控制页面"""
        self.config = get_config()
        self.strategy_config = get_strategy_config()
        self.config_path = Path("config/strategy_params.yaml")
    
    def render(self):
        """
        渲染策略控制页面
        
        实现方案：
        1. 策略列表展示（状态、绩效）
        2. 策略启停控制
        3. 参数调整表单
        4. 最近信号查看
        5. 快速回测功能
        """
        st.title("⚙️ 策略控制中心")
        
        # 创建标签页
        tab1, tab2, tab3 = st.tabs(["📋 策略管理", "🎯 策略信号", "🔧 参数调整"])
        
        with tab1:
            self._render_strategy_management()
        
        with tab2:
            self._render_strategy_signals()
        
        with tab3:
            self._render_parameter_adjustment()
    
    def _render_strategy_management(self):
        """
        渲染策略管理标签
        
        功能：
        - 显示所有可用策略
        - 策略启停开关
        - 策略绩效概览
        """
        st.subheader("📋 策略列表")
        
        # 获取策略列表
        strategies = self._get_strategy_list()
        
        if not strategies:
            st.warning("⚠️ 未找到可用策略")
            return
        
        # 显示每个策略的卡片
        for strategy_name, strategy_info in strategies.items():
            with st.expander(f"**{strategy_name}** - {strategy_info['status']}", expanded=True):
                # 策略信息
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown(f"**描述**: {strategy_info['description']}")
                    st.markdown(f"**类型**: {strategy_info['type']}")
                
                with col2:
                    # 绩效指标
                    st.markdown("**近期绩效**:")
                    perf = strategy_info.get('performance', {})
                    st.metric("信号数量", perf.get('signal_count', 0))
                    # TODO: 添加更多绩效指标
                
                with col3:
                    # 启停控制
                    current_enabled = strategy_info['enabled']
                    enabled = st.toggle(
                        "启用",
                        value=current_enabled,
                        key=f"toggle_{strategy_name}"
                    )
                    
                    if enabled != current_enabled:
                        self._toggle_strategy(strategy_name, enabled)
                
                # 参数显示
                st.markdown("**当前参数**:")
                params = strategy_info.get('parameters', {})
                param_cols = st.columns(len(params) if params else 1)
                
                for i, (param_name, param_value) in enumerate(params.items()):
                    with param_cols[i]:
                        st.text(f"{param_name}: {param_value}")
                
                # 操作按钮
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
                
                with btn_col1:
                    if st.button("📊 查看信号", key=f"signals_{strategy_name}"):
                        # TODO: 跳转到信号标签
                        st.info(f"查看 {strategy_name} 的信号")
                
                with btn_col2:
                    if st.button("🔧 调整参数", key=f"adjust_{strategy_name}"):
                        # TODO: 跳转到参数调整标签
                        st.info(f"调整 {strategy_name} 的参数")
    
    def _render_strategy_signals(self):
        """
        渲染策略信号标签
        
        功能：
        - 显示最近生成的策略信号
        - 信号置信度分析
        - 信号执行状态追踪
        """
        st.subheader("🎯 策略信号")
        
        # 筛选条件
        col_filter1, col_filter2, col_filter3 = st.columns(3)
        
        with col_filter1:
            strategy_filter = st.selectbox(
                "选择策略",
                options=["全部"] + list(self._get_strategy_list().keys())
            )
        
        with col_filter2:
            time_range = st.selectbox(
                "时间范围",
                options=["今天", "最近3天", "最近7天", "最近30天"],
                index=1
            )
        
        with col_filter3:
            signal_type = st.selectbox(
                "信号类型",
                options=["全部", "BUY", "SELL"]
            )
        
        # 获取信号数据
        signals = self._get_strategy_signals(strategy_filter, time_range, signal_type)
        
        if not signals:
            st.info("💡 该条件下暂无信号记录")
            return
        
        # 信号统计
        st.markdown("#### 信号统计")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("总信号数", len(signals))
        
        with stat_col2:
            buy_count = len([s for s in signals if s['signal_type'] == 'BUY'])
            st.metric("买入信号", buy_count)
        
        with stat_col3:
            sell_count = len([s for s in signals if s['signal_type'] == 'SELL'])
            st.metric("卖出信号", sell_count)
        
        with stat_col4:
            avg_confidence = sum(s.get('confidence', 0) for s in signals) / len(signals) if signals else 0
            st.metric("平均置信度", f"{avg_confidence:.2f}")
        
        # 信号列表
        st.markdown("#### 信号详情")
        df = pd.DataFrame(signals)
        
        if not df.empty:
            # 添加颜色标记
            def color_signal(val):
                return 'background-color: lightgreen' if val == 'BUY' else 'background-color: lightcoral'
            
            st.dataframe(
                df.style.applymap(color_signal, subset=['signal_type']),
                use_container_width=True,
                height=400
            )
            
            # 信号分析图表（预留）
            with st.expander("📊 信号分析图表", expanded=False):
                st.info("🚧 信号分析图表功能开发中...")
                # TODO: 添加信号分布图、置信度分布等
    
    def _render_parameter_adjustment(self):
        """
        渲染参数调整标签
        
        功能：
        - 动态生成参数调整表单
        - 参数范围验证
        - 参数修改历史记录
        - 一键回测功能
        """
        st.subheader("🔧 策略参数调整")
        
        # 选择要调整的策略
        strategies = self._get_strategy_list()
        strategy_names = list(strategies.keys())
        
        if not strategy_names:
            st.warning("⚠️ 未找到可用策略")
            return
        
        selected_strategy = st.selectbox(
            "选择策略",
            options=strategy_names,
            index=0
        )
        
        strategy_info = strategies[selected_strategy]
        current_params = strategy_info.get('parameters', {})
        
        st.markdown(f"### {selected_strategy} 参数调整")
        st.markdown(f"**描述**: {strategy_info['description']}")
        
        # 动态生成参数表单
        st.markdown("#### 调整参数")
        
        new_params = {}
        param_changed = False
        
        # MA交叉策略参数
        if 'short_window' in current_params:
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                new_short = st.number_input(
                    "短周期（Short Window）",
                    min_value=2,
                    max_value=50,
                    value=current_params.get('short_window', 5),
                    help="短期移动平均线的周期"
                )
                new_params['short_window'] = new_short
                if new_short != current_params.get('short_window'):
                    param_changed = True
            
            with col_p2:
                new_long = st.number_input(
                    "长周期（Long Window）",
                    min_value=10,
                    max_value=200,
                    value=current_params.get('long_window', 20),
                    help="长期移动平均线的周期"
                )
                new_params['long_window'] = new_long
                if new_long != current_params.get('long_window'):
                    param_changed = True
            
            # 参数验证
            if new_short >= new_long:
                st.error("❌ 短周期必须小于长周期")
                param_changed = False
        
        # 止损参数（通用）
        st.markdown("#### 止损配置")
        col_sl1, col_sl2 = st.columns(2)
        
        with col_sl1:
            stop_loss_type = st.selectbox(
                "止损类型",
                options=["fixed_percent", "key_level", "atr_based", "trailing"],
                index=0,
                help="选择止损计算方式"
            )
            new_params['stop_loss_type'] = stop_loss_type
        
        with col_sl2:
            if stop_loss_type == "fixed_percent":
                stop_loss_percent = st.slider(
                    "止损比例（%）",
                    min_value=1.0,
                    max_value=10.0,
                    value=3.0,
                    step=0.1,
                    help="固定百分比止损"
                )
                new_params['stop_loss_percent'] = stop_loss_percent / 100
            elif stop_loss_type == "atr_based":
                atr_multiplier = st.slider(
                    "ATR倍数",
                    min_value=1.0,
                    max_value=5.0,
                    value=2.0,
                    step=0.1,
                    help="ATR止损倍数"
                )
                new_params['atr_multiplier'] = atr_multiplier
        
        # 保存按钮
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
        
        with col_save1:
            if st.button("💾 保存参数", type="primary", disabled=not param_changed):
                if self._save_strategy_params(selected_strategy, new_params):
                    st.success("✅ 参数已保存")
                    st.rerun()
                else:
                    st.error("❌ 保存失败")
        
        with col_save2:
            if st.button("↩️ 重置参数"):
                # TODO: 重置为默认参数
                st.info("重置为默认参数")
        
        with col_save3:
            if st.button("🔄 快速回测", help="使用新参数进行快速回测"):
                # TODO: 触发回测
                st.info("🚧 回测功能开发中...")
        
        # 参数修改历史（预留）
        with st.expander("📜 参数修改历史", expanded=False):
            st.info("🚧 参数修改历史功能开发中...")
            # TODO: 显示参数修改历史
    
    # ==================== 数据获取方法 ====================
    
    def _get_strategy_list(self) -> Dict[str, Dict[str, Any]]:
        """
        获取策略列表
        
        Returns:
            dict: 策略信息字典
        """
        try:
            strategies = {}
            
            # 从配置文件读取
            enabled_strategies = self.strategy_config.get('enabled_strategies', [])
            
            # MA交叉策略
            if 'ma_cross' in enabled_strategies:
                ma_config = self.strategy_config.get('ma_cross', {})
                strategies['MA交叉策略'] = {
                    'name': 'ma_cross',
                    'description': '基于短期和长期移动平均线交叉的趋势跟踪策略',
                    'type': '趋势跟踪',
                    'enabled': True,
                    'status': '运行中',
                    'parameters': {
                        'short_window': ma_config.get('short_window', 5),
                        'long_window': ma_config.get('long_window', 20)
                    },
                    'performance': self._get_strategy_performance('ma_cross')
                }
            
            # TODO: 添加更多策略
            
            return strategies
            
        except Exception as e:
            logger.error(f"获取策略列表失败: {e}")
            return {}
    
    def _get_strategy_signals(
        self, 
        strategy_filter: str, 
        time_range: str, 
        signal_type: str
    ) -> List[Dict[str, Any]]:
        """
        获取策略信号
        
        Args:
            strategy_filter: 策略筛选
            time_range: 时间范围
            signal_type: 信号类型
        
        Returns:
            list: 信号列表
        """
        try:
            # 计算时间范围
            days_map = {"今天": 1, "最近3天": 3, "最近7天": 7, "最近30天": 30}
            days = days_map.get(time_range, 7)
            start_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 构建查询
            query = """
                SELECT 
                    strategy_name,
                    symbol,
                    signal_type,
                    price,
                    confidence,
                    datetime(timestamp, 'unixepoch') as time,
                    reason
                FROM strategy_signals
                WHERE timestamp >= ?
            """
            params = [start_timestamp]
            
            if strategy_filter != "全部":
                query += " AND strategy_name = ?"
                # TODO: 映射显示名称到内部名称
                params.append('ma_cross')
            
            if signal_type != "全部":
                query += " AND signal_type = ?"
                params.append(signal_type)
            
            query += " ORDER BY timestamp DESC LIMIT 100"
            
            cursor.execute(query, params)
            signals = [dict(row) for row in cursor.fetchall()]
            
            return signals
            
        except Exception as e:
            logger.error(f"获取策略信号失败: {e}")
            return []
    
    def _get_strategy_performance(self, strategy_name: str) -> Dict[str, Any]:
        """
        获取策略绩效数据
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            dict: 绩效数据
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # 统计最近7天的信号数量
            start_timestamp = int((datetime.now() - timedelta(days=7)).timestamp())
            
            cursor.execute(
                """
                SELECT COUNT(*) as count
                FROM strategy_signals
                WHERE strategy_name = ? AND timestamp >= ?
                """,
                (strategy_name, start_timestamp)
            )
            
            result = cursor.fetchone()
            signal_count = result['count'] if result else 0
            
            return {
                'signal_count': signal_count,
                # TODO: 添加更多绩效指标
            }
            
        except Exception as e:
            logger.error(f"获取策略绩效失败: {e}")
            return {'signal_count': 0}
    
    # ==================== 操作方法 ====================
    
    def _toggle_strategy(self, strategy_name: str, enabled: bool):
        """
        切换策略启停状态
        
        Args:
            strategy_name: 策略名称
            enabled: 是否启用
        """
        try:
            # TODO: 实现策略启停逻辑
            # 1. 更新配置文件
            # 2. 通知调度器
            # 3. 记录操作日志
            
            status = "启用" if enabled else "禁用"
            st.success(f"✅ 已{status}策略: {strategy_name}")
            logger.info(f"策略状态变更: {strategy_name} -> {status}")
            
        except Exception as e:
            logger.error(f"切换策略状态失败: {e}")
            st.error(f"❌ 操作失败: {e}")
    
    def _save_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """
        保存策略参数
        
        Args:
            strategy_name: 策略名称
            params: 新参数
        
        Returns:
            bool: 是否成功
        """
        try:
            # 读取当前配置
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 更新参数
            # TODO: 映射显示名称到配置名称
            config_key = 'ma_cross'  # 示例
            
            if config_key in config:
                config[config_key].update(params)
                
                # 保存配置
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True)
                
                logger.info(f"策略参数已更新: {strategy_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"保存策略参数失败: {e}")
            return False
    
    # ==================== 预留的扩展方法 ====================
    
    def _run_quick_backtest(self, strategy_name: str, params: Dict[str, Any]):
        """
        运行快速回测（待实现）
        
        Args:
            strategy_name: 策略名称
            params: 策略参数
        """
        # TODO: 实现快速回测功能
        pass
    
    def _get_parameter_history(self, strategy_name: str) -> List[Dict[str, Any]]:
        """
        获取参数修改历史（待实现）
        
        Args:
            strategy_name: 策略名称
        
        Returns:
            list: 参数修改历史
        """
        # TODO: 实现参数历史记录
        pass


# 页面入口函数
def show():
    """显示策略控制页面"""
    page = StrategyControlPage()
    page.render()
