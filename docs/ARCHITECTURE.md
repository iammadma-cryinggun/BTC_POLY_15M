# Polymarket V2 架构设计

> **核心理念**: 100% 利用 NautilusTrader 工具套件，不重复造轮子
>
> **日期**: 2026-01-28

---

## 📋 目录

1. [架构原则](#架构原则)
2. [NautilusTrader 层次利用](#nautilustrader-层次利用)
3. [核心组件设计](#核心组件设计)
4. [数据流设计](#数据流设计)
5. [策略基类设计](#策略基类设计)

---

## 🎯 架构原则

### **1. 框架优先原则**

```python
# ✅ 优先使用 NautilusTrader 提供的功能
portfolio = self.cache.portfolio()
account = self.cache.account_for_venue("POLYMARKET")

# ❌ 不重复造轮子
self.portfolio = {...}  # 不需要
self.account = {...}    # 不需要
```

### **2. 职责分离原则**

```
┌─────────────────────────────────────┐
│  NautilusTrader 框架（工具层）      │
│  - 数据收集和管理                   │
│  - 订单执行和路由                   │
│  - 仓位管理（Portfolio）            │
│  - 盈亏计算（BettingAccount）       │
│  - 风险检查（RiskEngine）           │
│  - 回测引擎（BacktestEngine）       │
└─────────────────────────────────────┘
            ↓ 提供能力
┌─────────────────────────────────────┐
│  我们的策略（逻辑层）                │
│  - 何时交易（信号生成）             │
│  - 交易什么（订单参数）             │
│  - 风险偏好（配置参数）             │
└─────────────────────────────────────┘
```

### **3. 平滑过渡原则**

```python
# ✅ 支持 paper → portfolio → live 的平滑过渡
config = StrategyConfig(
    portfolio_mode="paper",    # 模拟模式
    # portfolio_mode="both",  # 双轨对比
    # portfolio_mode="portfolio",  # 真实交易
)
```

---

## 🏗️ NautilusTrader 层次利用

### **第 1 层：数据层（Data Layer）** ✅

```python
class MyStrategy(Strategy):
    def on_start(self):
        # ✅ 使用框架的数据订阅
        self.subscribe_order_book_deltas(
            self.instrument.id,
            BookType.L2_MBP
        )

        self.subscribe_quote_ticks(self.instrument.id)
        self.subscribe_trade_ticks(self.instrument.id)

    def on_order_book(self, order_book):
        # ✅ 框架自动维护订单簿
        bids = order_book.bids()
        asks = order_book.asks()
        mid = order_book.midpoint()

        # 我们只需要做决策
        if self.should_trade(mid):
            self.execute_trade()
```

**我们负责**: 信号生成（何时交易）
**框架负责**: 数据收集、订单簿维护

---

### **第 2 层：执行层（Execution Layer）** ✅

```python
class MyStrategy(Strategy):
    def execute_trade(self):
        # ✅ 使用框架的 OrderFactory
        order = self.order_factory.limit(
            instrument_id=self.instrument.id,
            price=Price.from_str("0.50"),
            order_side=OrderSide.BUY,
            quantity=Quantity.from_int(20),
            post_only=False,
            time_in_force=TimeInForce.FOK,  # Polymarket 必需
        )

        # ✅ 使用框架的执行引擎
        self.submit_order(order)

    def on_order_filled(self, event):
        # ✅ 框架自动处理订单状态
        self.log.info(
            f"成交: {event.last_qty} @ {event.last_px}, "
            f"手续费: {event.commission}"
        )
```

**我们负责**: 订单参数（交易什么）
**框架负责**: 订单路由、状态管理、成交匹配

---

### **第 3 层：Portfolio 层（Portfolio Layer）** ⭐⭐⭐ 关键改进

```python
# ❌ 旧方式：自己维护仓位
class OldStrategy(Strategy):
    def __init__(self):
        self.paper_position_side = None
        self.paper_position_qty = Decimal("0")
        self.paper_entry_price = None

    def on_order_filled(self, event):
        if event.order_side == BUY:
            self.paper_position_side = "LONG"
            self.paper_position_qty += event.last_qty
            self.paper_entry_price = event.last_px

# ✅ 新方式：使用 Portfolio
class NewStrategy(Strategy):
    def on_order_filled(self, event):
        # Portfolio 自动维护仓位
        portfolio = self.cache.portfolio()
        position = portfolio.position(self.instrument_id)

        if position:
            self.log.info(
                f"仓位更新:\n"
                f"  方向: {position.side}\n"
                f"  数量: {position.quantity}\n"
                f"  入场价: {position.avg_px_open}\n"
                f"  当前价: {position.avg_px_current}\n"
                f"  未实现盈亏: {position.unrealized_pnl()}\n"
                f"  已实现盈亏: {position.realized_pnl}"
            )
```

**我们负责**: 不需要维护仓位！
**框架负责**:
- 仓位管理
- 开仓/平仓/反转
- 盈亏计算
- 历史记录

---

### **第 4 层：Accounting 层（Accounting Layer）** ⭐⭐⭐ 关键改进

```python
# ❌ 旧方式：自己计算盈亏
class OldStrategy(Strategy):
    def calculate_pnl(self):
        if self.paper_position_side == "LONG":  # YES
            roi = (current_price - entry_price) / entry_price
            pnl = roi * entry_price * quantity
        else:  # NO
            roi = (entry_price - current_price) / entry_price
            pnl = roi * entry_price * quantity
        return pnl

# ✅ 新方式：使用 BettingAccount
class NewStrategy(Strategy):
    def get_account_summary(self):
        # BettingAccount 自动处理 YES/NO 逻辑
        account = self.cache.account_for_venue("POLYMARKET")

        # BettingAccount 自动计算：
        # - YES: stake=qty*price, liability=0
        # - NO: stake=qty*(1-price), liability=qty*(1-price)

        return {
            'total_balance': account.balance_total(),
            'locked_balance': account.balance_locked(),
            'free_balance': account.balance_free(),
            'realized_pnl': account.realized_pnl(),
            'unrealized_pnl': account.unrealized_pnl(),
        }
```

**我们负责**: 不需要计算盈亏！
**框架负责**:
- YES/NO 代币的特殊逻辑
- stake, liability, payoff 计算
- 已实现/未实现盈亏
- 余额锁定

---

### **第 5 层：风险层（Risk Layer）** ⭐⭐⭐ 关键改进

```python
# ❌ 旧方式：自己检查风险
class OldStrategy(Strategy):
    def check_risk(self, order):
        account = self.cache.account_for_venue("POLYMARKET")
        free_balance = account.balance_free_total()

        required = order.quantity * order.price
        if free_balance < required:
            self.log.warning("余额不足")
            return False

        return True

# ✅ 新方式：配置 RiskEngine
from nautilus_trader.config import RiskEngineConfig

config = RiskEngineConfig(
    max_order_submit_rate=10,  # 每秒最多10个订单
    max_order_modify_rate=20,
    max_notional_per_order={
        instrument_id: Decimal("100.00")
    },
    bypass_check=False,  # 启用风险检查
)

# RiskEngine 自动检查：
# 1. 价格有效性（price > 0, 精度匹配）
# 2. 数量有效性（min <= qty <= max, 精度匹配）
# 3. 余额充足（调用 BettingAccount.calculate_balance_locked()）
# 4. 订单限流

class NewStrategy(Strategy):
    def execute_trade(self):
        order = self.order_factory.limit(...)

        # 框架自动风险检查
        self.submit_order(order)

        # 如果检查失败，会收到 on_order_rejected 事件
```

**我们负责**: 配置风险参数
**框架负责**:
- 预交易检查
- 订单限流
- 余额验证
- 自动拒绝

---

### **第 6 层：回测层（Backtest Layer）** ⭐⭐⭐ 关键改进

```python
# ❌ 旧方式：自己写回测引擎
# backtest_three_locks_official.py (几百行代码)

# ✅ 新方式：使用 BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.modules import PolymarketVenue
from nautilus_trader.config import BacktestRunConfig

def run_backtest(strategy_config, data_path):
    # 创建回测引擎
    engine = BacktestEngine(
        venue=[PolymarketVenue()],
        data_clients=[...],
        config=BacktestRunConfig(
            strategy_id=strategy_config.strategy_id,
            instrument_id=strategy_config.instrument_id,
        )
    )

    # 添加策略
    engine.add_strategy(
        strategy=EventDrivenStrategy(config=strategy_config)
    )

    # 运行回测
    result = engine.run()

    # 分析结果
    return {
        'total_trades': result.stats['total_trades'],
        'win_rate': result.stats['win_rate'],
        'total_pnl': result.stats['total_pnl'],
        'max_drawdown': result.stats['max_drawdown'],
        'sharpe_ratio': result.stats['sharpe_ratio'],
    }
```

**我们负责**: 策略逻辑
**框架负责**:
- 历史数据回放
- 订单模拟
- 滑点和手续费
- 性能指标计算

---

## 🧩 核心组件设计

### **组件 1: BaseStrategy（基础策略类）**

```python
# strategies/base_strategy.py

from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.portfolio import Portfolio

class BaseStrategy(Strategy):
    """
    基础策略类

    封装常用功能，确保正确使用 NautilusTrader API
    """

    def __init__(self, config):
        super().__init__(config)

        # ✅ 使用框架的 Portfolio
        # 不再自己维护 paper_position

    # ========== 仓位查询（使用 Portfolio） ==========

    def get_current_position(self):
        """获取当前仓位（使用 Portfolio）"""
        portfolio = self.cache.portfolio()
        position = portfolio.position(self.instrument_id)

        if position:
            return {
                'side': position.side,
                'quantity': position.quantity,
                'entry_price': position.avg_px_open,
                'current_price': position.avg_px_current,
                'unrealized_pnl': position.unrealized_pnl(),
                'realized_pnl': position.realized_pnl,
            }
        return None

    # ========== 账户查询（使用 BettingAccount） ==========

    def get_account_info(self):
        """获取账户信息（使用 BettingAccount）"""
        account = self.cache.account_for_venue("POLYMARKET")

        return {
            'total_balance': account.balance_total(),
            'free_balance': account.balance_free(),
            'locked_balance': account.balance_locked(),
            'realized_pnl': account.realized_pnl(),
            'unrealized_pnl': account.unrealized_pnl(),
        }

    # ========== 风险检查（使用 RiskEngine） ==========

    def can_submit_order(self, order):
        """
        检查是否可以提交订单

        注意：RiskEngine 会自动检查，这里是额外检查
        """
        # 检查是否有开放仓位
        positions = self.cache.positions_open(
            instrument_id=self.instrument.id,
            strategy_id=self.id
        )

        if len(positions) >= self.config.max_positions:
            self.log.warning("已达最大持仓数")
            return False

        return True

    # ========== 订单提交（使用框架） ==========

    def submit_order_with_check(self, order):
        """提交订单并进行额外检查"""
        if self.can_submit_order(order):
            self.submit_order(order)
        else:
            self.log.warning(f"订单未通过额外检查: {order.client_order_id}")
```

### **组件 2: RiskConfig（风险配置）**

```python
# config/risk_config.py

from nautilus_trader.config import RiskEngineConfig
from decimal import Decimal

def get_risk_config(instrument_id):
    """
    获取风险配置

    充分利用 RiskEngine 的能力
    """
    return RiskEngineConfig(
        # 订单限流
        max_order_submit_rate=10,  # 每秒最多10个订单
        max_order_modify_rate=20,  # 每秒最多20个修改

        # 最大名义价值
        max_notional_per_order={
            instrument_id: Decimal("100.00")  # 单订单最多100 USDC
        },

        # 不绕过风险检查
        bypass_check=False,

        # 调试模式
        debug=True,
    )
```

### **组件 3: BacktestRunner（回测运行器）**

```python
# backtests/run_backtest.py

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.modules import PolymarketVenue

class BacktestRunner:
    """
    回测运行器

    使用 NautilusTrader 的 BacktestEngine
    """

    def __init__(self, config):
        self.config = config

    def run(self, strategy_class, data_path):
        # 创建回测引擎
        engine = BacktestEngine(
            venue=[PolymarketVenue()],
            data_clients=self._load_data(data_path),
            config=self.config.backtest_config,
        )

        # 添加策略
        engine.add_strategy(
            strategy=strategy_class(config=self.config.strategy_config)
        )

        # 运行回测
        result = engine.run()

        # 返回结果
        return BacktestResult(result)
```

---

## 📊 数据流设计

### **实时交易数据流**

```
Polymarket CLOB
    ↓ WebSocket
NautilusTrader Adapter
    ↓ 解析
DataEngine
    ↓ 验证
Cache（数据缓存）
    ↓ 触发事件
Strategy.on_order_book()
    ↓ 决策
Strategy.submit_order()
    ↓ 风险检查
RiskEngine（自动）
    ↓ 通过
ExecutionEngine
    ↓ 路由
Adapter
    ↓ 发送
Polymarket CLOB
    ↓ 成交
OrderFilled 事件
    ↓ 更新
Portfolio（自动更新仓位）
Accounting（BettingAccount 自动计算盈亏）
```

### **回测数据流**

```
历史数据文件
    ↓ 读取
DataClient
    ↓ 回放
BacktestEngine
    ↓ 模拟
Strategy.on_order_book()
    ↓ 决策
Strategy.submit_order()
    ↓ 模拟执行
BacktestExecutionEngine
    ↓ 模拟成交
Portfolio（更新仓位）
Accounting（计算盈亏）
    ↓ 统计
BacktestResult
```

---

## 🎯 策略开发流程

### **开发流程**

```
1. 设计策略逻辑
   ↓
2. 继承 BaseStrategy
   ↓
3. 实现 on_order_book() / on_quote_tick()
   ↓
4. 使用 Portfolio 查询仓位
   ↓
5. 使用 BettingAccount 查询余额
   ↓
6. 提交订单（RiskEngine 自动检查）
   ↓
7. 使用 BacktestEngine 回测
   ↓
8. 分析结果，优化参数
   ↓
9. Paper Trading 测试
   ↓
10. Portfolio 双轨运行
    ↓
11. 真实交易
```

### **最佳实践**

1. **永远使用 Portfolio**，不自己维护仓位
2. **永远使用 BettingAccount**，不自己计算盈亏
3. **配置 RiskEngine**，不自己检查风险
4. **使用 BacktestEngine**，不自己写回测
5. **查询 Cache**，不自己缓存数据
6. **使用 OrderFactory**，不自己创建订单

---

## 📚 参考资料

- **NautilusTrader 文档**: https://docs.nautilustrader.io
- **BettingAccount 源码**: `nautilus_trader/accounting/accounts/betting.pyx`
- **Portfolio 源码**: `nautilus_trader/portfolio/portfolio.pyx`
- **RiskEngine 源码**: `nautilus_trader/risk/engine.pyx`
- **BacktestEngine 源码**: `nautilus_trader/backtest/engine.pyx`

---

**版本**: v1.0
**日期**: 2026-01-28
**作者**: Claude Code
