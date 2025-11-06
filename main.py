"""
QuantAITrade - 智能量化交易系统
主入口文件
"""

import argparse
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import get_config, LOG_DIRECTORY
from data.db_manager import db_manager
from data.fetcher import data_fetcher


def setup_logging():
    """配置日志系统"""
    config = get_config()
    log_level = config['logging']['log_level']
    log_dir = Path(LOG_DIRECTORY)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置loguru
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    if config['logging']['log_to_console']:
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        )
    
    # 文件输出
    if config['logging']['log_to_file']:
        logger.add(
            log_dir / "system.log",
            rotation="500 MB",
            retention=f"{config['logging']['log_retention_days']} days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )
        
        logger.add(
            log_dir / "trade.log",
            rotation="500 MB",
            retention=f"{config['logging']['log_retention_days']} days",
            level=log_level,
            filter=lambda record: "trade" in record["name"].lower(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )
    
    logger.info("日志系统初始化完成")


def init_database():
    """初始化数据库"""
    logger.info("初始化数据库...")
    db_manager.init_database()
    logger.success("数据库初始化完成")


def fetch_initial_data():
    """首次获取历史数据"""
    logger.info("开始获取历史数据...")
    try:
        data_fetcher.fetch_all_configured_symbols()
        logger.success("历史数据获取完成")
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise


def run_manual_mode():
    """运行人工模式"""
    logger.info("启动人工模式")
    logger.info("人工模式下，系统仅提供数据和信号，需要手动审核交易")
    
    # TODO: 启动Web界面
    logger.warning("Web界面尚未实现，请使用 --init-db 初始化数据库后查看数据")


def run_auto_mode():
    """运行全自动模式"""
    logger.info("启动全自动模式")
    logger.warning("全自动模式下，策略信号将自动执行，请确保风控参数已正确配置！")
    
    # TODO: 启动调度器和自动执行
    logger.warning("自动模式尚未完全实现")


def run_hybrid_mode():
    """运行混合模式"""
    logger.info("启动混合模式（推荐）")
    logger.info("混合模式下，策略自动执行但AI建议需人工审核")
    
    # TODO: 启动调度器、自动执行和Web界面
    logger.warning("混合模式尚未完全实现")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='QuantAITrade - 智能量化交易系统')
    parser.add_argument('--init-db', action='store_true', help='初始化数据库')
    parser.add_argument('--fetch-data', action='store_true', help='获取历史数据')
    parser.add_argument('--mode', choices=['manual', 'auto', 'hybrid'], 
                       help='运行模式（manual/auto/hybrid）')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging()
    
    logger.info("="*60)
    logger.info("QuantAITrade - 智能量化交易系统")
    logger.info("="*60)
    
    try:
        # 初始化数据库
        if args.init_db:
            init_database()
            logger.info("数据库初始化完成，可以使用 --fetch-data 获取历史数据")
            return
        
        # 获取历史数据
        if args.fetch_data:
            fetch_initial_data()
            logger.info("数据获取完成，可以使用 --mode 参数启动系统")
            return
        
        # 启动系统
        if args.mode:
            config = get_config()
            mode = args.mode
            
            logger.info(f"配置的运行模式: {config['run_mode']}")
            logger.info(f"命令行指定模式: {mode}")
            
            if mode == 'manual':
                run_manual_mode()
            elif mode == 'auto':
                run_auto_mode()
            elif mode == 'hybrid':
                run_hybrid_mode()
        else:
            # 没有参数，显示帮助
            parser.print_help()
            logger.info("\n快速开始:")
            logger.info("1. python main.py --init-db      # 初始化数据库")
            logger.info("2. python main.py --fetch-data   # 获取历史数据")
            logger.info("3. python main.py --mode hybrid  # 启动系统（混合模式）")
            
    except KeyboardInterrupt:
        logger.info("\n用户中断，正在关闭系统...")
    except Exception as e:
        logger.exception(f"系统运行出错: {e}")
        sys.exit(1)
    finally:
        db_manager.close()
        logger.info("系统已关闭")


if __name__ == '__main__':
    main()
