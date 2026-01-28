"""
简单示例策略 - 展示如何正确使用 NautilusTrader 工具套件

这是一个教学示例，展示：
1. 如何使用 Portfolio 查询仓位
2. 如何使用 BettingAccount 查询余额
3. 如何提交订单（RiskEngine 自动检查）
4. 如何处理订单事件

注意：这不是一个盈利策略，只是架构示例！
"""

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.enums import OrderSide, BookType
from nautilus_trader.model.orders import OrderList
from nautilus_trader.model.identifiers import OrderListId
from nautilus_trader.model.orderbook import OrderBook
from nautilus_trader.core.decimal import Decimal

from .base_strategy import BaseStrategy


class SimpleExampleStrategy(BaseStrategy):
    """
    简单示例策略

    策略逻辑：
    - 当中间价 < 下限时买入
    - 当中间价 > 上限时卖出
    - 使用 OCO 订单设置止盈止损

    注意：这只是架构示例，不是盈利策略！
    """

    # ========== 参数配置 ==========
    # 可以通过 config 传入

    # 价格阈值
    LOWER_THRESHOLD = Decimal("0.40")  # 买入阈值
    UPPER_THRESHOLD = Decimal("0.60")  # 卖出阈值

    # 仓位参数
    POSITION_SIZE = Decimal("10")      # 每次交易10个

    # 止盈止损
    TAKE_PROFIT_PCT = Decimal("0.10")  # 10% 止盈
    STOP_LOSS_PCT = Decimal("0.05")    # 5% 止损

    # 交易间隔
    TRADE_INTERVAL_NS = 60 * 1_000_000_000  # 60秒

    # ========== 内部状态 ==========

    def __init__(self, config):
        super().__init__(config)

        self._last_trade_time_ns = 0
        self._entry_price = None

    # ========== 数据处理 ==========

    def on_order_book(self, order_book: OrderBook):
        """
        处理订单簿更新

        这是策略的核心逻辑
        """
        # 1. 获取中间价
        mid = order_book.midpoint()
        if not mid:
            return

        mid_price = Decimal(mid)

        # 2. 检查交易间隔
        now_ns = self.clock.timestamp_ns()
        if now_ns - self._last_trade_time_ns < self.TRADE_INTERVAL_NS:
            return

        # 3. 根据当前仓位决定操作
        position = self.get_current_position()

        if position is None:
            # 无仓位，检查是否开仓
            self._check_entry(mid_price)
        elif position['side'] == 'LONG':
            # 有多头，检查是否平仓
            self._check_exit_long(mid_price, position)
        elif position['side'] == 'SHORT':
            # 有空头，检查是否平仓
            self._check_exit_short(mid_price, position)

    # ========== 开仓逻辑 ==========

    def _check_entry(self, mid_price: Decimal):
        """检查是否开仓"""
        # 价格过低 → 买入
        if mid_price < self.LOWER_THRESHOLD:
            self.log.info(
                f"📉 价格 {mid_price} < 下限 {self.LOWER_THRESHOLD}，"
                f"考虑买入"
            )

            # 检查余额
            free_balance = self.get_free_balance()

            if free_balance < Decimal("20"):
                self.log.warning("余额不足，不交易")
                return

            # 提交买单
            self._enter_long(mid_price)

        # 价格过高 → 卖出
        elif mid_price > self.UPPER_THRESHOLD:
            self.log.info(
                f"📈 价格 {mid_price} > 上限 {self.UPPER_THRESHOLD}，"
                f"考虑卖出"
            )

            # 检查余额
            free_balance = self.get_free_balance()

            if free_balance < Decimal("20"):
                self.log.warning("余额不足，不交易")
                return

            # 提交卖单
            self._enter_short(mid_price)

    # ========== 平仓逻辑 ==========

    def _check_exit_long(self, mid_price: Decimal, position: dict):
        """检查是否平多头"""
        entry_price = Decimal(position['entry_price'])
        unrealized_pnl = Decimal(position['unrealized_pnl'])

        # 计算盈亏百分比
        roi = (mid_price - entry_price) / entry_price

        self.log.info(
            f"📊 多头仓位: 入场={entry_price}, "
            f"当前={mid_price}, ROI={roi*100:.2f}%"
        )

        # 止盈
        if roi >= self.TAKE_PROFIT_PCT:
            self.log.info(f"🎯 止盈: ROI={roi*100:.2f}%")
            self._close_position()

        # 止损
        elif roi <= -self.STOP_LOSS_PCT:
            self.log.info(f"🛑 止损: ROI={roi*100:.2f}%")
            self._close_position()

        # 价格回到上限以上
        elif mid_price > self.UPPER_THRESHOLD:
            self.log.info(f"📈 价格回到上限以上，平仓")
            self._close_position()

    def _check_exit_short(self, mid_price: Decimal, position: dict):
        """检查是否平空头"""
        entry_price = Decimal(position['entry_price'])
        unrealized_pnl = Decimal(position['unrealized_pnl'])

        # 计算盈亏百分比
        roi = (entry_price - mid_price) / entry_price

        self.log.info(
            f"📊 空头仓位: 入场={entry_price}, "
            f"当前={mid_price}, ROI={roi*100:.2f}%"
        )

        # 止盈
        if roi >= self.TAKE_PROFIT_PCT:
            self.log.info(f"🎯 止盈: ROI={roi*100:.2f}%")
            self._close_position()

        # 止损
        elif roi <= -self.STOP_LOSS_PCT:
            self.log.info(f"🛑 止损: ROI={roi*100:.2f}%")
            self._close_position()

        # 价格回到下限以下
        elif mid_price < self.LOWER_THRESHOLD:
            self.log.info(f"📉 价格回到下限以下，平仓")
            self._close_position()

    # ========== 执行交易 ==========

    def _enter_long(self, mid_price: Decimal):
        """开多头仓位"""
        # 使用 FOK 限价单
        # 价格略高于中间价（提高成交概率）
        price = mid_price * Decimal("1.01")

        self.submit_limit_order(
            side=OrderSide.BUY,
            quantity=Quantity.from_int(self.POSITION_SIZE),
            price=Price.from_str(str(price)),
            time_in_force=TimeInForce.FOK,
        )

        self._last_trade_time_ns = self.clock.timestamp_ns()

    def _enter_short(self, mid_price: Decimal):
        """开空头仓位"""
        # 使用 FOK 限价单
        # 价格略低于中间价（提高成交概率）
        price = mid_price * Decimal("0.99")

        self.submit_limit_order(
            side=OrderSide.SELL,
            quantity=Quantity.from_int(self.POSITION_SIZE),
            price=Price.from_str(str(price)),
            time_in_force=TimeInForce.FOK,
        )

        self._last_trade_time_ns = self.clock.timestamp_ns()

    def _close_position(self):
        """平仓"""
        position = self.get_current_position()

        if not position:
            return

        # 使用市价单快速平仓
        if position['side'] == 'LONG':
            side = OrderSide.SELL
        else:
            side = OrderSide.BUY

        self.submit_market_order(
            side=side,
            quantity=Quantity.from_int(position['quantity']),
        )

        self._last_trade_time_ns = self.clock.timestamp_ns()

    # ========== 事件处理（重写父类方法以添加自定义逻辑） ==========

    def on_order_filled(self, event):
        """订单成交"""
        super().on_order_filled(event)

        # 如果是开仓成交，记录入场价
        position = self.get_current_position()
        if position and position['entry_price']:
            self._entry_price = Decimal(position['entry_price'])

            # 设置止盈止损订单（使用 OCO）
            # self._set_stop_orders()

    def _set_stop_orders(self):
        """设置止盈止损订单（使用 OCO）"""
        position = self.get_current_position()
        if not position:
            return

        entry_price = Decimal(position['entry_price'])

        # 计算止盈止损价
        if position['side'] == 'LONG':
            # 多头：止盈在上方，止损在下方
            tp_price = entry_price * (Decimal("1") + self.TAKE_PROFIT_PCT)
            sl_price = entry_price * (Decimal("1") - self.STOP_LOSS_PCT)

            take_profit = self.order_factory.limit(
                instrument_id=self.instrument.id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_int(position['quantity']),
                price=Price.from_str(str(tp_price)),
                time_in_force=TimeInForce.GTC,  # OCO 需要 GTC
            )

            stop_loss = self.order_factory.stop_market(
                instrument_id=self.instrument.id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_int(position['quantity']),
                trigger_price=Price.from_str(str(sl_price)),
            )

        else:  # SHORT
            # 空头：止盈在下方，止损在上方
            tp_price = entry_price * (Decimal("1") - self.TAKE_PROFIT_PCT)
            sl_price = entry_price * (Decimal("1") + self.STOP_LOSS_PCT)

            take_profit = self.order_factory.limit(
                instrument_id=self.instrument.id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_int(position['quantity']),
                price=Price.from_str(str(tp_price)),
                time_in_force=TimeInForce.GTC,
            )

            stop_loss = self.order_factory.stop_market(
                instrument_id=self.instrument.id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_int(position['quantity']),
                trigger_price=Price.from_str(str(sl_price)),
            )

        # 提交 OCO 订单
        self.submit_oco_orders(take_profit, stop_loss)

        self.log.info("✅ 止盈止损订单已设置（OCO）")
