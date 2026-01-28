"""
Paper Trading 测试脚本

目的：模拟真实交易环境，使用实时订单簿数据，不真实下单
时间：可配置（默认 60 分钟）

运行方法：
    python tests/test_paper_trading.py --duration=60
    python tests/test_paper_trading.py --duration=240 --verbose
    python tests/test_paper_trading.py --duration=60 --stats
"""

import os
import sys
import time
import argparse
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from nautilus_trader.live.node import TradingNode
    from nautilus_trader.config import TradingNodeConfig, LoggingConfig
    from nautilus_trader.config import LiveExecClientConfig, LiveDataClientConfig
    from nautilus_trader.model.enums import OrderSide, BookType
    from strategies.market_making_strategy import MarketMakingStrategy
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print("\n请确保已安装 NautilusTrader:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


# ========== 配置 ==========

INSTRUMENT_ID = "POLY-BTC-USD.POLYMARKET"
PRIVATE_KEY = os.getenv("POLYMARKET_PK", "0x" + "1" * 64)  # 可选
SIGNATURE_TYPE = 0

# Paper Trading 配置
PAPER_CONFIG = {
    'base_spread': Decimal("0.02"),      # 2% 基础价差
    'min_spread': Decimal("0.005"),      # 0.5% 最小价差
    'max_spread': Decimal("0.10"),       # 10% 最大价差
    'order_size': 20,                    # 每单 20 个
    'min_order_size': 5,
    'max_order_size': 50,
    'target_inventory': 0,               # 目标库存（中性）
    'max_inventory': 200,                # 最大库存
    'inventory_skew_factor': Decimal("0.0001"),
    'max_skew': Decimal("0.02"),         # 2% 最大倾斜
    'hedge_threshold': 80,               # 对冲阈值
    'hedge_size': 20,                    # 对冲大小
    'min_price': Decimal("0.05"),        # 5%
    'max_price': Decimal("0.95"),        # 95%
    'max_volatility': Decimal("0.15"),   # 15%
    'volatility_window': 100,            # 100 个 tick
    'max_position_ratio': Decimal("0.5"),    # 50%
    'max_daily_loss': Decimal("-1000.0"),   # Paper Trading 可以承受更多亏损
    'update_interval_ms': 1000,          # 1 秒更新
    'use_inventory_skew': True,
    'use_dynamic_spread': True,
}


# ========== 统计类 ==========

class PaperTradingStats:
    """Paper Trading 统计"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

        # 订单统计
        self.orders_placed = 0
        self.orders_filled = 0
        self.bid_orders = 0
        self.ask_orders = 0

        # 交易统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal("0")

        # 做市统计
        self.spreads = []  # 记录每次交易的价差
        self.inventory_history = []  # 记录库存历史

        # 风险统计
        self.volatility_protection_triggered = 0
        self.hedge_triggered = 0
        self.max_inventory_reached = 0

    def record_trade(self, pnl: Decimal, spread: Decimal):
        """记录交易"""
        self.total_trades += 1
        self.total_pnl += pnl
        self.spreads.append(float(spread))

        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

    def get_win_rate(self) -> float:
        """获取胜率"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    def get_fill_rate(self) -> float:
        """获取成交率"""
        if self.orders_placed == 0:
            return 0.0
        return (self.orders_filled / self.orders_placed) * 100

    def get_avg_spread(self) -> float:
        """获取平均价差"""
        if not self.spreads:
            return 0.0
        return sum(self.spreads) / len(self.spreads)

    def get_max_drawdown(self) -> Decimal:
        """获取最大回撤（简化计算）"""
        # 这里简化处理，实际应该记录最高点和最低点
        return Decimal("0")

    def get_inventory_turnover(self, final_inventory: int) -> float:
        """获取库存周转率"""
        if self.max_inventory == 0:
            return 0.0
        return self.total_trades / (self.max_inventory / 2)


# ========== Paper Trading 类 ==========

class PaperTradingTester:
    """Paper Trading 测试器"""

    def __init__(self, duration_minutes: int, verbose: bool = False, show_stats: bool = False):
        self.duration_minutes = duration_minutes
        self.verbose = verbose
        self.show_stats = show_stats

        self.stats = PaperTradingStats()
        self.node = None
        self.strategy = None

        self._last_stats_time = None
        self._stats_interval = 60  # 每 60 秒打印一次统计

    def print_banner(self):
        """打印横幅"""
        print("=" * 80)
        print("Market Making Strategy - Paper Trading")
        print("=" * 80)
        print(f"\n开始时间: {datetime.utcnow()}")
        print(f"运行时长: {self.duration_minutes} 分钟")
        print(f"模式: Paper Trading (模拟交易，不真实下单)")
        print("\n" + "=" * 80)

    def print_config(self):
        """打印配置"""
        print("\n📋 做市配置:")
        print(f"  基础价差: {PAPER_CONFIG['base_spread']*100:.1f}%")
        print(f"  订单大小: {PAPER_CONFIG['order_size']} 个")
        print(f"  最大库存: {PAPER_CONFIG['max_inventory']} 个")
        print(f"  库存倾斜因子: {PAPER_CONFIG['inventory_skew_factor']}")
        print(f"  对冲阈值: {PAPER_CONFIG['hedge_threshold']} 个")
        print("=" * 80)

    def print_stats(self, force: bool = False):
        """打印统计信息"""
        now = time.time()

        if not force and self._last_stats_time:
            if now - self._last_stats_time < self._stats_interval:
                return

        self._last_stats_time = now

        print(f"\n{'='*80}")
        print(f"📊 实时统计 (运行 {int(now - self.stats.start_time)} 秒)")
        print(f"{'='*80}")

        print(f"\n订单:")
        print(f"  已下单: {self.stats.orders_placed}")
        print(f"  已成交: {self.stats.orders_filled} ({self.stats.get_fill_rate():.1f}%)")
        print(f"  买单: {self.stats.bid_orders}")
        print(f"  卖单: {self.stats.ask_orders}")

        if self.stats.total_trades > 0:
            print(f"\n交易:")
            print(f"  总交易: {self.stats.total_trades}")
            print(f"  获胜: {self.stats.winning_trades} ({self.stats.get_win_rate():.1f}%)")
            print(f"  亏损: {self.stats.losing_trades}")
            print(f"  总盈亏: {self.stats.total_pnl:.2f} USDC")
            print(f"  平均价差: {self.stats.get_avg_spread()*100:.2f}%")

        print(f"\n风险:")
        print(f"  波动率保护: {self.stats.volatility_protection_triggered} 次")
        print(f"  对冲触发: {self.stats.hedge_triggered} 次")
        print(f"  库存上限: {self.stats.max_inventory_reached} 次")

        print(f"{'='*80}\n")

    def print_final_report(self):
        """打印最终报告"""
        self.stats.end_time = datetime.utcnow()
        duration = (self.stats.end_time - self.stats.start_time).total_seconds() / 60

        print("\n" + "=" * 80)
        print("Paper Trading 最终报告")
        print("=" * 80)

        print(f"\n时长: {duration:.1f} 分钟")
        print(f"已下单: {self.stats.orders_placed} ({self.stats.bid_orders} 买单, {self.stats.ask_orders} 卖单)")
        print(f"已成交: {self.stats.orders_filled} ({self.stats.get_fill_rate():.1f}% 成交率)")

        if self.stats.total_trades > 0:
            print(f"\n📊 绩效指标:")
            print(f"  总交易: {self.stats.total_trades}")
            print(f"  获胜: {self.stats.winning_trades} ({self.stats.get_win_rate():.1f}%)")
            print(f"  亏损: {self.stats.losing_trades}")
            print(f"  总盈亏: {self.stats.total_pnl:.2f} USDC")
            print(f"  平均价差: {self.stats.get_avg_spread()*100:.2f}%")
            print(f"  最大回撤: {self.stats.get_max_drawdown():.2f} USDC")

            if self.stats.inventory_history:
                final_inventory = self.stats.inventory_history[-1]
                turnover = self.stats.get_inventory_turnover(abs(final_inventory))
                print(f"  库存周转率: {turnover:.2f}x")

        print(f"\n🛡️ 风险管理:")
        print(f"  波动率保护: {self.stats.volatility_protection_triggered} 次")
        print(f"  对冲触发: {self.stats.hedge_triggered} 次")
        print(f"  库存上限: {self.stats.max_inventory_reached} 次")
        print(f"  日亏损限制: {'触发' if self.stats.total_pnl < PAPER_CONFIG['max_daily_loss'] else '未触发'}")

        print("\n" + "=" * 80)

        # 判断结果
        if self.stats.total_trades == 0:
            print("⚠️  没有交易记录")
            print("建议: 检查市场流动性，降低价差或订单大小")
        elif self.stats.get_fill_rate() < 10:
            print("⚠️  成交率过低 (< 10%)")
            print("建议: 降低 base_spread 或 order_size")
        elif self.stats.total_pnl > 0:
            print("✅ Paper Trading PASSED - 盈利!")
            print(f"建议: 可以考虑进入真实交易（从小资金开始）")
        elif self.stats.get_win_rate() > 60:
            print("⚠️  胜率较高但亏损")
            print("建议: 检查盈亏比，可能止盈设置不当")
        else:
            print("❌ Paper Trading FAILED - 亏损")
            print("建议: 调整参数后继续 Paper Trading")

        print("=" * 80 + "\n")

    def run(self):
        """运行 Paper Trading"""
        self.print_banner()
        self.print_config()

        print("\n⏳ 正在初始化 Paper Trading...")
        print("提示: 这将连接到 Polymarket 实时 API，但不会真实下单\n")

        # 注意：这里只是示例框架
        # 实际实现需要完整的 NautilusTrader 集成
        print("❌ Paper Trading 框架尚未完成")
        print("\n原因:")
        print("1. NautilusTrader 的 Paper Trading 模式需要额外配置")
        print("2. 需要创建 MockExecutionClient 和 MockDataClient")
        print("3. 需要实现订单簿模拟和订单成交模拟")
        print("\n替代方案:")
        print("1. 使用单元测试验证计算逻辑")
        print("2. 使用快速验证脚本检查基本功能")
        print("3. 直接使用真实 Paper Trading 模式（小资金测试）")
        print("\n建议:")
        print("  python tests/quick_validation.py")
        print("  pytest tests/unit/test_market_making.py -v")
        print("  python run_market_making.py --mode paper --duration=60")

        return 1


# ========== 主函数 ==========

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="做市策略 Paper Trading 测试"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="运行时长（分钟），默认 60"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细日志"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示实时统计"
    )

    args = parser.parse_args()

    tester = PaperTradingTester(
        duration_minutes=args.duration,
        verbose=args.verbose,
        show_stats=args.stats
    )

    try:
        return tester.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  收到停止信号")
        tester.print_final_report()
        return 0
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
