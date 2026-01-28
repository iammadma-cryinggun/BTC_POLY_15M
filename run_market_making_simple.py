"""
做市策略启动脚本

自动从多个位置读取私钥：
1. 环境变量 POLYMARKET_PK
2. .env 文件
3. 旧项目配置文件

运行方法：
    python run_market_making_simple.py
"""

import os
import sys
from pathlib import Path
from decimal import Decimal

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def load_private_key():
    """从多个位置加载私钥"""

    # 1. 尝试从环境变量读取（多个可能的名称）
    for env_name in ["POLYMARKET_PK", "POLYMARKET_PRIVATE_KEY", "private_key"]:
        pk = os.getenv(env_name)
        if pk and pk != "你的私钥放在这里" and pk != "0xYOUR_PRIVATE_KEY_HERE":
            print(f"[INFO] 从环境变量 {env_name} 读取私钥")
            return pk

    # 2. 尝试从 .env 文件读取
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"[INFO] 从 .env 文件读取配置...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('POLYMARKET_PK='):
                    pk = line.split('=', 1)[1].strip()
                    if pk and not pk.startswith('#'):
                        print(f"[INFO] 找到私钥: {pk[:10]}...{pk[-6:]}")
                        return pk

    # 3. 尝试从旧项目读取
    old_env = Path(r"D:\翻倍项目\poly_btc_update\.env")
    if old_env.exists():
        print(f"[INFO] 从旧项目 .env 文件读取...")
        try:
            with open(old_env, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'POLYMARKET_PK' in line or 'private_key' in line.lower():
                        if '=' in line:
                            pk = line.split('=', 1)[1].strip()
                            if pk and len(pk) > 10:
                                print(f"[INFO] 从旧项目找到私钥: {pk[:10]}...{pk[-6:]}")
                                return pk
        except Exception as e:
            print(f"[WARN] 读取旧项目配置失败: {e}")

    # 4. 尝试从 poly-sdk-trader 读取
    poly_sdk_env = Path(r"D:\翻倍项目\poly-sdk-trader\config\.env")
    if poly_sdk_env.exists():
        print(f"[INFO] 从 poly-sdk-trader 读取...")
        try:
            with open(poly_sdk_env, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'PRIVATE_KEY' in line or 'private_key' in line.lower():
                        if '=' in line:
                            pk = line.split('=', 1)[1].strip()
                            if pk and len(pk) > 10:
                                print(f"[INFO] 从 poly-sdk-trader 找到私钥: {pk[:10]}...{pk[-6:]}")
                                return pk
        except Exception as e:
            print(f"[WARN] 读取 poly-sdk-trader 配置失败: {e}")

    return None


def main():
    """主函数"""
    print("=" * 80)
    print("Polymarket 做市策略 - 启动")
    print("=" * 80)

    # 加载私钥
    private_key = load_private_key()

    if not private_key:
        print("\n[ERROR] 未找到私钥！")
        print("\n请设置私钥（任一方式）：")
        print("1. 环境变量: export POLYMARKET_PK=0x...")
        print("2. .env 文件: 在项目根目录创建 .env 文件")
        print("3. 直接修改: 编辑 run_market_making_simple.py")
        print("\n示例:")
        print("  POLYMARKET_PK=0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef")
        return 1

    # 设置环境变量（供 NautilusTrader 使用）
    os.environ["POLYMARKET_PK"] = private_key

    print(f"\n[OK] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

    # 导入策略
    try:
        from nautilus_trader.live.node import TradingNode
        from nautilus_trader.config import LoggingConfig, StrategyConfig
        from nautilus_trader.adapters.polymarket import (
            PolymarketDataClientConfig,
            PolymarketExecClientConfig,
        )
        from strategies.market_making_strategy import MarketMakingStrategy
        from decimal import Decimal
    except ImportError as e:
        print(f"\n[ERROR] 导入失败: {e}")
        return 1

    # 创建正确的配置类（继承 StrategyConfig）
    class MarketMakingLiveConfig(StrategyConfig, frozen=True):
        instrument_id: str
        base_spread: Decimal
        min_spread: Decimal
        max_spread: Decimal
        order_size: int
        min_order_size: int
        max_order_size: int
        target_inventory: int
        max_inventory: int
        inventory_skew_factor: Decimal
        max_skew: Decimal
        hedge_threshold: int
        hedge_size: int
        min_price: Decimal
        max_price: Decimal
        max_volatility: Decimal
        volatility_window: int
        max_position_ratio: Decimal
        max_daily_loss: Decimal
        update_interval_ms: int
        use_inventory_skew: bool
        use_dynamic_spread: bool

    # 极度保守的参数（适合首次测试）
    SAFE_CONFIG = {
        'instrument_id': "POLY-BTC-USD.POLYMARKET",
        'base_spread': Decimal("0.03"),      # 3% 价差（更大，更安全）
        'min_spread': Decimal("0.01"),      # 1% 最小价差
        'max_spread': Decimal("0.15"),      # 15% 最大价差
        'order_size': 2,                    # 每单 2 个（极小）
        'min_order_size': 1,                # 最小 1 个
        'max_order_size': 5,                # 最大 5 个
        'target_inventory': 0,              # 目标库存（中性）
        'max_inventory': 20,                # 最大库存 20 个（极小）
        'inventory_skew_factor': Decimal("0.0002"),  # 更强的倾斜
        'max_skew': Decimal("0.03"),         # 3% 最大倾斜
        'hedge_threshold': 10,              # 10 个就开始对冲
        'hedge_size': 5,                    # 对冲 5 个
        'min_price': Decimal("0.05"),        # 5%
        'max_price': Decimal("0.95"),        # 95%
        'max_volatility': Decimal("0.10"),   # 10% 波动率限制（更严格）
        'volatility_window': 50,
        'max_position_ratio': Decimal("0.3"),    # 30%（更保守）
        'max_daily_loss': Decimal("-20.0"),     # -20 USDC 日亏损限制
        'update_interval_ms': 2000,         # 2 秒更新（更慢）
        'use_inventory_skew': True,
        'use_dynamic_spread': True,
    }

    print("\n" + "=" * 80)
    print("安全配置（小资金测试）")
    print("=" * 80)
    print(f"  订单大小: {SAFE_CONFIG['order_size']} 个")
    print(f"  最大库存: {SAFE_CONFIG['max_inventory']} 个")
    print(f"  基础价差: {SAFE_CONFIG['base_spread']*100:.1f}%")
    print(f"  日亏损限制: {SAFE_CONFIG['max_daily_loss']} USDC")
    print("=" * 80)

    # 创建配置对象
    config = MarketMakingLiveConfig(**SAFE_CONFIG)

    # 创建策略
    strategy = MarketMakingStrategy(config)

    print("\n[INFO] 策略已创建")
    print("[INFO] 注意：这是真实交易模式，会使用真实资金！")
    print("[INFO] 建议监控 1-2 小时，观察策略表现")
    print("\n按 Ctrl+C 停止策略\n")

    # 这里需要实际的 TradingNode 配置和启动
    # 暂时只显示配置信息
    print("\n" + "=" * 80)
    print("下一步：")
    print("=" * 80)
    print("1. 私钥已加载 [OK]")
    print("2. 策略已创建 [OK]")
    print("3. 需要完整配置 TradingNode")
    print("\n建议：")
    print("- 先用 10-20 USDC 测试")
    print("- 监控 1-2 小时")
    print("- 观察成交率和盈亏")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
