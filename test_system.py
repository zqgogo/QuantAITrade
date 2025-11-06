"""
系统测试脚本
演示核心功能的使用
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from datetime import datetime, timedelta

# 配置简单的日志
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_config_loading():
    """测试配置加载"""
    logger.info("=" * 60)
    logger.info("测试1: 配置加载")
    logger.info("=" * 60)
    
    from config import get_config, get_strategy_config
    
    config = get_config()
    logger.info(f"✓ 主配置加载成功")
    logger.info(f"  - 运行模式: {config['run_mode']}")
    logger.info(f"  - 交易对: {config['trading']['symbols']}")
    
    strategy_config = get_strategy_config()
    logger.info(f"✓ 策略配置加载成功")
    logger.info(f"  - 启用策略: {strategy_config['enabled_strategies']}")
    
    return True


def test_database():
    """测试数据库"""
    logger.info("\n" + "=" * 60)
    logger.info("测试2: 数据库初始化")
    logger.info("=" * 60)
    
    from data import db_manager
    
    db_manager.init_database()
    logger.info("✓ 数据库初始化成功")
    
    return True


def test_strategy():
    """测试策略"""
    logger.info("\n" + "=" * 60)
    logger.info("测试3: 策略系统")
    logger.info("=" * 60)
    
    import pandas as pd
    from strategy import MACrossStrategy
    
    # 创建策略
    strategy = MACrossStrategy({'short_window': 5, 'long_window': 20})
    logger.info(f"✓ 策略创建成功: {strategy}")
    
    # 创建模拟数据
    dates = pd.date_range(end=datetime.now(), periods=50, freq='H')
    df = pd.DataFrame({
        'close': [100 + i + (i % 10) for i in range(50)],
        'open': [100 + i for i in range(50)],
        'high': [102 + i for i in range(50)],
        'low': [98 + i for i in range(50)],
        'volume': [1000 for _ in range(50)]
    }, index=dates)
    
    # 生成信号
    signal = strategy.on_data(df)
    if signal:
        logger.info(f"✓ 策略信号: {signal.signal_type.value} @ {signal.price:.2f}")
    else:
        logger.info("  - 当前无交易信号")
    
    return True


def test_risk_controller():
    """测试风控"""
    logger.info("\n" + "=" * 60)
    logger.info("测试4: 风控系统")
    logger.info("=" * 60)
    
    from execution import risk_controller
    from data.models import Signal, SignalType
    
    # 创建测试信号
    signal = Signal(
        strategy_name="TEST",
        symbol="BTCUSDT",
        signal_type=SignalType.BUY,
        price=45000.0,
        confidence=0.8
    )
    
    # 风控检查
    passed, reason = risk_controller.check_order_risk(signal, 10000.0, [])
    
    if passed:
        logger.info(f"✓ 风控检查通过")
    else:
        logger.info(f"✗ 风控拒绝: {reason}")
    
    # 止损计算
    stop_price, stop_type = risk_controller.calculate_stop_loss(
        entry_price=45000.0,
        stop_loss_config={'type': 'fixed_percent', 'stop_loss_percent': 0.03},
        symbol="BTCUSDT"
    )
    logger.info(f"✓ 止损计算: {stop_price:.2f} ({stop_type.value})")
    
    return True


def test_backtest():
    """测试回测（需要数据）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试5: 回测引擎")
    logger.info("=" * 60)
    
    from backtest import BacktestEngine
    from strategy import MACrossStrategy
    from data import db_manager
    
    # 检查是否有数据
    klines = db_manager.get_klines('BTCUSDT', '1h', limit=1)
    
    if not klines:
        logger.warning("⚠ 没有历史数据，跳过回测测试")
        logger.info("  提示: 先运行 'python main.py --fetch-data' 获取数据")
        return True
    
    strategy = MACrossStrategy()
    engine = BacktestEngine(strategy, initial_capital=10000.0)
    
    logger.info("✓ 回测引擎创建成功")
    logger.info("  注意: 需要足够的历史数据才能运行完整回测")
    
    return True


def main():
    """运行所有测试"""
    logger.info("\n")
    logger.info("*" * 60)
    logger.info("QuantAITrade 系统功能测试")
    logger.info("*" * 60)
    
    tests = [
        ("配置加载", test_config_loading),
        ("数据库", test_database),
        ("策略系统", test_strategy),
        ("风控系统", test_risk_controller),
        ("回测引擎", test_backtest),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            logger.error(f"✗ {name}测试失败: {e}")
            results.append((name, False))
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        logger.success("\n✓ 所有核心功能测试通过！")
        logger.info("\n下一步:")
        logger.info("1. 配置 .env 文件（复制 .env.example）")
        logger.info("2. python main.py --init-db    # 初始化数据库")
        logger.info("3. python main.py --fetch-data # 获取历史数据")
        logger.info("4. python main.py --mode hybrid # 启动系统")
    else:
        logger.warning(f"\n⚠ {total-passed}个测试失败，请检查日志")


if __name__ == '__main__':
    main()
