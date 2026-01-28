# NautilusTrader + Polymarket 基础设施深度分析

> **日期**: 2026-01-28
> **目的**: 深度理解三者关系，设计适配市场特性的策略

---

## 📋 目录

1. [NautilusTrader 基础设施能力](#1-nautilustrader-基础设施能力)
2. [Polymarket 市场机制](#2-polymarket-市场机制)
3. [BettingAccount 核心算法](#3-bettingaccount-核心算法)
4. [三者结合点](#4-三者结合点)
5. [能做什么 & 不能做什么](#5-能做什么--不能做什么)

---

## 1. NautilusTrader 基础设施能力

### **1.1 Polymarket 官方适配器** ⭐⭐⭐⭐⭐

#### **完整的基础设施**

```python
# 文件位置：
# nautilus_trader/adapters/polymarket/

PolymarketDataClient         # 数据客户端
PolymarketExecutionClient     # 执行客户端
PolymarketInstrumentProvider  # 品种提供者
PolymarketWebSocketClient     # WebSocket 客户端
```

#### **配置参数**

```python
class PolymarketDataClientConfig:
    # 认证
    private_key: str | None        # Polygon 钱包私钥
    signature_type: int = 0        # 0=EOA, 1=Email Proxy, 2=Browser Proxy
    funder: str | None             # 资金钱包地址

    # API 认证
    api_key: str | None
    api_secret: str | None
    passphrase: str | None

    # API 端点
    base_url_http: str = "https://clob.polymarket.com"
    base_url_ws: str

    # 行为配置
    update_instruments_interval_mins: 60  # 每60秒更新品种
    compute_effective_deltas: False      # 是否计算有效增量
    drop_quotes_missing_side: True       # 是否丢弃缺失方的报价

class PolymarketExecClientConfig:
    # 重试配置
    max_retries: int
    retry_delay_initial_ms: int
    retry_delay_max_ms: int

    # 订单确认
    ack_timeout_secs: 5.0           # 5秒确认超时

    # API 选择
    use_data_api: False             # 使用 CLOB API（稳定）
```

#### **核心能力**

| 能力 | 实现方式 | 说明 |
|------|---------|------|
| **WebSocket 数据流** | PolymarketDataClient | 实时订单簿、报价、成交 |
| **HTTP API** | py_clob_client.client.ClobClient | REST API 调用 |
| **订单执行** | PolymarketExecutionClient | 提交、取消订单 |
| **自动重连** | WebSocketClient | 连接断开自动重连 |
| **订单路由** | ExecutionEngine | 路由到 Polymarket CLOB |
| **状态同步** | Cache | 缓存订单、仓位、余额 |

---

### **1.2 BettingAccount - 专为二元预测市场设计** ⭐⭐⭐⭐⭐

#### **文件位置**
```python
nautilus_trader/accounting/accounts/betting.pyx
```

#### **核心算法**

```python
# ========== 下注额计算 ==========
cpdef stake(Quantity quantity, Price price):
    return quantity * (price - 1)

# ========== 责任（最大损失）计算 ==========
cpdef liability(Quantity quantity, Price price, OrderSide side):
    if side == OrderSide.SELL:  # 卖出 YES（做空）
        return quantity
    elif side == OrderSide.BUY:  # 买入 YES（做多）
        return stake(quantity, price)

# ========== 赢的盈亏计算 ==========
cpdef win_payoff(Quantity quantity, Price price, OrderSide side):
    if side == OrderSide.BUY:  # 买入 YES
        return stake(quantity, price)  # 赚 stake
    elif side == OrderSide.SELL:  # 卖出 YES
        return -stake(quantity, price)  # 赚 -stake

# ========== 输的盈亏计算 ==========
cpdef lose_payoff(Quantity quantity, OrderSide side):
    if side == OrderSide.BUY:  # 买入 YES 输了
        return -quantity  # 损失全部代币
    elif side == OrderSide.SELL:  # 卖出 YES 输了
        return quantity  # 赚全部代币

# ========== 敞口计算 ==========
cpdef exposure(Quantity quantity, Price price, OrderSide side):
    return win_payoff(quantity, price, side) - lose_payoff(quantity, side)
```

#### **实际例子**

假设：价格 = 0.60 (60%概率)，数量 = 100个

```python
# 场景1: 买入 YES（认为会发生）
# OrderSide.BUY, price=0.60, quantity=100

stake = 100 * (0.60 - 1) = -40 USDC
liability = stake = -40 USDC  # 最大损失40 USDC

if YES 赢了（价格→1.00）:
    win_payoff = stake = -40 USDC
    lose_payoff = -100
    net_profit = win_payoff - lose_payoff = -40 - (-100) = +60 USDC ✅

if YES 输了（价格→0.00）:
    win_payoff = stake = -40 USDC
    lose_payoff = -100
    net_profit = -40 - (-100) = -40 USDC ❌

# 场景2: 卖出 YES（做空白）
# OrderSide.SELL, price=0.60, quantity=100

stake = 100 * (0.60 - 1) = -40 USDC
liability = quantity = 100  # 最大损失100 USDC

if YES 赢了（价格→1.00）:
    win_payoff = -stake = +40 USDC
    lose_payoff = +100
    net_profit = 40 - 100 = -60 USDC ❌

if YES 输了（价格→0.00）:
    win_payoff = -stake = +40 USDC
    lose_payoff = +100
    net_profit = 40 - 100 = +40 USDC ✅
```

#### **余额锁定计算**

```python
cpdef Money calculate_balance_locked(
    self,
    Instrument instrument,
    OrderSide side,
    Quantity quantity,
    Price price,
):
    # 锁定金额 = 责任
    locked = liability(quantity, price, side)
    return Money(locked, instrument.quote_currency)

# 买入 YES: locked = stake = quantity * (price - 1)
# 卖出 YES: locked = quantity
```

---

### **1.3 Portfolio 系统** ⭐⭐⭐⭐⭐

#### **核心功能**

```python
# 查询仓位
portfolio = self.cache.portfolio()
position = portfolio.position(instrument_id)

# 仓位信息
position.side          # LONG | SHORT | FLAT
position.quantity      # 数量
position.avg_px_open   # 开仓均价
position.avg_px_current # 当前均价
position.realized_pnl  # 已实现盈亏
position.unrealized_pnl() # 未实现盈亏
```

#### **与 Paper Trading 的区别**

| 维度 | 旧方式（自己维护） | 新方式（Portfolio） |
|------|-----------------|------------------|
| **仓位数据** | `self.paper_position_side` | `position.side` |
| **数量** | `self.paper_position_qty` | `position.quantity` |
| **入场价** | `self.paper_entry_price` | `position.avg_px_open` |
| **盈亏** | 自己计算 | `position.realized_pnl` + `position.unrealized_pnl()` |
| **可靠性** | ❌ 容易出错 | ✅ 框架保证 |
| **实盘过渡** | ❌ 需要重写 | ✅ 无缝过渡 |

---

### **1.4 RiskEngine 风险管理** ⭐⭐⭐⭐

#### **自动风险检查**

```python
class RiskEngine:
    # 1. 价格检查
    def _check_price(self, instrument, price):
        if price <= 0:
            return "Price must be positive"
        if price.precision > instrument.price_precision:
            return "Price precision exceeds instrument precision"
        if price % instrument.price_increment != 0:
            return "Price not aligned to tick size"

    # 2. 数量检查
    def _check_quantity(self, instrument, quantity):
        if quantity <= 0:
            return "Quantity must be positive"
        if quantity < instrument.min_quantity:
            return "Quantity below minimum"
        if quantity > instrument.max_quantity:
            return "Quantity above maximum"

    # 3. 余额检查（调用 BettingAccount）
    def _check_balance(self, account, order):
        required = account.calculate_balance_locked(
            instrument, order.side, order.quantity, order.price
        )
        free = account.balance_free()
        if free < required:
            return "Insufficient balance"

    # 4. 限流检查
    def _check_throttle(self):
        if self._order_submit_rate >= self.max_order_submit_rate:
            return "Throttle: order submit rate exceeded"
```

---

### **1.5 支持的订单类型**

#### **TimeInForce**

```python
# ✅ Polymarket 支持的订单类型
TimeInForce.FOK   # Fill-Or-Kill: 全部成交或立即取消
TimeInForce.IOC   # Immediate-Or-Cancel: 立即成交部分或全部取消

# ❌ Polymarket 不支持的订单类型
TimeInForce.GTC   # Good-Til-Cancel: 有效直到取消
```

#### **订单类型**

```python
# ✅ 支持的订单
OrderType.LIMIT        # 限价单
OrderType.MARKET       # 市价单
OrderType.STOP_MARKET  # 止损市价单
OrderType.LIMIT_MAKER  # Post-only 限价单

# ✅ 支持的订单组合
OrderList(orders=[tp, sl], oco=True)  # OCO: 一个成交，另一个取消
OrderList(orders=[entry, tp], oto=True) # OTO: 一个成交，触发另一个
```

---

## 2. Polymarket 市场机制

### **2.1 CLOB (中央限价订单簿)**

#### **订单簿结构**

```
ASKS (卖单)          BIDS (买单)
0.62 x 100          0.58 x 200
0.61 x 150          0.57 x 150
0.60 x 200  ← MID   0.56 x 100
```

#### **特性**

1. **即时成交机制**
   - FOK: 必须全部成交，否则取消
   - IOC: 成交部分，剩余取消
   - 无挂单簿累积（GTC 不支持）

2. **低流动性**
   - 大部分时间买卖压在 0-1%（几乎平衡）
   - 订单簿更新频率低
   - 大单会显著移动价格

3. **价格发现**
   - 价格反映事件概率
   - 不是传统供需关系
   - 受新闻/事件驱动

---

### **2.2 YES/NO 代币系统**

#### **代币含义**

```python
YES 代币 = 认为事件会发生
NO 代币 = 认为事件不会发生

# 关键公式：
YES_price + NO_price = 1.00

# 如果 YES 价格 = 0.60
# 则 NO 价格 = 0.40
```

#### **盈亏逻辑**

| 持仓 | 事件发生 | 事件不发生 |
|------|---------|----------|
| **持有 YES** | 价格→1.00，赚 (1-入场价) | 价格→0.00，赔 入场价 |
| **持有 NO** | 价格→0.00，赔 入场价 | 价格→1.00，赚 (1-入场价) |

---

### **2.3 结算机制**

#### **市场到期**

```python
# 市场结算时：
if 事件发生:
    YES 价格 → 1.00
    NO 价格 → 0.00
else:
    YES 价格 → 0.00
    NO 价格 → 1.00

# 自动结算：
# - 持有 YES 的：price * quantity (USDC)
# - 持有 NO 的：(1-price) * quantity (USDC)
```

---

### **2.4 交易限制**

#### **最小/最大订单**

```python
# 从 NautilusTrader 源码推断：
min_quantity: 1          # 最小1个代币
max_quantity: 10000+     # 不同品种不同
min_price: 0.001         # 最小价格（0.1%）
max_price: 0.999         # 最大价格（99.9%）
price_increment: 0.001   # 价格精度 0.1%
```

#### **手续费**

```python
# Polymarket 手续费：
# Maker fee: 0% (暂时)
# Taker fee: 0.2% (可能)

# 注意：使用 NautilusTrader 会自动计算
```

---

## 3. BettingAccount 核心算法

### **3.1 算法总结表**

| 算法 | BUY (做多 YES) | SELL (做空 YES) |
|------|---------------|---------------|
| **stake** | `qty × (price - 1)` | `qty × (price - 1)` |
| **liability** | `stake` | `qty` |
| **win_payoff** | `stake` | `-stake` |
| **lose_payoff** | `-qty` | `+qty` |
| **balance_locked** | `stake` | `qty` |

### **3.2 实际计算示例**

#### **示例 1: 买入 YES**

```python
# 参数
price = 0.60  # 60%
quantity = 100
side = OrderSide.BUY

# 计算
stake = 100 × (0.60 - 1) = -40 USDC
liability = -40 USDC
balance_locked = 40 USDC

# 场景A: YES 赢（价格→1.00）
win_payoff = -40 USDC
lose_payoff = -100
net_profit = -40 - (-100) = +60 USDC  ✅ 盈利 60 USDC

# 场景B: YES 输（价格→0.00）
win_payoff = -40 USDC
lose_payoff = -100
net_profit = -40 - (-100) = -40 USDC  ❌ 亏损 40 USDC

# ROI 计算
盈亏 ROI = 60/40 = 150% ✅
亏损 ROI = -40/40 = -100% ❌
```

#### **示例 2: 卖出 YES (做空)**

```python
# 参数
price = 0.60  # 60%
quantity = 100
side = OrderSide.SELL

# 计算
stake = 100 × (0.60 - 1) = -40 USDC
liability = 100 USDC  # 最大损失
balance_locked = 100 USDC  # 需要锁定100 USDC

# 场景A: YES 赢（价格→1.00）
win_payoff = +40 USDC
lose_payoff = +100
net_profit = 40 - 100 = -60 USDC  ❌ 亏损 60 USDC

# 场景B: YES 输（价格→0.00）
win_payoff = +40 USDC
lose_payoff = +100
net_profit = 40 - 100 = +40 USDC  ✅ 盈利 40 USDC

# ROI 计算
盈利 ROI = 40/100 = 40% ✅
亏损 ROI = -60/100 = -60% ❌
```

---

### **3.3 为什么需要 BettingAccount？**

#### **手动计算的复杂性**

```python
# ❌ 错误的手动计算
def calculate_pnl_wrong(side, entry_price, exit_price, quantity):
    # 这是传统现货的计算方法！
    if side == "LONG":
        return (exit_price - entry_price) * quantity
    else:
        return (entry_price - exit_price) * quantity

# 这个计算对 Polymarket 是错误的！
# 因为 Polymarket 是二元预测市场，不是现货市场！
```

#### **正确的计算（BettingAccount）**

```python
# ✅ BettingAccount 自动处理
account = self.cache.account_for_venue("POLYMARKET")

# 获取盈亏
realized_pnl = account.realized_pnl()  # 已实现
unrealized_pnl = account.unrealized_pnl()  # 未实现

# 框架自动调用：
# - stake(quantity, price, side)
# - win_payoff(quantity, price, side)
# - lose_payoff(quantity, side)
# - liability(quantity, price, side)
# - exposure(quantity, price, side)
```

---

## 4. 三者结合点

### **4.1 数据流**

```
┌───────────────────────────────────────────────────────┐
│ Polymarket CLOB                                        │
│ - YES/NO 代币                                          │
│ - FOK/IOC 订单                                         │
│ - 低流动性                                             │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ NautilusTrader Polymarket 适配器                      │
│ - PolymarketDataClient (WebSocket + HTTP)             │
│ - PolymarketExecutionClient (订单执行)                │
│ - 自动重连、订单路由、状态同步                         │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ NautilusTrader 核心系统                                │
│ - Cache (数据缓存)                                      │
│ - DataEngine (数据处理)                                 │
│ - ExecutionEngine (订单执行)                           │
│ - RiskEngine (风险检查)                                │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 专用系统                                               │
│ - Portfolio (仓位管理)                                 │
│ - BettingAccount (二元预测市场记账) ⭐                 │
│ - Accounting (盈亏计算)                                │
└───────────────────────────────────────────────────────┘
                        ↓
┌───────────────────────────────────────────────────────┐
│ 我们的策略                                             │
│ - 信号生成                                             │
│ - 订单参数                                             │
│ - 风险偏好                                             │
└───────────────────────────────────────────────────────┘
```

---

### **4.2 关键结合点**

#### **结合点 1: 订单执行**

```python
# Polymarket: 只支持 FOK/IOC
order = self.order_factory.limit(
    instrument_id=self.instrument.id,
    price=Price.from_str("0.60"),
    order_side=OrderSide.BUY,
    quantity=Quantity.from_int(100),
    time_in_force=TimeInForce.FOK,  # ✅ Polymarket 必需
)

# NautilusTrader: 自动路由
self.submit_order(order)
# → PolymarketExecutionClient
# → CLOB API
# → Polymarket CLOB
```

#### **结合点 2: 余额检查**

```python
# NautilusTrader RiskEngine 调用
# BettingAccount.calculate_balance_locked()

# 买入 YES:
locked = quantity * (price - 1)
# 例如: 100 * (0.60 - 1) = -40 USDC

# 卖出 YES:
locked = quantity
# 例如: 100 USDC

# 如果 free_balance < locked:
# → OrderRejected("Insufficient balance")
```

#### **结合点 3: 盈亏计算**

```python
# Polymarket: 二元预测市场特殊逻辑
# 事件发生 → YES → 1.00, NO → 0.00

# NautilusTrader BettingAccount: 自动处理
account = self.cache.account_for_venue("POLYMARKET")

realized_pnl = account.realized_pnl()
# 框架自动调用 win_payoff/lose_payoff

# 我们的策略: 不需要计算！
pnl = realized_pnl + unrealized_pnl
```

---

## 5. 能做什么 & 不能做什么

### **5.1 ✅ 能做什么**

#### **基础设施层面**

1. **实时数据获取** ✅
   ```python
   # WebSocket 实时订单簿
   self.subscribe_order_book_deltas(instrument_id, BookType.L2_MBP)

   def on_order_book(self, order_book):
       bids = order_book.bids()
       asks = order_book.asks()
       mid = order_book.midpoint()
   ```

2. **订单执行** ✅
   ```python
   # FOK/IOC 订单
   order = self.order_factory.limit(
       time_in_force=TimeInForce.FOK
   )
   self.submit_order(order)

   # OCO 止盈止损
   self.submit_oco_orders(take_profit, stop_loss)
   ```

3. **仓位管理** ✅
   ```python
   # Portfolio 自动管理
   position = self.get_current_position()

   # 不需要自己维护 paper_position
   ```

4. **风险控制** ✅
   ```python
   # RiskEngine 自动检查
   # - 价格有效性
   # - 数量有效性
   # - 余额充足性（BettingAccount）
   # - 订单限流
   ```

5. **盈亏计算** ✅
   ```python
   # BettingAccount 自动计算
   account = self.cache.account_for_venue("POLYMARKET")
   pnl = account.realized_pnl() + account.unrealized_pnl()

   # 不需要自己计算 YES/NO 盈亏逻辑
   ```

6. **回测** ✅
   ```python
   # BacktestEngine
   engine = BacktestEngine(...)
   result = engine.run()

   # 不需要自己写回测引擎
   ```

---

#### **策略层面**

7. **订单簿数据分析** ✅
   ```python
   # 获取订单簿数据
   book = self.cache.order_book(instrument_id)
   bids = book.bids()
   asks = book.asks()

   # 分析订单簿深度
   bid_depth = sum(level.size() for level in bids[:5])
   ask_depth = sum(level.size() for level in asks[:5])
   ```

8. **价格监控** ✅
   ```python
   # 监控价格变化
   mid = book.midpoint()

   if mid > upper_threshold:
       # 价格过高，考虑卖出
       self.submit_sell_order()
   elif mid < lower_threshold:
       # 价格过低，考虑买入
       self.submit_buy_order()
   ```

9. **仓位管理** ✅
   ```python
   # 动态调整仓位
   position = self.get_current_position()

   if position and position['unrealized_pnl'] > target_profit:
       # 止盈
       self.close_position()

   elif position and position['unrealized_pnl'] < -max_loss:
       # 止损
       self.close_position()
   ```

10. **事件驱动交易** ✅（需要外部数据源）
    ```python
    # 监控外部事件（需要额外实现）
    def on_major_event(self, event):
        if event.impact == "HIGH":
            if event.sentiment == "POSITIVE":
                self.buy_market()
            else:
                self.sell_market()
    ```

---

### **5.2 ❌ 不能做什么**

#### **基础设施限制**

1. **无 GTC 订单** ❌
   ```python
   # ❌ Polymarket 不支持
   order = self.order_factory.limit(
       time_in_force=TimeInForce.GTC  # 无法使用
   )

   # ✅ 只能用 FOK/IOC
   time_in_force=TimeInForce.FOK
   ```

2. **无法挂单等待** ❌
   ```python
   # ❌ 无法长时间挂单
   # FOK: 立即全部成交或取消
   # IOC: 立即部分成交或取消

   # ✅ 需要策略定期检查并重新下单
   ```

3. **无法深度回测** ❌
   ```python
   # ❌ 历史数据有限
   # Polymarket 是新市场，历史数据少

   # ✅ 需要自己收集数据
   # 或使用短期回测
   ```

---

#### **策略限制**

4. **订单簿不平衡策略不适合** ❌
   ```python
   # ❌ Polymarket 流动性太低
   # 买卖压通常 0-1%（几乎平衡）
   # 无法触发不平衡信号

   # ✅ 需要其他策略：
   # - 事件驱动
   # - 做市策略
   # - 统计套利
   ```

5. **无法预测事件** ❌
   ```python
   # ❌ NautilusTrader 无法预测事件
   # 价格反映事件概率，不是技术分析

   # ✅ 需要外部数据源：
   # - Twitter API
   # - 新闻 API
   # - 链上数据
   ```

6. **无法解决低流动性** ❌
   ```python
   # ❌ Polymarket 本身低流动性
   # 大单会显著移动价格
   # 滑点不可避免

   # ✅ 只能：
   # - 小订单（10-50个）
   # - 使用 FOK（全部成交或取消）
   # - 接受部分成交（IOC）
   ```

---

### **5.3 ⚠️ 需要注意的**

#### **市场特性**

1. **价格跳跃**
   ```python
   # Polymarket 价格可能跳跃
   # 0.60 → 0.80（重大新闻）
   # 0.60 → 0.40（反面消息）

   # ⚠️ 止损可能失效
   # 价格跳过止损价
   ```

2. **市场到期**
   ```python
   # 市场到期时流动性急剧下降
   # drop_quotes_missing_side = True（默认）

   # ⚠️ 接近期日时停止交易
   # 或使用 boundary prices (0.001/0.999)
   ```

3. **API 限制**
   ```python
   # Polymarket API 可能有速率限制
   # max_retries, retry_delay_initial_ms

   # ⚠️ 不要过度交易
   # 使用 RiskEngine 限流
   ```

---

## 6. 下一步策略设计方向

### **6.1 基于基础设施能力的策略**

#### **策略 1: 做市策略** ⭐⭐⭐⭐⭐

```python
class MarketMakingStrategy(BaseStrategy):
    """
    利用 NautilusTrader 的 OCO 订单

    优势：
    - 不依赖价格方向
    - 赚取买卖价差
    - 提供流动性
    """

    def on_order_book(self, order_book):
        mid = order_book.midpoint()
        spread = Decimal("0.02")  # 2% 价差

        # 同时挂买单和卖单
        buy_order = self.order_factory.limit(
            price=mid * (Decimal("1") - spread),
            quantity=Quantity.from_int(10),
            time_in_force=TimeInForce.FOK,
        )

        sell_order = self.order_factory.limit(
            price=mid * (Decimal("1") + spread),
            quantity=Quantity.from_int(10),
            time_in_force=TimeInForce.FOK,
        )

        # 使用 OCO：一个成交，取消另一个
        self.submit_oco_orders(buy_order, sell_order)
```

#### **策略 2: 事件驱动策略** ⭐⭐⭐⭐⭐

```python
class EventDrivenStrategy(BaseStrategy):
    """
    结合外部数据源

    需要：
    - Twitter API
    - 新闻 API
    - 链上数据监控
    """

    def on_major_event(self, event):
        # 快速评估事件影响
        if event.impact == "HIGH":
            if event.sentiment == "POSITIVE":
                # 使用市价单快速入场
                self.submit_market_order(
                    side=OrderSide.BUY,
                    quantity=Quantity.from_int(20),
                )

                # 使用 OCO 设置止盈止损
                self._set_stop_orders()
```

#### **策略 3: 统计套利** ⭐⭐⭐

```python
class StatisticalArbitrageStrategy(BaseStrategy):
    """
    跨市场套利（如果有多市场）

    利用：
    - Portfolio 管理多仓位
    - BettingAccount 计算盈亏
    - RiskEngine 风险控制
    """
```

---

### **6.2 不能做的策略**

#### **❌ 订单簿不平衡策略**

```python
# 为什么不适合？
# - Polymarket 流动性太低
# - 买卖压通常 0-1%
# - 无法触发不平衡信号
# - 已被回测证明失败（162种组合全部亏损）
```

#### **❌ 趋势跟踪策略**

```python
# 为什么不适合？
# - Polymarket 价格是概率，不是趋势
# - 受事件驱动，不是技术分析
# - 价格跳跃（0.60 → 0.80）
```

---

## 📊 总结

### **NautilusTrader + Polymarket 结合优势**

1. ✅ **官方适配器** - 无需自己对接 API
2. ✅ **BettingAccount** - 自动处理 YES/NO 盈亏
3. ✅ **Portfolio 系统** - 自动管理仓位
4. ✅ **RiskEngine** - 自动风险检查
5. ✅ **FOK/IOC 支持** - 匹配 CLOB 机制
6. ✅ **OCO 订单** - 自动止盈止损

### **策略设计原则**

1. **适应市场特性**
   - 低流动性 → 小订单
   - 事件驱动 → 快速反应
   - 价格跳跃 → 宽止损

2. **充分利用框架**
   - Portfolio → 不自己维护仓位
   - BettingAccount → 不自己计算盈亏
   - RiskEngine → 不自己检查风险
   - BacktestEngine → 不自己写回测

3. **避免不适合的策略**
   - ❌ 订单簿不平衡
   - ❌ 趋势跟踪
   - ✅ 事件驱动
   - ✅ 做市策略

---

**文档版本**: v1.0
**日期**: 2026-01-28
**作者**: Claude Code
**下一步**: 基于基础设施能力设计具体策略
