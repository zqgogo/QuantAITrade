#!/bin/bash
# 快速启动脚本

echo "=============================="
echo "QuantAITrade 快速启动脚本"
echo "=============================="

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -q loguru pyyaml python-dotenv ccxt

# 运行系统
echo ""
echo "=============================="
echo "系统就绪，可用命令："
echo "=============================="
echo "python main.py --init-db      # 初始化数据库"
echo "python main.py --fetch-data   # 获取历史数据"
echo "python main.py --mode hybrid  # 启动系统"
echo "streamlit run src/ui/app.py  # 启动Web UI"
echo "默认访问地址：http://localhost:8501"
echo ""
echo "按 Ctrl+D 退出虚拟环境"
echo "=============================="

# 进入交互式shell
$SHELL
