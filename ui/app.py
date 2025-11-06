"""
QuantAITrade Web界面主程序
基于Streamlit的可视化管理平台
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入页面模块
from ui.pages import dashboard, strategy_control, ai_analysis


# ==================== 页面配置 ====================

st.set_page_config(
    page_title="QuantAITrade - 智能量化交易系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "QuantAITrade v1.0.0 - 智能量化交易系统"
    }
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 侧边栏 ====================

st.sidebar.title("📊 QuantAITrade")
st.sidebar.markdown("---")

# 页面导航
page = st.sidebar.radio(
    "📍 导航",
    options=[
        "📊 仪表盘",
        "⚙️ 策略控制",
        "🤖 AI分析",
        "📈 回测中心",
        "⚙️ 系统设置"
    ],
    index=0
)

st.sidebar.markdown("---")

# 系统状态指示器
st.sidebar.markdown("### 🔌 系统状态")

# TODO: 实时获取系统状态
system_status = {
    'database': True,
    'exchange': True,
    'scheduler': True,
    'ai': True
}

status_emoji = {True: "🟢", False: "🔴"}

st.sidebar.text(f"{status_emoji[system_status['database']]} 数据库")
st.sidebar.text(f"{status_emoji[system_status['exchange']]} 交易所连接")
st.sidebar.text(f"{status_emoji[system_status['scheduler']]} 任务调度器")
st.sidebar.text(f"{status_emoji[system_status['ai']]} AI服务")

st.sidebar.markdown("---")

# 快捷操作
st.sidebar.markdown("### ⚡ 快捷操作")

col_quick1, col_quick2 = st.sidebar.columns(2)

with col_quick1:
    if st.button("🔄 刷新", use_container_width=True):
        st.rerun()

with col_quick2:
    if st.button("📤 导出", use_container_width=True):
        st.info("导出功能开发中...")

st.sidebar.markdown("---")

# 版本信息
st.sidebar.caption("QuantAITrade v1.0.0")
st.sidebar.caption("© 2025 QuantAI Team")


# ==================== 主内容区域 ====================

if page == "📊 仪表盘":
    dashboard.show()

elif page == "⚙️ 策略控制":
    strategy_control.show()

elif page == "🤖 AI分析":
    ai_analysis.show()

elif page == "📈 回测中心":
    st.title("📈 回测中心")
    st.info("🚧 回测中心功能开发中...")
    
    # 预留回测功能框架
    st.markdown("""
    ### 计划功能
    - 📊 策略回测配置
    - 📈 回测结果可视化
    - 📉 绩效指标分析
    - 🔄 参数优化扫描
    - 💾 回测结果保存
    """)

elif page == "⚙️ 系统设置":
    st.title("⚙️ 系统设置")
    st.info("🚧 系统设置功能开发中...")
    
    # 预留设置功能框架
    tab1, tab2, tab3, tab4 = st.tabs(["基本设置", "风控配置", "AI配置", "告警设置"])
    
    with tab1:
        st.markdown("### 基本设置")
        st.selectbox("运行模式", options=["manual", "auto", "hybrid"], index=2)
        st.multiselect("交易对", options=["BTCUSDT", "ETHUSDT", "SOLUSDT"], default=["BTCUSDT"])
    
    with tab2:
        st.markdown("### 风控配置")
        st.slider("单仓位上限(%)", 1, 10, 3)
        st.slider("总仓位上限(%)", 50, 100, 80)
    
    with tab3:
        st.markdown("### AI配置")
        st.selectbox("AI模型", options=["gpt-4", "gpt-3.5-turbo"])
        st.time_input("每日分析时间", value=None)
    
    with tab4:
        st.markdown("### 告警设置")
        st.checkbox("启用邮件告警")
        st.checkbox("启用微信告警")


# ==================== 页脚 ====================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8rem;'>
        QuantAITrade - 智能量化交易系统 | 
        <a href='https://github.com' target='_blank'>GitHub</a> | 
        <a href='#' target='_blank'>文档</a> | 
        <a href='#' target='_blank'>帮助</a>
    </div>
    """,
    unsafe_allow_html=True
)
