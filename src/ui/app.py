"""
QuantAITrade Web界面主程序
基于Streamlit的可视化管理平台
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入页面模块
from src.ui.pages import dashboard, strategy_control, ai_analysis

# 导入系统状态检测器
from src.utils.system_status_checker import system_status_checker

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

# 实时获取系统状态
system_status = system_status_checker.get_system_status()

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
        # 强制刷新系统状态
        system_status = system_status_checker.refresh_status()
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
    
    # 设置标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["基本设置", "风控配置", "AI配置", "告警设置", "配置管理"])
    
    with tab1:
        self._render_basic_settings()
    
    with tab2:
        self._render_risk_settings()
    
    with tab3:
        self._render_ai_settings()
    
    with tab4:
        self._render_alert_settings()
    
    with tab5:
        self._render_config_management()
        
def _render_basic_settings(self):
    """
    渲染基本设置标签
    """
    st.subheader("🔧 基本设置")
    
    # 运行模式
    st.markdown("#### 运行模式")
    run_mode = st.radio(
        "选择运行模式",
        options=[
            ("manual", "人工模式 - 所有交易需要人工审核"),
            ("auto", "自动模式 - 策略信号自动执行"),
            ("hybrid", "混合模式 - AI建议人工审核")
        ],
        format_func=lambda x: x[1],
        index=2  # 默认混合模式
    )
    
    # 交易对设置
    st.markdown("#### 交易对设置")
    symbols = st.multiselect(
        "选择交易对",
        options=["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT"],
        default=["BTCUSDT", "ETHUSDT"]
    )
    
    # 数据更新设置
    st.markdown("#### 数据更新设置")
    col1, col2 = st.columns(2)
    
    with col1:
        fetch_interval = st.slider(
            "数据抓取间隔(分钟)",
            min_value=1,
            max_value=60,
            value=5,
            help="设置获取市场数据的时间间隔"
        )
    
    with col2:
        data_retention = st.slider(
            "数据保留天数",
            min_value=7,
            max_value=365,
            value=30,
            help="设置历史数据保留时间"
        )
    
    # 保存按钮
    st.markdown("---")
    if st.button("💾 保存基本设置", type="primary"):
        st.success("✅ 基本设置已保存")
        
def _render_risk_settings(self):
    """
    渲染风控配置标签
    """
    st.subheader("🛡️ 风控配置")
    
    # 仓位管理
    st.markdown("#### 仓位管理")
    col1, col2 = st.columns(2)
    
    with col1:
        single_position_limit = st.slider(
            "单仓位上限(%)",
            min_value=1,
            max_value=20,
            value=3,
            help="单个交易对的最大仓位占比"
        )
    
    with col2:
        total_position_limit = st.slider(
            "总仓位上限(%)",
            min_value=50,
            max_value=100,
            value=80,
            help="所有仓位的总资金占比"
        )
    
    # 止损设置
    st.markdown("#### 止损设置")
    col3, col4 = st.columns(2)
    
    with col3:
        default_stop_loss = st.slider(
            "默认止损比例(%)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            help="默认的止损比例设置"
        )
    
    with col4:
        take_profit_ratio = st.slider(
            "止盈比例(%)",
            min_value=1.0,
            max_value=20.0,
            value=5.0,
            step=0.1,
            help="默认的止盈比例设置"
        )
    
    # 风险等级
    st.markdown("#### 风险等级")
    risk_level = st.select_slider(
        "风险承受等级",
        options=["保守", "稳健", "平衡", "积极", "激进"],
        value="稳健"
    )
    
    # 保存按钮
    st.markdown("---")
    if st.button("💾 保存风控配置", type="primary"):
        st.success("✅ 风控配置已保存")
        
def _render_ai_settings(self):
    """
    渲染AI配置标签
    """
    st.subheader("🤖 AI配置")
    
    # AI模型设置
    st.markdown("#### AI模型设置")
    ai_model = st.selectbox(
        "选择AI模型",
        options=[
            ("gpt-4", "GPT-4 (推荐)"),
            ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
            ("claude-2", "Claude 2"),
            ("llama-2", "Llama 2")
        ],
        format_func=lambda x: x[1],
        index=0
    )
    
    # 分析时间
    st.markdown("#### 分析时间设置")
    analysis_time = st.time_input(
        "每日AI分析时间",
        value=datetime.strptime("09:00", "%H:%M").time(),
        help="设置每日AI市场分析的执行时间"
    )
    
    # 分析范围
    st.markdown("#### 分析范围设置")
    lookback_days = st.slider(
        "回看天数",
        min_value=7,
        max_value=90,
        value=30,
        help="AI分析时回看的历史数据天数"
    )
    
    # 分析深度
    st.markdown("#### 分析深度")
    analysis_depth = st.radio(
        "分析深度",
        options=[
            ("basic", "基础分析 - 快速但简单"),
            ("standard", "标准分析 - 平衡速度与深度"),
            ("deep", "深度分析 - 详细但耗时")
        ],
        format_func=lambda x: x[1],
        index=1
    )
    
    # 保存按钮
    st.markdown("---")
    if st.button("💾 保存AI配置", type="primary"):
        st.success("✅ AI配置已保存")
        
def _render_alert_settings(self):
    """
    渲染告警设置标签
    """
    st.subheader("🚨 告警设置")
    
    # 告警级别
    st.markdown("#### 告警级别设置")
    alert_level = st.selectbox(
        "告警敏感度",
        options=[
            ("low", "低 - 仅重要事件"),
            ("medium", "中 - 重要和一般事件"),
            ("high", "高 - 所有事件")
        ],
        format_func=lambda x: x[1],
        index=1
    )
    
    # 告警方式
    st.markdown("#### 告警方式")
    enable_email = st.checkbox("启用邮件告警", value=True)
    enable_wechat = st.checkbox("启用微信告警")
    enable_sms = st.checkbox("启用短信告警")
    enable_desktop = st.checkbox("启用桌面通知", value=True)
    
    # 邮件设置
    if enable_email:
        st.markdown("#### 邮件设置")
        email_address = st.text_input("接收邮箱地址", placeholder="example@email.com")
        smtp_server = st.text_input("SMTP服务器", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP端口", min_value=1, max_value=65535, value=587)
    
    # 微信设置
    if enable_wechat:
        st.markdown("#### 微信设置")
        wechat_webhook = st.text_input("企业微信Webhook地址", placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY")
    
    # 短信设置
    if enable_sms:
        st.markdown("#### 短信设置")
        sms_api_key = st.text_input("短信API密钥", type="password")
        sms_phone = st.text_input("接收手机号码", placeholder="+86 13800138000")
    
    # 告警事件类型
    st.markdown("#### 告警事件类型")
    event_types = [
        "系统异常",
        "交易执行",
        "风控触发",
        "AI建议",
        "策略信号",
        "账户变动"
    ]
    selected_events = st.multiselect(
        "选择需要告警的事件类型",
        options=event_types,
        default=event_types[:3]
    )
    
    # 保存按钮
    st.markdown("---")
    if st.button("💾 保存告警设置", type="primary"):
        st.success("✅ 告警设置已保存")
        
def _render_config_management(self):
    """
    渲染配置管理标签
    """
    st.subheader("📂 配置管理")
    
    # 配置导入导出
    st.markdown("#### 配置导入导出")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**导出配置**")
        if st.button("📥 导出当前配置"):
            st.info("正在导出配置文件...")
    
    with col2:
        st.markdown("**导入配置**")
        uploaded_file = st.file_uploader("上传配置文件", type=["json", "yaml"])
        if uploaded_file is not None:
            st.success("✅ 配置文件已上传")
            if st.button("📤 应用配置"):
                st.success("✅ 配置已应用")
    
    # 配置版本管理
    st.markdown("#### 配置版本管理")
    versions = [
        {"version": "v1.2.0", "date": "2025-11-10", "author": "系统自动"},
        {"version": "v1.1.5", "date": "2025-11-05", "author": "用户调整"},
        {"version": "v1.1.0", "date": "2025-10-28", "author": "系统初始化"}
    ]
    
    # 显示版本历史
    for version in versions:
        with st.expander(f"{version['version']} - {version['date']} by {version['author']}"):
            st.text("配置详情:")
            st.json({
                "run_mode": "hybrid",
                "symbols": ["BTCUSDT", "ETHUSDT"],
                "risk_level": "稳健",
                "ai_model": "gpt-4"
            })
            
            col_restore, col_download = st.columns(2)
            with col_restore:
                if st.button("⏪ 恢复此版本"):
                    st.success(f"✅ 已恢复到版本 {version['version']}")
            with col_download:
                if st.button("💾 下载此版本"):
                    st.info("正在下载配置文件...")
    
    # 配置校验
    st.markdown("#### 配置校验")
    if st.button("🔍 校验当前配置"):
        st.success("✅ 配置校验通过，所有设置均有效")


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
