"""
做市策略单元测试

测试范围：
- 核心计算逻辑（价差、倾斜、订单大小、波动率）
- 风险检查（价格范围、波动率、库存、仓位、日亏损）
- 对冲逻辑

运行方法：
    pytest tests/unit/test_market_making.py -v
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, MagicMock
from datetime import datetime

from strategies.market_making_strategy import MarketMakingStrategy


# ========== Fixtures ==========

@pytest.fixture
def config():
    """创建测试配置"""
    mock_config = Mock()
    mock_config.instrument_id = "POLY-BTC-USD.POLYMARKET"
    mock_config.base_spread = Decimal("0.02")
    mock_config.min_spread = Decimal("0.005")
    mock_config.max_spread = Decimal("0.10")
    mock_config.order_size = 20
    mock_config.min_order_size = 5
    mock_config.max_order_size = 50
    mock_config.target_inventory = 0
    mock_config.max_inventory = 200
    mock_config.inventory_skew_factor = Decimal("0.0001")
    mock_config.max_skew = Decimal("0.02")
    mock_config.hedge_threshold = 80
    mock_config.hedge_size = 20
    mock_config.min_price = Decimal("0.05")
    mock_config.max_price = Decimal("0.95")
    mock_config.max_volatility = Decimal("0.15")
    mock_config.volatility_window = 100
    mock_config.max_position_ratio = Decimal("0.5")
    mock_config.max_daily_loss = Decimal("-100.0")
    mock_config.update_interval_ms = 1000
    mock_config.use_inventory_skew = True
    mock_config.use_dynamic_spread = True
    return mock_config


@pytest.fixture
def strategy(config):
    """创建策略实例"""
    strat = MarketMakingStrategy(config)

    # 注入 Mock 对象
    strat.instrument = Mock()
    strat.instrument.id = config.instrument_id
    strat.clock = Mock()
    strat.clock.timestamp_ns = Mock(return_value=1700000000000000000)
    strat.cache = Mock()
    strat.cache.portfolio = Mock()
    strat.log = Mock()
    strat.order_factory = Mock()

    return strat


@pytest.fixture
def mock_order_book():
    """创建模拟订单簿"""
    book = Mock()
    book.midpoint = Mock(return_value=Decimal("0.60"))

    # 模拟买卖单深度
    bid_level = Mock()
    bid_level.size = Mock(return_value=Decimal("100"))
    ask_level = Mock()
    ask_level.size = Mock(return_value=Decimal("100"))

    book.bids = Mock(return_value=[bid_level] * 5)
    book.asks = Mock(return_value=[ask_level] * 5)

    return book


# ========== 动态价差测试 ==========

def test_calculate_dynamic_spread_base(strategy, mock_order_book):
    """测试基础价差（无波动率）"""
    spread = strategy._calculate_dynamic_spread(mock_order_book)

    assert spread == strategy.base_spread
    assert spread == Decimal("0.02")


def test_calculate_dynamic_spread_high_volatility(strategy, mock_order_book):
    """测试高波动率下的价差"""
    # 添加价格历史（高波动）
    for i in range(100):
        price = Decimal("0.60") + Decimal(str(i * 0.001))
        strategy._update_price_history(price)

    spread = strategy._calculate_dynamic_spread(mock_order_book)

    # 高波动率应该增加价差
    assert spread > strategy.base_spread
    assert spread <= strategy.max_spread


def test_calculate_dynamic_spread_limits(strategy, mock_order_book):
    """测试价差限制"""
    # 设置最小价差
    strategy.base_spread = Decimal("0.001")
    spread = strategy._calculate_dynamic_spread(mock_order_book)
    assert spread >= strategy.min_spread

    # 设置最大价差
    strategy.base_spread = Decimal("0.20")
    spread = strategy._calculate_dynamic_spread(mock_order_book)
    assert spread <= strategy.max_spread


# ========== 库存倾斜测试 ==========

def test_calculate_inventory_skew_neutral(strategy):
    """测试中性持仓（无倾斜）"""
    # Mock 空持仓
    strategy.cache.portfolio.position = Mock(return_value=None)
    strategy.get_current_position = Mock(return_value=None)

    skew = strategy._calculate_inventory_skew()

    assert skew == Decimal("0")


def test_calculate_inventory_skew_long_position(strategy):
    """测试多头持仓的倾斜"""
    # Mock 多头持仓
    strategy.get_current_position = Mock(return_value={
        'side': 'LONG',
        'quantity': 100,
        'entry_price': Decimal("0.60"),
        'unrealized_pnl': Decimal("0"),
    })

    skew = strategy._calculate_inventory_skew()

    # 持有 100 个 YES，目标 0，倾斜应该是正的
    # skew = (100 - 0) * 0.0001 = 0.01
    assert skew > 0
    assert skew == Decimal("0.01")


def test_calculate_inventory_skew_short_position(strategy):
    """测试空头持仓的倾斜"""
    # Mock 空头持仓
    strategy.get_current_position = Mock(return_value={
        'side': 'SHORT',
        'quantity': -100,
        'entry_price': Decimal("0.60"),
        'unrealized_pnl': Decimal("0"),
    })

    skew = strategy._calculate_inventory_skew()

    # 持有 -100 个 YES，目标 0，倾斜应该是负的
    # skew = (-100 - 0) * 0.0001 = -0.01
    assert skew < 0
    assert skew == Decimal("-0.01")


def test_calculate_inventory_skew_max_limit(strategy):
    """测试库存倾斜最大限制"""
    # 极大持仓
    strategy.get_current_position = Mock(return_value={
        'side': 'LONG',
        'quantity': 500,
        'entry_price': Decimal("0.60"),
        'unrealized_pnl': Decimal("0"),
    })

    skew = strategy._calculate_inventory_skew()

    # 应该被限制在 max_skew
    assert skew == strategy.max_skew


# ========== 订单大小测试 ==========

def test_calculate_order_size_normal_depth(strategy, mock_order_book):
    """测试正常深度下的订单大小"""
    order_size = strategy._calculate_order_size(mock_order_book)

    # 正常深度 (100)，应该使用配置的大小
    assert order_size == strategy.order_size


def test_calculate_order_size_low_depth(strategy, mock_order_book):
    """测试低深度下的订单大小"""
    # 模拟低深度
    bid_level = Mock()
    bid_level.size = Mock(return_value=Decimal("10"))
    ask_level = Mock()
    ask_level.size = Mock(return_value=Decimal("10"))

    mock_order_book.bids = Mock(return_value=[bid_level] * 5)
    mock_order_book.asks = Mock(return_value=[ask_level] * 5)

    order_size = strategy._calculate_order_size(mock_order_book)

    # 低深度，应该减小订单
    assert order_size <= strategy.min_order_size * 2


def test_calculate_order_size_high_depth(strategy, mock_order_book):
    """测试高深度下的订单大小"""
    # 模拟高深度
    bid_level = Mock()
    bid_level.size = Mock(return_value=Decimal("500"))
    ask_level = Mock()
    ask_level.size = Mock(return_value=Decimal("500"))

    mock_order_book.bids = Mock(return_value=[bid_level] * 5)
    mock_order_book.asks = Mock(return_value=[ask_level] * 5)

    order_size = strategy._calculate_order_size(mock_order_book)

    # 高深度，可以使用较大订单
    assert order_size <= strategy.max_order_size


# ========== 波动率计算测试 ==========

def test_calculate_volatility_no_history(strategy):
    """测试无历史数据时的波动率"""
    volatility = strategy._calculate_volatility()

    assert volatility == Decimal("0")


def test_calculate_volatility_with_history(strategy):
    """测试有历史数据时的波动率"""
    # 添加稳定价格历史
    for i in range(100):
        strategy._update_price_history(Decimal("0.60"))

    volatility = strategy._calculate_volatility()

    # 稳定价格，波动率应该很低
    assert volatility >= Decimal("0")
    assert volatility < Decimal("0.01")


def test_calculate_volatility_volatile_prices(strategy):
    """测试波动价格下的波动率"""
    # 添加波动价格历史
    for i in range(100):
        price = Decimal("0.50") + Decimal(str(i * 0.002))
        strategy._update_price_history(price)

    volatility = strategy._calculate_volatility()

    # 波动价格，波动率应该较高
    assert volatility > Decimal("0.01")


# ========== 风险检查测试 ==========

def test_check_price_range_normal(strategy, mock_order_book):
    """测试正常价格范围"""
    mock_order_book.midpoint = Mock(return_value=Decimal("0.60"))

    result = strategy._check_price_range(mock_order_book)

    assert result is True


def test_check_price_range_too_low(strategy, mock_order_book):
    """测试价格过低"""
    mock_order_book.midpoint = Mock(return_value=Decimal("0.03"))

    result = strategy._check_price_range(mock_order_book)

    assert result is False


def test_check_price_range_too_high(strategy, mock_order_book):
    """测试价格过高"""
    mock_order_book.midpoint = Mock(return_value=Decimal("0.97"))

    result = strategy._check_price_range(mock_order_book)

    assert result is False


def test_check_volatility_limit_normal(strategy):
    """测试正常波动率"""
    # 添加稳定价格
    for i in range(100):
        strategy._update_price_history(Decimal("0.60"))

    result = strategy._check_volatility_limit()

    assert result is True


def test_check_volatility_limit_too_high(strategy):
    """测试波动率过高"""
    # 添加极端波动价格
    for i in range(100):
        price = Decimal("0.40") + Decimal(str(i * 0.003))
        strategy._update_price_history(price)

    result = strategy._check_volatility_limit()

    assert result is False


def test_check_inventory_limits_normal(strategy):
    """测试正常库存"""
    strategy.get_current_position = Mock(return_value={
        'quantity': 50,
    })

    result = strategy._check_inventory_limits()

    assert result is True


def test_check_inventory_limits_exceeded(strategy):
    """测试库存超限"""
    strategy.get_current_position = Mock(return_value={
        'quantity': 250,  # 超过 max_inventory (200)
    })

    result = strategy._check_inventory_limits()

    assert result is False


def test_check_position_limits_normal(strategy):
    """测试正常仓位"""
    strategy.get_account_info = Mock(return_value={
        'free_balance': MagicMock(amount=Decimal("1000")),
    })
    strategy.get_current_position = Mock(return_value={
        'quantity': 100,
        'current_price': 0.60,
    })

    result = strategy._check_position_limits()

    # 100 * 0.60 = 60 < 1000 * 0.5 = 500
    assert result is True


def test_check_position_limits_exceeded(strategy):
    """测试仓位超限"""
    strategy.get_account_info = Mock(return_value={
        'free_balance': MagicMock(amount=Decimal("100")),
    })
    strategy.get_current_position = Mock(return_value={
        'quantity': 200,
        'current_price': 0.60,
    })

    result = strategy._check_position_limits()

    # 200 * 0.60 = 120 > 100 * 0.5 = 50
    assert result is False


def test_check_daily_loss_limit_normal(strategy):
    """测试正常日亏损"""
    strategy.get_account_info = Mock(return_value={
        'realized_pnl': MagicMock(amount=Decimal("10")),
        'unrealized_pnl': MagicMock(amount=Decimal("5")),
    })

    result = strategy._check_daily_loss_limit()

    # 10 + 5 = 15 > -100
    assert result is True


def test_check_daily_loss_limit_exceeded(strategy):
    """测试日亏损超限"""
    strategy.get_account_info = Mock(return_value={
        'realized_pnl': MagicMock(amount=Decimal("-80")),
        'unrealized_pnl': MagicMock(amount=Decimal("-30")),
    })

    result = strategy._check_daily_loss_limit()

    # -80 + (-30) = -110 < -100
    assert result is False


# ========== 对冲逻辑测试 ==========

def test_need_hedge_no_position(strategy):
    """测试无持仓时不需要对冲"""
    strategy.get_current_position = Mock(return_value=None)

    result = strategy._need_hedge()

    assert result is False


def test_need_hedge_below_threshold(strategy):
    """测试库存低于阈值时不需要对冲"""
    strategy.get_current_position = Mock(return_value={
        'quantity': 50,  # 低于 hedge_threshold (80)
    })

    result = strategy._need_hedge()

    assert result is False


def test_need_hedge_above_threshold(strategy):
    """测试库存高于阈值时需要对冲"""
    strategy.get_current_position = Mock(return_value={
        'quantity': 100,  # 高于 hedge_threshold (80)
    })

    result = strategy._need_hedge()

    assert result is True


def test_need_hedge_negative_threshold(strategy):
    """测试负库存（空头）对冲"""
    strategy.get_current_position = Mock(return_value={
        'quantity': -100,  # abs(-100) > 80
    })

    result = strategy._need_hedge()

    assert result is True


# ========== 综合风险检查测试 ==========

def test_check_risk_all_passed(strategy, mock_order_book):
    """测试所有风险检查通过"""
    # 设置正常条件
    mock_order_book.midpoint = Mock(return_value=Decimal("0.60"))
    strategy.get_current_position = Mock(return_value={'quantity': 50})
    strategy.get_account_info = Mock(return_value={
        'free_balance': MagicMock(amount=Decimal("1000")),
        'realized_pnl': MagicMock(amount=Decimal("10")),
        'unrealized_pnl': MagicMock(amount=Decimal("5")),
    })

    result = strategy._check_risk(mock_order_book)

    assert result is True


def test_check_risk_one_failed(strategy, mock_order_book):
    """测试一个风险检查失败"""
    # 价格超出范围
    mock_order_book.midpoint = Mock(return_value=Decimal("0.03"))
    strategy.get_current_position = Mock(return_value={'quantity': 50})
    strategy.get_account_info = Mock(return_value={
        'free_balance': MagicMock(amount=Decimal("1000")),
        'realized_pnl': MagicMock(amount=Decimal("10")),
        'unrealized_pnl': MagicMock(amount=Decimal("5")),
    })

    result = strategy._check_risk(mock_order_book)

    assert result is False


# ========== 价格历史更新测试 ==========

def test_update_price_history(strategy):
    """测试价格历史更新"""
    initial_len = len(strategy._price_history)

    # 添加价格
    strategy._update_price_history(Decimal("0.60"))

    assert len(strategy._price_history) == initial_len + 1


def test_update_price_history_truncation(strategy):
    """测试价格历史截断"""
    strategy.volatility_window = 10

    # 添加超过限制的价格
    for i in range(50):
        strategy._update_price_history(Decimal(str(i * 0.01)))

    # 应该被截断
    assert len(strategy._price_history) <= strategy.volatility_window * 2


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
