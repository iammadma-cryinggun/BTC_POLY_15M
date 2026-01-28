"""
风险配置 - 充分利用 NautilusTrader RiskEngine

核心原则：
1. 使用 RiskEngine 进行所有风险检查
2. 不在策略中重复实现风险逻辑
3. 配置合理的限制参数
"""

from nautilus_trader.config import RiskEngineConfig
from nautilus_trader.model.identifiers import InstrumentId
from decimal import Decimal


def get_polymarket_risk_config(instrument_id: InstrumentId):
    """
    获取 Polymarket 风险配置

    充分利用 RiskEngine 的能力：
    - 订单限流（防止过度交易）
    - 最大名义价值（资金管理）
    - 价格和数量验证（防止无效订单）

    Args:
        instrument_id: InstrumentId 对象

    Returns:
        RiskEngineConfig
    """
    return RiskEngineConfig(
        # ========== 订单限流 ==========
        # Polymarket 低流动性，限制订单速率
        max_order_submit_rate=10,   # 每秒最多10个订单
        max_order_modify_rate=20,   # 每秒最多20个修改

        # ========== 最大名义价值 ==========
        # 单订单最大金额（资金管理）
        max_notional_per_order={
            instrument_id: Decimal("100.00")  # 单订单最多100 USDC
        },

        # ========== 风险检查开关 ==========
        bypass_check=False,  # 启用所有风险检查

        # ========== 调试模式 ==========
        debug=True,  # 记录详细的检查日志
    )


# ========== 策略级别的风险配置 ==========

class StrategyRiskConfig:
    """
    策略级别的风险配置

    注意：这些是策略的额外限制
    RiskEngine 会进行基础检查
    """

    def __init__(
        self,
        max_positions: int = 1,              # 最大持仓数
        min_free_balance: Decimal = Decimal("10.00"),  # 最小保留余额
        max_position_size: Decimal = Decimal("100"),   # 单笔最大仓位
        max_daily_pnl_loss: Decimal = Decimal("-50.00"),  # 日最大亏损
    ):
        self.max_positions = max_positions
        self.min_free_balance = min_free_balance
        self.max_position_size = max_position_size
        self.max_daily_pnl_loss = max_daily_pnl_loss

    def __repr__(self):
        return (
            f"StrategyRiskConfig(\n"
            f"  max_positions={self.max_positions},\n"
            f"  min_free_balance={self.min_free_balance},\n"
            f"  max_position_size={self.max_position_size},\n"
            f"  max_daily_pnl_loss={self.max_daily_pnl_loss}\n"
            f")"
        )


# ========== 预设配置 ==========

def get_conservative_config(instrument_id: InstrumentId):
    """保守配置（低风险）"""
    return {
        'risk_engine': get_polymarket_risk_config(instrument_id),
        'strategy': StrategyRiskConfig(
            max_positions=1,
            min_free_balance=Decimal("50.00"),  # 保留50 USDC
            max_position_size=Decimal("20"),     # 单笔最多20个
            max_daily_pnl_loss=Decimal("-20.00"),  # 日最大亏损20 USDC
        ),
    }


def get_moderate_config(instrument_id: InstrumentId):
    """适中配置（中等风险）"""
    return {
        'risk_engine': get_polymarket_risk_config(instrument_id),
        'strategy': StrategyRiskConfig(
            max_positions=2,
            min_free_balance=Decimal("20.00"),  # 保留20 USDC
            max_position_size=Decimal("50"),     # 单笔最多50个
            max_daily_pnl_loss=Decimal("-50.00"),  # 日最大亏损50 USDC
        ),
    }


def get_aggressive_config(instrument_id: InstrumentId):
    """激进配置（高风险）"""
    return {
        'risk_engine': get_polymarket_risk_config(instrument_id),
        'strategy': StrategyRiskConfig(
            max_positions=3,
            min_free_balance=Decimal("10.00"),  # 保留10 USDC
            max_position_size=Decimal("100"),    # 单笔最多100个
            max_daily_pnl_loss=Decimal("-100.00"),  # 日最大亏损100 USDC
        ),
    }
