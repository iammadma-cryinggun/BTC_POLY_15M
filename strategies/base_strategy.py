"""
基础策略类 - 充分利用 NautilusTrader 工具套件

核心原则：
1. 不重复造轮子
2. 使用 Portfolio 管理仓位
3. 使用 BettingAccount 计算盈亏
4. 使用 RiskEngine 检查风险
5. 使用 Cache 获取数据
"""

from decimal import Decimal

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import InstrumentId, Venue
from nautilus_trader.model.orders import Order
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.objects import Quantity, Price


class BaseStrategy(Strategy):
    """
    基础策略类

    封装常用功能，确保正确使用 NautilusTrader API
    充分利用 Portfolio、BettingAccount、RiskEngine 等框架能力
    """

    # ========== 生命周期管理 ==========

    def on_start(self):
        """策略启动时调用"""
        self.log.info("=" * 80)
        self.log.info(f"策略启动: {self.id}")
        self.log.info("=" * 80)

        # 获取 Instrument
        self.instrument = self.cache.instrument(self.instrument_id)

        if not self.instrument:
            self.log.error(f"Instrument not found: {self.instrument_id}")
            return

        self.log.info(
            f"\n"
            f"交易品种:\n"
            f"  ID: {self.instrument.id}\n"
            f"  基础货币: {self.instrument.base_currency}\n"
            f"  计价货币: {self.instrument.quote_currency}\n"
            f"  价格精度: {self.instrument.price_precision}\n"
            f"  数量精度: {self.instrument.size_precision}\n"
            f"  最小数量: {self.instrument.min_quantity}\n"
            f"  最大数量: {self.instrument.max_quantity}\n"
        )

        # 订阅数据
        self.subscribe_data()

        # 打印初始状态
        self.print_account_summary()
        self.print_position_summary()

    def on_stop(self):
        """策略停止时调用"""
        self.log.info("=" * 80)
        self.log.info(f"策略停止: {self.id}")
        self.log.info("=" * 80)

        # 打印最终状态
        self.print_account_summary()
        self.print_position_summary()

        # 取消所有订单
        self.cancel_all_orders(self.instrument_id)

    # ========== 数据订阅 ==========

    def subscribe_data(self):
        """订阅市场数据"""
        # 订阅订单簿增量（推荐）
        self.subscribe_order_book_deltas(
            self.instrument.id,
            BookType.L2_MBP
        )

        # 订阅报价
        self.subscribe_quote_ticks(self.instrument.id)

        # 订阅成交
        self.subscribe_trade_ticks(self.instrument.id)

        self.log.info("✅ 数据订阅完成")

    # ========== Portfolio 相关方法 ==========

    def get_current_position(self):
        """
        获取当前仓位信息

        ✅ 使用 Portfolio 系统，不自己维护 paper_position

        Returns:
            dict | None: 仓位信息字典，如果无仓位返回 None
        """
        portfolio = self.cache.portfolio()
        position = portfolio.position(self.instrument_id)

        if not position:
            return None

        return {
            'side': str(position.side),  # 'LONG' | 'SHORT' | 'FLAT'
            'quantity': Decimal(position.quantity),
            'entry_price': Decimal(position.avg_px_open) if position.avg_px_open else None,
            'current_price': Decimal(position.avg_px_current) if position.avg_px_current else None,
            'unrealized_pnl': Decimal(position.unrealized_pnl()),
            'realized_pnl': Decimal(position.realized_pnl),
        }

    def has_open_position(self):
        """检查是否有开放仓位"""
        position = self.get_current_position()
        return position is not None and position['quantity'] > 0

    def is_long(self):
        """检查是否持有多头仓位"""
        position = self.get_current_position()
        return position is not None and position['side'] == 'LONG'

    def is_short(self):
        """检查是否持有空头仓位"""
        position = self.get_current_position()
        return position is not None and position['side'] == 'SHORT'

    # ========== BettingAccount 相关方法 ==========

    def get_account_info(self):
        """
        获取账户信息

        ✅ 使用 BettingAccount，不自己计算盈亏
        BettingAccount 自动处理 YES/NO 代币的特殊逻辑

        Returns:
            dict: 账户信息字典
        """
        account = self.cache.account_for_venue(Venue("POLYMARKET"))

        if not account:
            self.log.error("账户未找到")
            return None

        return {
            'total_balance': Money(account.balance_total(), account.currency),
            'free_balance': Money(account.balance_free(), account.currency),
            'locked_balance': Money(account.balance_locked(), account.currency),
            'realized_pnl': Money(account.realized_pnl(), account.currency),
            'unrealized_pnl': Money(account.unrealized_pnl(), account.currency),
        }

    def get_free_balance(self):
        """获取可用余额"""
        account_info = self.get_account_info()
        return account_info['free_balance'] if account_info else Decimal('0')

    # ========== 订单簿相关方法 ==========

    def get_order_book(self):
        """
        获取订单簿

        ✅ 使用 Cache，不自己维护

        Returns:
            OrderBook | None
        """
        return self.cache.order_book(self.instrument_id)

    def get_best_bid(self):
        """获取最优买价"""
        book = self.get_order_book()
        return book.best_bid_price() if book else None

    def get_best_ask(self):
        """获取最优卖价"""
        book = self.get_order_book()
        return book.best_ask_price() if book else None

    def get_midpoint(self):
        """获取中间价"""
        book = self.get_order_book()
        return book.midpoint() if book else None

    # ========== 风险检查相关方法 ==========

    def can_submit_order(self, order):
        """
        检查是否可以提交订单

        注意：RiskEngine 会自动检查基础风险
        这里是策略级别的额外检查

        Args:
            order: Order 对象

        Returns:
            bool: 是否可以提交
        """
        # 检查最大持仓数
        positions = self.cache.positions_open(
            instrument_id=self.instrument.id,
            strategy_id=self.id
        )

        if len(positions) >= self.config.max_positions:
            self.log.warning(f"已达最大持仓数: {self.config.max_positions}")
            return False

        # 检查最小余额
        free_balance = self.get_free_balance()
        min_balance = self.config.min_free_balance

        if free_balance < min_balance:
            self.log.warning(
                f"可用余额不足: {free_balance} < {min_balance}"
            )
            return False

        return True

    # ========== 订单提交相关方法 ==========

    def submit_order_with_check(self, order):
        """
        提交订单并进行额外检查

        Args:
            order: Order 对象
        """
        if self.can_submit_order(order):
            self.submit_order(order)
            self.log.info(f"✅ 订单已提交: {order.client_order_id}")
        else:
            self.log.warning(
                f"❌ 订单未通过额外检查: {order.client_order_id}"
            )

    def submit_market_order(self, side, quantity):
        """
        提交市价单

        Args:
            side: OrderSide.BUY | OrderSide.SELL
            quantity: Quantity
        """
        order = self.order_factory.market(
            instrument_id=self.instrument.id,
            order_side=side,
            quantity=quantity,
        )

        self.submit_order_with_check(order)

    def submit_limit_order(
        self,
        side,
        quantity,
        price,
        post_only=False,
        time_in_force=TimeInForce.FOK,
    ):
        """
        提交限价单

        Args:
            side: OrderSide.BUY | OrderSide.SELL
            quantity: Quantity
            price: Price
            post_only: bool
            time_in_force: TimeInForce
        """
        order = self.order_factory.limit(
            instrument_id=self.instrument.id,
            order_side=side,
            quantity=quantity,
            price=price,
            post_only=post_only,
            time_in_force=time_in_force,
        )

        self.submit_order_with_check(order)

    # ========== OCO/OTO 订单相关方法 ==========

    def submit_oco_orders(self, order1, order2):
        """
        提交 OCO（One-Cancels-Other）订单

        一个成交，另一个自动取消

        Args:
            order1: Order 对象
            order2: Order 对象
        """
        order_list = OrderList(
            orders=[order1, order2],
            order_list_id=OrderListId(f"OCO_{self.clock.timestamp_ns()}"),
            oco=True,
        )

        self.submit_order_list(order_list)
        self.log.info(f"✅ OCO 订单已提交: {order_list.order_list_id}")

    # ========== 事件处理 ==========

    def on_order_filled(self, event):
        """订单成交时调用"""
        self.log.info(
            f"\n"
            f"{'='*60}\n"
            f"[OK] Order Filled\n"
            f"{'='*60}\n"
            f"Order ID: {event.client_order_id}\n"
            f"Venue Order ID: {event.venue_order_id}\n"
            f"Side: {event.order_side}\n"
            f"Fill Price: {event.last_px}\n"
            f"成交数量: {event.last_qty}\n"
            f"手续费: {event.commission}\n"
            f"{'='*60}"
        )

        # 打印仓位更新（Portfolio 自动维护）
        self.print_position_summary()

    def on_order_rejected(self, event):
        """订单被拒绝时调用"""
        self.log.error(
            f"\n"
            f"{'='*60}\n"
            f"❌ 订单被拒绝\n"
            f"{'='*60}\n"
            f"订单ID: {event.client_order_id}\n"
            f"拒绝原因: {event.reason}\n"
            f"{'='*60}"
        )

        # 分析拒绝原因
        if "insufficient" in event.reason.lower():
            self.log.error("💰 余额不足，请充值")

        elif "price" in event.reason.lower():
            self.log.error("📊 价格无效，检查价格设置")

        elif "quantity" in event.reason.lower():
            self.log.error("📊 数量无效，检查数量设置")

        elif "throttle" in event.reason.lower():
            self.log.error("⏱️ 订单速率过快，等待后重试")

    def on_order_canceled(self, event):
        """订单取消时调用"""
        self.log.info(
            f"🚫 订单取消: {event.client_order_id}, "
            f"取消数量: {event.rejected_qty}"
        )

    # ========== 打印辅助方法 ==========

    def print_account_summary(self):
        """打印账户摘要"""
        account_info = self.get_account_info()

        if not account_info:
            return

        self.log.info(
            f"\n"
            f"{'='*60}\n"
            f"💰 账户摘要\n"
            f"{'='*60}\n"
            f"总余额: {account_info['total_balance']}\n"
            f"可用余额: {account_info['free_balance']}\n"
            f"锁定余额: {account_info['locked_balance']}\n"
            f"已实现盈亏: {account_info['realized_pnl']}\n"
            f"未实现盈亏: {account_info['unrealized_pnl']}\n"
            f"{'='*60}"
        )

    def print_position_summary(self):
        """打印仓位摘要"""
        position = self.get_current_position()

        if not position:
            self.log.info("📊 当前无仓位")
            return

        self.log.info(
            f"\n"
            f"{'='*60}\n"
            f"📊 仓位摘要\n"
            f"{'='*60}\n"
            f"方向: {position['side']}\n"
            f"数量: {position['quantity']}\n"
            f"入场价: {position['entry_price']}\n"
            f"当前价: {position['current_price']}\n"
            f"未实现盈亏: {position['unrealized_pnl']}\n"
            f"已实现盈亏: {position['realized_pnl']}\n"
            f"{'='*60}"
        )

    def print_order_book_snapshot(self, depth=5):
        """打印订单簿快照"""
        book = self.get_order_book()

        if not book:
            self.log.warning("订单簿不可用")
            return

        self.log.info(f"\n{'='*60}\n订单簿快照 (前{depth}档)\n{'='*60}")

        # 卖单（从高到低）
        asks = book.asks()[:depth]
        for i, level in enumerate(reversed(asks)):
            self.log.info(
                f"  [{depth-i}] ASK: {level.price} x {level.size()}"
            )

        # 中间价
        mid = book.midpoint()
        if mid:
            self.log.info(f"  {'─'*40}\n  MID: {mid}\n  {'─'*40}")

        # 买单（从高到低）
        bids = book.bids()[:depth]
        for i, level in enumerate(bids):
            self.log.info(
                f"  [{i+1}] BID: {level.price} x {level.size()}"
            )

        self.log.info(f"{'='*60}")
