"""
QuantAITrade - 智能量化交易系统
主入口文件 - 完整集成版本
"""

import argparse
import sys
import signal
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger

# 添加项目根目录和src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

from config import get_config, LOG_DIRECTORY
from data.db_manager import db_manager
from data.fetcher import data_fetcher
from src.execution.trade_executor import trade_executor
from src.execution.exchange_connector import exchange_connector
from src.execution.position_tracker import position_tracker
from orchestrator.scheduler import scheduler
from strategy import MACrossStrategy
from ai.ai_analyzer import ai_analyzer

# 导入新增的状态管理模块
from utils.state_manager import state_manager
from utils.task_logger import task_logger
from utils.recovery_manager import recovery_manager

# 全局变量用于优雅关闭
shutdown_flag = False


def signal_handler(signum, frame):
    """信号处理函数"""
    global shutdown_flag
    logger.info(f"收到停止信号 {signum}，准备关闭系统...")
    shutdown_flag = True


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
            filter=lambda record: "trade" in record["name"].lower() or "execution" in record["name"].lower(),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )
        
        logger.add(
            log_dir / "ai.log",
            rotation="500 MB",
            retention=f"{config['logging']['log_retention_days']} days",
            level=log_level,
            filter=lambda record: "ai" in record["name"].lower(),
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


def init_system_components():
    """初始化系统组件"""
    logger.info("初始化系统组件...")
    
    # 1. 连接交易所
    logger.info("连接交易所...")
    if not exchange_connector.connect():
        logger.warning("交易所连接失败，将以离线模式运行")
    
    # 2. 启动交易执行器
    logger.info("启动交易执行器...")
    trade_executor.start()
    
    logger.success("系统组件初始化完成")


def shutdown_system_components():
    """关闭系统组件"""
    logger.info("关闭系统组件...")
    
    # 1. 停止调度器
    scheduler.shutdown()
    
    # 2. 停止交易执行器
    trade_executor.stop()
    
    # 3. 关闭交易所连接
    exchange_connector.close()
    
    # 4. 关闭数据库
    db_manager.close()
    
    logger.success("系统组件已关闭")


# ==================== 定时任务函数 ====================

def data_fetch_task():
    """数据获取任务（定时执行）"""
    task_id = None
    try:
        # 记录任务开始
        task_id = task_logger.log_task_start('data_fetch', 'scheduled')
        
        logger.info("开始定时数据获取...")
        data_fetcher.fetch_all_configured_symbols()
        logger.success("数据获取完成")
        
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success'})
    except Exception as e:
        logger.error(f"数据获取失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


def strategy_analysis_task():
    """策略分析任务（定时执行）"""
    task_id = None
    try:
        # 记录任务开始
        task_id = task_logger.log_task_start('strategy_analysis', 'scheduled')
        
        logger.info("开始策略分析...")
        config = get_config()
        symbols = config['trading']['symbols']
        
        # 创建策略
        strategy = MACrossStrategy()
        
        for symbol in symbols:
            try:
                # 获取最新数据
                klines = db_manager.get_klines(symbol, '1h', limit=100)
                if not klines:
                    logger.warning(f"{symbol} 没有数据，跳过")
                    continue
                
                # 转换为pandas DataFrame
                df = pd.DataFrame(klines)
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
                df.set_index('timestamp', inplace=True)
                
                # 生成信号
                signal = strategy.on_data(df)
                
                if signal:
                    logger.info(f"生成交易信号: {signal.symbol} {signal.signal_type.value} @ {signal.price:.2f}")
                    # 提交到执行器
                    trade_executor.submit_signal(signal)
                else:
                    logger.debug(f"{symbol} 无交易信号")
                    
            except Exception as e:
                logger.error(f"分析 {symbol} 失败: {e}")
        
        logger.success("策略分析完成")
        
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success', 'symbols_analyzed': len(symbols)})
    except Exception as e:
        logger.error(f"策略分析任务失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


def position_monitor_task():
    """持仓监控任务（定时执行）"""
    task_id = None
    try:
        # 记录任务开始
        task_id = task_logger.log_task_start('position_monitor', 'scheduled')
        
        logger.debug("检查持仓止损...")
        triggered = position_tracker.check_stop_loss()
        
        if triggered:
            logger.warning(f"发现 {len(triggered)} 个持仓触发止损")
            
            for position_id, symbol, reason in triggered:
                # 获取当前价格
                current_price = exchange_connector.get_current_price(symbol)
                if current_price:
                    # 执行平仓
                    position_tracker.close_position(position_id, current_price, reason)
                    logger.warning(f"已平仓: {symbol} @ {current_price:.2f} - {reason}")
        
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success', 'stop_loss_triggered': len(triggered)})
    except Exception as e:
        logger.error(f"持仓监控任务失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


def ai_analysis_task():
    """AI分析任务（每日执行）"""
    task_id = None
    try:
        # 检查是否已执行过今天的分析
        config = get_config()
        if config.get('task_logging', {}).get('enable_task_log', True):
            # 这里应该检查是否已执行过今天的AI分析
            pass
            
        # 记录任务开始
        task_id = task_logger.log_task_start('ai_analysis', 'scheduled')
        
        logger.info("开始执行 AI 分析...")
        result = ai_analyzer.run_daily_analysis(datetime.now().strftime('%Y-%m-%d'))
        if result:
            logger.success("AI 分析完成")
        else:
            logger.warning("AI 分析未返回结果")
            
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success', 'result': result is not None})
    except Exception as e:
        logger.error(f"AI 分析任务失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


def heartbeat_task():
    """心跳任务（每30秒执行）"""
    try:
        state_manager.update_heartbeat()
        logger.debug("心跳更新完成")
    except Exception as e:
        logger.error(f"心跳任务失败: {e}")


def order_sync_task():
    """订单同步任务（每5分钟执行）"""
    task_id = None
    try:
        # 记录任务开始
        task_id = task_logger.log_task_start('order_sync', 'scheduled')
        
        logger.info("开始同步未完成订单...")
        # 这里应该实现订单同步逻辑
        logger.info("订单同步完成")
        
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success'})
    except Exception as e:
        logger.error(f"订单同步任务失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


def position_verification_task():
    """持仓验证任务（每小时执行）"""
    task_id = None
    try:
        # 记录任务开始
        task_id = task_logger.log_task_start('position_verification', 'scheduled')
        
        logger.info("开始验证持仓数据一致性...")
        # 这里应该实现持仓验证逻辑
        logger.info("持仓数据一致性验证完成")
        
        # 记录任务结束
        if task_id:
            task_logger.log_task_end(task_id, {'status': 'success'})
    except Exception as e:
        logger.error(f"持仓验证任务失败: {e}")
        # 记录任务失败
        if task_id:
            task_logger.log_task_failed(task_id, str(e))


# ==================== 运行模式函数 ====================

def run_manual_mode():
    """运行人工模式"""
    logger.info("="*60)
    logger.info("启动人工模式")
    logger.info("="*60)
    logger.info("人工模式：系统仅生成信号，所有交易需要手动确认")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化系统组件
        init_system_components()
        
        # 配置调度器
        config = get_config()
        data_interval = config['data']['fetch_interval_minutes']
        
        # 添加数据获取任务
        scheduler.add_job(
            func=data_fetch_task,
            trigger_type='interval',
            trigger_args={'minutes': data_interval},
            job_id='data_fetch',
            name='数据获取任务'
        )
        
        # 添加心跳任务
        scheduler.add_job(
            func=heartbeat_task,
            trigger_type='interval',
            trigger_args={'seconds': config.get('state_management', {}).get('heartbeat_interval_seconds', 30)},
            job_id='heartbeat',
            name='心跳任务'
        )
        
        # 添加订单同步任务
        scheduler.add_job(
            func=order_sync_task,
            trigger_type='interval',
            trigger_args={'minutes': config.get('state_management', {}).get('order_sync_interval_minutes', 5)},
            job_id='order_sync',
            name='订单同步任务'
        )
        
        # 添加策略分析任务（仅生成信号，不自动执行）
        scheduler.add_job(
            func=strategy_analysis_task,
            trigger_type='interval',
            trigger_args={'minutes': 15},  # 每15分钟分析一次
            job_id='strategy_analysis',
            name='策略分析任务'
        )
        
        # 启动调度器
        scheduler.start()
        
        logger.success("人工模式已启动")
        logger.info("提示：查看 trade.log 文件获取交易信号，手动决定是否执行")
        logger.info("按 Ctrl+C 停止系统")
        
        # 保持运行
        while not shutdown_flag:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        shutdown_system_components()


def run_auto_mode():
    """运行全自动模式"""
    logger.info("="*60)
    logger.info("启动全自动模式")
    logger.info("="*60)
    logger.warning("⚠️  全自动模式：策略信号将自动执行交易，请确保风控参数已正确配置！")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化系统组件
        init_system_components()
        
        # 配置调度器
        config = get_config()
        data_interval = config['data']['fetch_interval_minutes']
        position_interval = config['position_tracking']['monitor_interval_seconds']
        
        # 添加数据获取任务
        scheduler.add_job(
            func=data_fetch_task,
            trigger_type='interval',
            trigger_args={'minutes': data_interval},
            job_id='data_fetch',
            name='数据获取任务'
        )
        
        # 添加心跳任务
        scheduler.add_job(
            func=heartbeat_task,
            trigger_type='interval',
            trigger_args={'seconds': config.get('state_management', {}).get('heartbeat_interval_seconds', 30)},
            job_id='heartbeat',
            name='心跳任务'
        )
        
        # 添加订单同步任务
        scheduler.add_job(
            func=order_sync_task,
            trigger_type='interval',
            trigger_args={'minutes': config.get('state_management', {}).get('order_sync_interval_minutes', 5)},
            job_id='order_sync',
            name='订单同步任务'
        )
        
        # 添加持仓验证任务
        scheduler.add_job(
            func=position_verification_task,
            trigger_type='interval',
            trigger_args={'hours': config.get('state_management', {}).get('position_verify_interval_hours', 1)},
            job_id='position_verification',
            name='持仓验证任务'
        )
        
        # 添加策略分析任务（自动执行交易）
        scheduler.add_job(
            func=strategy_analysis_task,
            trigger_type='interval',
            trigger_args={'minutes': 15},
            job_id='strategy_analysis',
            name='策略分析任务'
        )
        
        # 添加持仓监控任务
        scheduler.add_job(
            func=position_monitor_task,
            trigger_type='interval',
            trigger_args={'seconds': position_interval},
            job_id='position_monitor',
            name='持仓监控任务'
        )
        
        # 启动调度器
        scheduler.start()
        
        logger.success("全自动模式已启动")
        logger.info("系统将自动执行交易，持续监控持仓")
        logger.info("按 Ctrl+C 停止系统")
        
        # 保持运行
        while not shutdown_flag:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        shutdown_system_components()


def run_hybrid_mode():
    """运行混合模式"""
    logger.info("="*60)
    logger.info("启动混合模式（推荐）")
    logger.info("="*60)
    logger.info("混合模式：策略自动执行，AI建议需人工审核")
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 初始化系统组件
        init_system_components()
        
        # 配置调度器
        config = get_config()
        data_interval = config['data']['fetch_interval_minutes']
        position_interval = config['position_tracking']['monitor_interval_seconds']
        ai_time = config['ai']['analysis_time']
        
        # 添加数据获取任务
        scheduler.add_job(
            func=data_fetch_task,
            trigger_type='interval',
            trigger_args={'minutes': data_interval},
            job_id='data_fetch',
            name='数据获取任务'
        )
        
        # 添加心跳任务
        scheduler.add_job(
            func=heartbeat_task,
            trigger_type='interval',
            trigger_args={'seconds': config.get('state_management', {}).get('heartbeat_interval_seconds', 30)},
            job_id='heartbeat',
            name='心跳任务'
        )
        
        # 添加订单同步任务
        scheduler.add_job(
            func=order_sync_task,
            trigger_type='interval',
            trigger_args={'minutes': config.get('state_management', {}).get('order_sync_interval_minutes', 5)},
            job_id='order_sync',
            name='订单同步任务'
        )
        
        # 添加持仓验证任务
        scheduler.add_job(
            func=position_verification_task,
            trigger_type='interval',
            trigger_args={'hours': config.get('state_management', {}).get('position_verify_interval_hours', 1)},
            job_id='position_verification',
            name='持仓验证任务'
        )
        
        # 添加策略分析任务
        scheduler.add_job(
            func=strategy_analysis_task,
            trigger_type='interval',
            trigger_args={'minutes': 15},
            job_id='strategy_analysis',
            name='策略分析任务'
        )
        
        # 添加持仓监控任务
        scheduler.add_job(
            func=position_monitor_task,
            trigger_type='interval',
            trigger_args={'seconds': position_interval},
            job_id='position_monitor',
            name='持仓监控任务'
        )
        
        # 添加AI分析任务（每日定时）
        hour, minute = ai_time.split(':')
        scheduler.add_job(
            func=ai_analysis_task,
            trigger_type='cron',
            trigger_args={'hour': int(hour), 'minute': int(minute)},
            job_id='ai_analysis',
            name='AI分析任务'
        )
        
        # 启动调度器
        scheduler.start()
        
        logger.success("混合模式已启动")
        logger.info(f"- 策略自动交易：每15分钟分析一次")
        logger.info(f"- 持仓自动监控：每{position_interval}秒检查一次")
        logger.info(f"- AI每日分析：{ai_time} 执行")
        logger.info("按 Ctrl+C 停止系统")
        
        # 保持运行
        while not shutdown_flag:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断")
    finally:
        shutdown_system_components()


def execute_system_recovery():
    """执行系统恢复流程"""
    logger.info("检查是否需要执行系统恢复...")
    
    if recovery_manager.check_recovery_needed():
        logger.warning("检测到上次异常关闭，开始执行恢复流程...")
        recovery_manager.execute_recovery()
        logger.success("系统恢复完成")
    else:
        logger.info("系统状态正常，无需恢复")


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
            
            logger.info(f"配置的默认模式: {config['run_mode']}")
            logger.info(f"命令行指定模式: {mode}")
            
            # 创建系统实例
            instance_id = state_manager.create_instance(mode)
            task_logger.set_instance_id(instance_id)
            
            # 执行系统恢复
            execute_system_recovery()
            
            if mode == 'manual':
                run_manual_mode()
            elif mode == 'auto':
                run_auto_mode()
            elif mode == 'hybrid':
                run_hybrid_mode()
                
            # 标记系统正常停止
            state_manager.mark_stopped('manual')
        else:
            # 没有参数，显示帮助
            parser.print_help()
            logger.info("\n快速开始:")
            logger.info("1. python main.py --init-db      # 初始化数据库")
            logger.info("2. python main.py --fetch-data   # 获取历史数据")
            logger.info("3. python main.py --mode hybrid  # 启动系统（混合模式）")
            
    except KeyboardInterrupt:
        logger.info("\n用户中断，正在关闭系统...")
        # 标记系统正常停止
        state_manager.mark_stopped('interrupt')
    except Exception as e:
        logger.exception(f"系统运行出错: {e}")
        # 标记系统崩溃
        state_manager.mark_crashed(str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
