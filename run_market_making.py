"""
做市策略运行脚本

使用方法：
1. 模拟模式：python run_market_making.py --mode paper
2. 双轨模式：python run_market_making.py --mode both
3. 真实交易：python run_market_making.py --mode portfolio
"""

import os
import asyncio
from datetime import datetime

from nautilus_trader.config import TradingNodeConfig
from nautilus_trader.config import LoggingConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.live.node import TradingNode

from strategies.market_making_strategy import MarketMakingStrategy
from config.risk_config import get_moderate_config


# ========== 配置参数 ==========

INSTRUMENT_ID = "POLY-BTC-USD.POLYMARKET"  # 示例品种 ID
PRIVATE_KEY = os.getenv("POLYMARKET_PK")
SIGNATURE_TYPE = 0  # 0=EOA, 1=Email Proxy, 2=Browser Proxy

# 做市策略配置
MM_CONFIG = {
    # 价差参数
    'base_spread': 0.02,      # 2% 基础价差
    'min_spread': 0.005,      # 0.5% 最小价差
    'max_spread': 0.10,       # 10% 最大价差

    # 订单参数
    'order_size': 20,         # 每单 20 个
    'min_order_size': 5,
    'max_order_size': 50,

    # 库存参数
    'target_inventory': 0,    # 目标库存（中性）
    'max_inventory': 200,     # 最大库存
    'inventory_skew_factor': 0.0001,
    'max_skew': 0.02,         # 2% 最大倾斜
    'hedge_threshold': 80,    # 对冲阈值
    'hedge_size': 20,         # 对冲大小

    # 价格参数
    'min_price': 0.05,        # 5%
    'max_price': 0.95,        # 95%

    # 波动率参数
    'max_volatility': 0.15,   # 15%
    'volatility_window': 100, # 100 tick

    # 资金参数
    'max_position_ratio': 0.5,    # 50%
    'max_daily_loss': -100.0,     # -100 USDC

    # 行为参数
    'update_interval_ms': 1000,       # 1 秒更新
    'use_inventory_skew': True,       # 使用库存倾斜
    'use_dynamic_spread': True,       # 使用动态价差
}


def get_strategy_config():
    """获取策略配置"""
    from dataclasses import dataclass

    @dataclass
    class MarketMakingStrategyConfig:
        instrument_id: str
        max_positions: int = 1
        min_free_balance: float = 10.0
        # ... 其他参数从 MM_CONFIG 读取

    config = MarketMakingStrategyConfig(
        instrument_id=INSTRUMENT_ID,
        **MM_CONFIG
    )

    return config


def main():
    """主函数"""
    print("=" * 80)
    print("Polymarket 做市策略")
    print("=" * 80)
    print(f"开始时间: {datetime.utcnow()}")
    print(f"品种ID: {INSTRUMENT_ID}")
    print(f"基础价差: {MM_CONFIG['base_spread']*100:.1f}%")
    print(f"订单大小: {MM_CONFIG['order_size']}个")
    print(f"最大库存: {MM_CONFIG['max_inventory']}个")
    print("=" * 80)
    print()

    # 检查环境变量
    if not PRIVATE_KEY:
        raise ValueError("POLYMARKET_PK 环境变量未设置")

    # 获取策略配置
    strategy_config = get_strategy_config()

    # 获取风险配置
    risk_configs = get_moderate_config(
        instrument_id=strategy_config.instrument_id
    )

    # 创建日志配置
    logging_config = LoggingConfig(
        log_level="INFO",
        log_colors=True,
    )

    # 创建数据客户端配置
    data_client_config = PolymarketDataClientConfig(
        private_key=PRIVATE_KEY,
        signature_type=SIGNATURE_TYPE,
        # ... 其他参数
    )

    # 创建执行客户端配置
    exec_client_config = PolymarketExecClientConfig(
        private_key=PRIVATE_KEY,
        signature_type=SIGNATURE_TYPE,
        # ... 其他参数
    )

    # 创建节点配置
    node_config = TradingNodeConfig(
        data_clients=[data_client_config],
        exec_clients=[exec_client_config],
        risk_engine_config=risk_configs['risk_engine'],
        logging_config=logging_config,
    )

    # 创建交易节点
    node = TradingNode(config=node_config)

    # 添加策略
    strategy = MarketMakingStrategy(config=strategy_config)
    node.add_strategy(strategy)

    # 启动节点
    try:
        node.start()

        print("\n✅ 策略已启动")
        print("按 Ctrl+C 停止\n")

        # 运行直到用户中断
        asyncio.get_event_loop().run_forever()

    except KeyboardInterrupt:
        print("\n\n⏹️  正在停止策略...")
        node.stop()
        print("✅ 策略已停止")

        # 打印最终统计
        print("\n" + "=" * 80)
        print("最终统计")
        print("=" * 80)

        account = node.portfolio.account_for_venue("POLYMARKET")
        if account:
            print(f"总盈亏: {account.realized_pnl() + account.unrealized_pnl()}")
            print(f"已实现盈亏: {account.realized_pnl()}")
            print(f"未实现盈亏: {account.unrealized_pnl()}")

        print("=" * 80)


if __name__ == "__main__":
    main()
