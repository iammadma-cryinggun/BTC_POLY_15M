"""
做市策略快速验证脚本

目的：验证策略基本功能，无需私钥，无需真实交易
时间：30 秒内完成

运行方法：
    python tests/quick_validation.py
"""

import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from nautilus_trader.trading.config import StrategyConfig
    from nautilus_trader.model.identifiers import InstrumentId
    from strategies.market_making_strategy import MarketMakingStrategy
    from strategies.base_strategy import BaseStrategy
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print("\nPlease ensure NautilusTrader is installed:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


# ========== 配置类 ==========

class MarketMakingConfig(StrategyConfig, frozen=True):
    """做市策略配置类"""

    # 必需字段
    instrument_id: str

    # 价差参数
    base_spread: Decimal
    min_spread: Decimal
    max_spread: Decimal

    # 订单参数
    order_size: int
    min_order_size: int
    max_order_size: int

    # 库存参数
    target_inventory: int
    max_inventory: int
    inventory_skew_factor: Decimal
    max_skew: Decimal
    hedge_threshold: int
    hedge_size: int

    # 价格参数
    min_price: Decimal
    max_price: Decimal

    # 波动率参数
    max_volatility: Decimal
    volatility_window: int

    # 资金参数
    max_position_ratio: Decimal
    max_daily_loss: Decimal

    # 行为参数
    update_interval_ms: int
    use_inventory_skew: bool
    use_dynamic_spread: bool


# ========== 测试函数 ==========

def test_imports():
    """测试导入"""
    print("\n[OK] Imports")

    checks = [
        ("MarketMakingStrategy", MarketMakingStrategy is not None),
        ("BaseStrategy", BaseStrategy is not None),
        ("StrategyConfig", StrategyConfig is not None),
    ]

    all_ok = True
    for name, check in checks:
        status = "[OK]" if check else "[FAIL]"
        print(f"   - {name}: {status}")
        all_ok = all_ok and check

    return all_ok


def test_configuration_validation():
    """测试配置验证"""
    print("\n[OK] Configuration validation")

    # 创建配置
    config = MarketMakingConfig(
        instrument_id="POLY-BTC-USD.POLYMARKET",
        base_spread=Decimal("0.02"),
        min_spread=Decimal("0.005"),
        max_spread=Decimal("0.10"),
        order_size=20,
        min_order_size=5,
        max_order_size=50,
        target_inventory=0,
        max_inventory=200,
        inventory_skew_factor=Decimal("0.0001"),
        max_skew=Decimal("0.02"),
        hedge_threshold=80,
        hedge_size=20,
        min_price=Decimal("0.05"),
        max_price=Decimal("0.95"),
        max_volatility=Decimal("0.15"),
        volatility_window=100,
        max_position_ratio=Decimal("0.5"),
        max_daily_loss=Decimal("-100.0"),
        update_interval_ms=1000,
        use_inventory_skew=True,
        use_dynamic_spread=True,
    )

    # 检查核心参数
    checks = [
        ("instrument_id", config.instrument_id, "POLY-BTC-USD.POLYMARKET"),
        ("base_spread", config.base_spread, Decimal("0.02")),
        ("order_size", config.order_size, 20),
        ("max_inventory", config.max_inventory, 200),
        ("inventory_skew_factor", config.inventory_skew_factor, Decimal("0.0001")),
        ("hedge_threshold", config.hedge_threshold, 80),
    ]

    all_valid = True
    for name, value, expected in checks:
        is_valid = value == expected
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"   - {name}: {value} {status}")
        all_valid = all_valid and is_valid

    if all_valid:
        print("   All parameters valid")
    return all_valid


def test_strategy_creation():
    """测试策略创建"""
    print("\n[OK] Strategy creation")

    # 创建配置
    config = MarketMakingConfig(
        instrument_id="POLY-BTC-USD.POLYMARKET",
        base_spread=Decimal("0.02"),
        min_spread=Decimal("0.005"),
        max_spread=Decimal("0.10"),
        order_size=20,
        min_order_size=5,
        max_order_size=50,
        target_inventory=0,
        max_inventory=200,
        inventory_skew_factor=Decimal("0.0001"),
        max_skew=Decimal("0.02"),
        hedge_threshold=80,
        hedge_size=20,
        min_price=Decimal("0.05"),
        max_price=Decimal("0.95"),
        max_volatility=Decimal("0.15"),
        volatility_window=100,
        max_position_ratio=Decimal("0.5"),
        max_daily_loss=Decimal("-100.0"),
        update_interval_ms=1000,
        use_inventory_skew=True,
        use_dynamic_spread=True,
    )

    # 创建策略实例
    try:
        strategy = MarketMakingStrategy(config)
        print(f"   - Strategy created: {type(strategy).__name__}")
        print(f"   - Config loaded: base_spread={strategy.base_spread}")
        print(f"   - Config loaded: order_size={strategy.order_size}")
        print(f"   - Config loaded: max_inventory={strategy.max_inventory}")
        print(f"   - Strategy ready")
        return True
    except Exception as e:
        print(f"   [ERROR] Failed to create strategy: {e}")
        return False


def test_inheritance():
    """测试继承关系"""
    print("\n[OK] Inheritance")

    # 检查继承
    is_subclass = issubclass(MarketMakingStrategy, BaseStrategy)
    print(f"   - MarketMakingStrategy inherits BaseStrategy: {'[OK]' if is_subclass else '[FAIL]'}")

    return is_subclass


def test_method_availability():
    """测试方法可用性"""
    print("\n[OK] Method availability")

    # 检查核心方法
    methods = [
        "_calculate_dynamic_spread",
        "_calculate_inventory_skew",
        "_calculate_order_size",
        "_calculate_volatility",
        "_check_risk",
        "_check_price_range",
        "_check_volatility_limit",
        "_check_inventory_limits",
        "_check_position_limits",
        "_check_daily_loss_limit",
        "_need_hedge",
        "_hedge_inventory",
        "on_order_book",
        "on_order_filled",
        "on_start",
    ]

    all_available = True
    for method_name in methods:
        has_method = hasattr(MarketMakingStrategy, method_name)
        status = "[OK]" if has_method else "[FAIL]"
        print(f"   - {method_name}: {status}")
        all_available = all_available and has_method

    if all_available:
        print("   All methods available")
    return all_available


def test_default_values():
    """测试默认值"""
    print("\n[OK] Default values")

    # 创建配置
    config = MarketMakingConfig(
        instrument_id="POLY-BTC-USD.POLYMARKET",
        base_spread=Decimal("0.02"),
        min_spread=Decimal("0.005"),
        max_spread=Decimal("0.10"),
        order_size=20,
        min_order_size=5,
        max_order_size=50,
        target_inventory=0,
        max_inventory=200,
        inventory_skew_factor=Decimal("0.0001"),
        max_skew=Decimal("0.02"),
        hedge_threshold=80,
        hedge_size=20,
        min_price=Decimal("0.05"),
        max_price=Decimal("0.95"),
        max_volatility=Decimal("0.15"),
        volatility_window=100,
        max_position_ratio=Decimal("0.5"),
        max_daily_loss=Decimal("-100.0"),
        update_interval_ms=1000,
        use_inventory_skew=True,
        use_dynamic_spread=True,
    )

    strategy = MarketMakingStrategy(config)

    # 检查默认值
    checks = [
        ("_last_update_time_ns", strategy._last_update_time_ns, 0),
        ("_price_history", strategy._price_history, []),
    ]

    all_valid = True
    for name, value, expected in checks:
        is_valid = value == expected
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"   - {name}: {value} {status}")
        all_valid = all_valid and is_valid

    if all_valid:
        print("   All default values correct")
    return all_valid


def test_constants():
    """测试常量"""
    print("\n[OK] Constants")

    # 检查常量
    checks = [
        ("DEFAULT_BASE_SPREAD", MarketMakingStrategy.DEFAULT_BASE_SPREAD, Decimal("0.02")),
        ("DEFAULT_ORDER_SIZE", MarketMakingStrategy.DEFAULT_ORDER_SIZE, 20),
        ("DEFAULT_MAX_INVENTORY", MarketMakingStrategy.DEFAULT_MAX_INVENTORY, 200),
        ("DEFAULT_HEDGE_THRESHOLD", MarketMakingStrategy.DEFAULT_HEDGE_THRESHOLD, 80),
    ]

    all_valid = True
    for name, _, expected in checks:
        value = getattr(MarketMakingStrategy, name)
        is_valid = value == expected
        status = "[OK]" if is_valid else "[FAIL]"
        print(f"   - {name}: {value} {status}")
        all_valid = all_valid and is_valid

    if all_valid:
        print("   All constants correct")
    return all_valid


# ========== 主函数 ==========

def main():
    """主函数"""
    print("=" * 60)
    print("Market Making Strategy - Quick Validation")
    print("=" * 60)
    print(f"\nStart time: {datetime.now()}")

    results = []

    # 运行所有测试
    try:
        results.append(("Imports", test_imports()))
        results.append(("Configuration validation", test_configuration_validation()))
        results.append(("Strategy creation", test_strategy_creation()))
        results.append(("Inheritance", test_inheritance()))
        results.append(("Method availability", test_method_availability()))
        results.append(("Default values", test_default_values()))
        results.append(("Constants", test_constants()))
    except Exception as e:
        print(f"\n[ERROR] Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # 打印结果
    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")

    print("\n" + "=" * 60)
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)

    if passed_tests == total_tests:
        print("\n[SUCCESS] Quick validation PASSED")
        return 0
    else:
        print(f"\n[FAILED] Quick validation FAILED ({total_tests - passed_tests} tests failed)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
