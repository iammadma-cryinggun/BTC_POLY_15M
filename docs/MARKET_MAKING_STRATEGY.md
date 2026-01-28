# Polymarket 做市策略设计文档

> **日期**: 2026-01-28
> **作者**: Claude Code
> **版本**: v1.0

---

## 📋 目录

1. [策略概述](#策略概述)
2. [市场特性分析](#市场特性分析)
3. [策略核心逻辑](#策略核心逻辑)
4. [风险管理](#风险管理)
5. [参数配置](#参数配置)
6. [实现方案](#实现方案)

---

## 1. 策略概述

### **1.1 什么是做市策略？**

做市策略（Market Making）是指同时挂买单和卖单，通过赚取买卖价差（Spread）来获利。

```
订单簿状态:
ASK: 0.62 x 100  ← 我们的卖单
BID: 0.58 x 100  ← 我们的买单
      ↑
    中间价 0.60
```

**盈利逻辑**：
- 以 0.58 买入（低买）
- 以 0.62 卖出（高卖）
- 赚取 0.04 价差（6.67%）

**风险**：
- 价格向不利方向移动
- 库存积压（持有太多 YES 或 NO）

---

### **1.2 为什么适合 Polymarket？**

| Polymarket 特性 | 做市策略优势 |
|-----------------|-------------|
| **低流动性** | 我们提供流动性，赚取流动性溢价 ✅ |
| **大价差** | 价差通常 2-5%，利润空间大 ✅ |
| **FOK/IOC** | 快速成交，减少持仓时间 ✅ |
| **事件驱动** | 事件前价差更大，利润更丰厚 ✅ |
| **YES/NO** | 可以双向做市，灵活调整 ✅ |

---

### **1.3 核心目标**

```python
主要目标：
1. 赚取买卖价差（核心）
2. 保持库存中性（不偏向 YES 或 NO）
3. 控制最大回撤
4. 提供市场流动性

次要目标：
1. 适应事件（重大新闻前后调整）
2. 动态调整价差
3. 管理单笔风险
```

---

## 2. 市场特性分析

### **2.1 Polymarket 订单簿特征**

#### **正常情况**
```
时间: 平静期
ASK: 0.61 x 50
     0.60 x 100  ← MID
BID: 0.59 x 80
     0.58 x 120

价差: (0.61 - 0.58) / 0.60 = 5.0%
```

#### **事件期**
```
时间: 重大新闻后
ASK: 0.75 x 20
     0.70 x 50   ← MID (跳升)
BID: 0.65 x 30
     0.60 x 100

价差: (0.75 - 0.60) / 0.70 = 21.4% (更大！)
```

### **2.2 关键发现**

1. **价差大**：正常 2-5%，事件期可达 10-20%
2. **深度浅**：订单簿薄，大单会显著移动价格
3. **价格跳跃**：事件发生时价格可能跳跃 10-20%
4. **流动性不均**：YES 和 NO 流动性可能不同

---

## 3. 策略核心逻辑

### **3.1 基础做市逻辑**

```python
def on_order_book(self, order_book):
    # 1. 获取中间价
    mid = order_book.midpoint()

    # 2. 计算价差
    half_spread = self.config.base_spread / 2  # 如 2% / 2 = 1%

    # 3. 计算挂单价格
    bid_price = mid * (1 - half_spread)  # 买单价
    ask_price = mid * (1 + half_spread)  # 卖单价

    # 4. 同时挂买单和卖单
    buy_order = self.order_factory.limit(
        price=bid_price,
        quantity=self.config.order_size,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.FOK,
    )

    sell_order = self.order_factory.limit(
        price=ask_price,
        quantity=self.config.order_size,
        side=OrderSide.SELL,
        time_in_force=TimeInForce.FOK,
    )

    # 5. 使用 OCO：一个成交，取消另一个
    self.submit_oco_orders(buy_order, sell_order)
```

---

### **3.2 库存管理（关键！）**

#### **问题**
如果只做市，可能会累积库存：
- 价格下跌 → 买入成交多 → 持有过多 YES
- 价格上涨 → 卖出成交多 → 持有过多 NO（做空白头）

#### **解决方案：Skew（倾斜）**

```python
def calculate_skew(self, target_inventory=0):
    """
    计算价格倾斜

    如果持有过多 YES（做多）→ 降低买价，提高卖价 → 鼓励卖出
    如果持有过多 NO（做空）→ 提高买价，降低卖价 → 鼓励买入
    """
    position = self.get_current_position()

    if not position:
        return 0.0  # 无持仓，不倾斜

    current_inventory = position['quantity']
    inventory_delta = current_inventory - target_inventory

    # 库存越多，倾斜越大
    skew = inventory_delta * self.config.inventory_skew_factor

    # 限制最大倾斜
    max_skew = self.config.max_skew
    skew = max(min(skew, max_skew), -max_skew)

    return skew

# 应用倾斜
skew = self.calculate_skew()

bid_price = mid * (1 - half_spread - skew)  # 降低买价
ask_price = mid * (1 + half_spread + skew)  # 提高卖价
```

#### **例子**

```python
# 场景1: 持有过多 YES（+100个）
skew = 100 * 0.0001 = 0.01 (1%)

mid = 0.60
half_spread = 0.01 (1%)

# 正常价：
bid_price = 0.60 * (1 - 0.01) = 0.594
ask_price = 0.60 * (1 + 0.01) = 0.606

# 倾斜后：
bid_price = 0.60 * (1 - 0.01 - 0.01) = 0.588  # 降低买价（难买）
ask_price = 0.60 * (1 + 0.01 + 0.01) = 0.612  # 提高卖价（好卖）

# 结果：倾向于卖出 YES，减少库存
```

---

### **3.3 动态价差调整**

#### **基础价差**

```python
# 根据市场波动率调整价差
def calculate_spread(self, order_book):
    """
    计算动态价差

    波动率大 → 价差大（风险补偿）
    波动率小 → 价差小（更激进）
    """
    # 1. 计算价格波动率
    volatility = self.calculate_recent_volatility()

    # 2. 基础价差
    base_spread = self.config.base_spread

    # 3. 根据波动率调整
    if volatility > 0.05:  # 高波动
        spread = base_spread * 1.5
    elif volatility > 0.03:  # 中等波动
        spread = base_spread * 1.2
    else:  # 低波动
        spread = base_spread * 1.0

    # 4. 限制价差范围
    min_spread = self.config.min_spread
    max_spread = self.config.max_spread
    spread = max(min(spread, max_spread), min_spread)

    return spread
```

#### **事件期价差扩大**

```python
# 检测到重大事件
if self.detect_major_event():
    spread = self.config.event_spread  # 如 10%
    order_size = self.config.event_order_size  # 如 5个（小单）
else:
    spread = self.calculate_spread(order_book)
    order_size = self.config.order_size
```

---

### **3.4 订单执行逻辑**

#### **FOK vs IOC**

```python
# FOK (Fill-Or-Kill): 全部成交或取消
# 优点：完全成交，无部分成交
# 缺点：可能无法成交

# IOC (Immediate-Or-Cancel): 立即成交部分或全部
# 优点：部分成交也能赚一点
# 缺点：可能留下小仓位

# 推荐：使用 IOC（更灵活）
time_in_force=TimeInForce.IOC
```

#### **订单大小**

```python
# 根据订单簿深度调整
def calculate_order_size(self, order_book):
    """
    动态调整订单大小

    深度浅 → 小订单（避免冲击价格）
    深度深 → 大订单（更多利润）
    """
    # 获取订单簿深度
    bids = order_book.bids()
    asks = order_book.asks()

    bid_depth = sum(level.size() for level in bids[:5])
    ask_depth = sum(level.size() for level in asks[:5])
    avg_depth = (bid_depth + ask_depth) / 2

    # 根据深度调整
    if avg_depth < 50:
        order_size = min(self.config.order_size, 10)
    elif avg_depth < 200:
        order_size = min(self.config.order_size, 20)
    else:
        order_size = self.config.order_size

    return Quantity.from_int(int(order_size))
```

---

## 4. 风险管理

### **4.1 库存风险**

#### **最大库存限制**

```python
def check_inventory_limits(self):
    """检查库存是否超限"""
    position = self.get_current_position()

    if not position:
        return True

    current_inventory = abs(position['quantity'])
    max_inventory = self.config.max_inventory

    if current_inventory >= max_inventory:
        self.log.warning(
            f"库存已达上限: {current_inventory} >= {max_inventory}"
        )
        return False

    # 接近上限时降低订单大小
    if current_inventory >= max_inventory * 0.8:
        self.order_size = self.config.order_size * 0.5
        self.log.info(f"库存接近上限，降低订单大小")

    return True
```

#### **库存对冲**

```python
def hedge_inventory(self):
    """
    当库存过多时对冲

    持有过多 YES → 卖出 YES（市价单）
    持有过多 NO → 买入 YES（市价单）
    """
    position = self.get_current_position()

    if not position:
        return

    current_inventory = position['quantity']
    hedge_threshold = self.config.hedge_threshold  # 如 50个

    if abs(current_inventory) > hedge_threshold:
        self.log.warning(
            f"库存过多，执行对冲: {current_inventory}"
        )

        # 使用市价单快速对冲
        if current_inventory > 0:
            # 持有过多 YES，卖出
            self.submit_market_order(
                side=OrderSide.SELL,
                quantity=Quantity.from_int(abs(current_inventory) / 2),
            )
        else:
            # 持有过多 NO，买入
            self.submit_market_order(
                side=OrderSide.BUY,
                quantity=Quantity.from_int(abs(current_inventory) / 2),
            )
```

---

### **4.2 价格风险**

#### **价格保护**

```python
def check_price_range(self, order_book):
    """
    检查价格是否在合理范围内

    避免极端价格交易
    """
    mid = order_book.midpoint()

    if not mid:
        return False

    # 检查价格范围
    min_price = self.config.min_price  # 如 0.05 (5%)
    max_price = self.config.max_price  # 如 0.95 (95%)

    if mid < min_price or mid > max_price:
        self.log.warning(
            f"价格 {mid} 超出范围 [{min_price}, {max_price}]"
        )
        return False

    return True
```

#### **波动率保护**

```python
def check_volatility(self):
    """
    检查波动率是否过高

    波动率过高时暂停做市
    """
    volatility = self.calculate_recent_volatility()

    if volatility > self.config.max_volatility:
        self.log.warning(
            f"波动率过高: {volatility*100:.2f}% > "
            f"{self.config.max_volatility*100:.2f}%"
        )
        return False

    return True
```

---

### **4.3 单笔风险**

#### **止损设置**

```python
def set_stop_loss(self, entry_price, side):
    """
    使用 OCO 订单设置止盈止损

    做市策略本身不设止损（通过价差赚钱）
    但需要对冲仓位设置止损
    """
    # 止盈：价差的 2 倍
    take_profit_price = entry_price * (1 + self.config.spread * 2)

    # 止损：价差的 3 倍
    stop_loss_price = entry_price * (1 - self.config.spread * 3)

    # 创建 OCO 订单
    take_profit = self.order_factory.limit(
        price=take_profit_price,
        quantity=self.config.hedge_size,
        side=OrderSide.SELL if side == "LONG" else OrderSide.BUY,
        time_in_force=TimeInForce.GTC,
    )

    stop_loss = self.order_factory.stop_market(
        trigger_price=stop_loss_price,
        quantity=self.config.hedge_size,
        side=OrderSide.SELL if side == "LONG" else OrderSide.BUY,
    )

    self.submit_oco_orders(take_profit, stop_loss)
```

---

### **4.4 资金管理**

#### **最大仓位**

```python
def check_position_limits(self):
    """
    检查仓位限制

    总持仓不超过总资金的一定比例
    """
    account = self.cache.account_for_venue("POLYMARKET")
    free_balance = account.balance_free()

    position = self.get_current_position()
    if not position:
        return True

    position_value = abs(position['quantity']) * position['current_price']

    if position_value > free_balance * self.config.max_position_ratio:
        self.log.warning(
            f"仓位过大: {position_value} > "
            f"{free_balance * self.config.max_position_ratio}"
        )
        return False

    return True
```

---

## 5. 参数配置

### **5.1 核心参数**

```python
@dataclass
class MarketMakingConfig:
    # ========== 价差参数 ==========
    base_spread: float = 0.02       # 基础价差 2%
    min_spread: float = 0.005       # 最小价差 0.5%
    max_spread: float = 0.10       # 最大价差 10%
    event_spread: float = 0.08      # 事件期价差 8%

    # ========== 订单参数 ==========
    order_size: int = 20            # 基础订单大小（个）
    min_order_size: int = 5         # 最小订单大小
    max_order_size: int = 50        # 最大订单大小
    event_order_size: int = 10      # 事件期订单大小（小单）

    # ========== 库存参数 ==========
    target_inventory: int = 0       # 目标库存（中性）
    max_inventory: int = 200       # 最大库存（个）
    inventory_skew_factor: float = 0.0001  # 库存倾斜因子
    max_skew: float = 0.02         # 最大倾斜 2%
    hedge_threshold: int = 80      # 对冲阈值（个）
    hedge_size: int = 20           # 对冲大小（个）

    # ========== 价格参数 ==========
    min_price: float = 0.05        # 最小价格 5%
    max_price: float = 0.95        # 最大价格 95%

    # ========== 波动率参数 ==========
    max_volatility: float = 0.15   # 最大波动率 15%
    volatility_window: int = 100   # 波动率计算窗口（tick数）

    # ========== 风险参数 ==========
    max_position_ratio: float = 0.5  # 最大仓位比例（50%）
    max_daily_loss: float = -100.0   # 日最大亏损（USDC）
    max_drawdown: float = -0.20      # 最大回撤（-20%）

    # ========== 行为参数 ==========
    update_interval_ms: int = 1000  # 更新间隔（毫秒）
    use_inventory_skew: bool = True   # 使用库存倾斜
    use_dynamic_spread: bool = True  # 使用动态价差
```

---

### **5.2 预设配置**

#### **保守配置**

```python
CONSERVATIVE_CONFIG = MarketMakingConfig(
    base_spread=0.03,           # 3% 价差（利润更大）
    order_size=10,              # 小单（10个）
    max_inventory=100,          # 限制库存
    inventory_skew_factor=0.0002,  # 更积极的库存管理
    max_volatility=0.10,        # 波动率 > 10% 暂停
    max_position_ratio=0.3,     # 最大仓位 30%
)
```

#### **激进配置**

```python
AGGRESSIVE_CONFIG = MarketMakingConfig(
    base_spread=0.01,           # 1% 价差（更激进）
    order_size=50,              # 大单（50个）
    max_inventory=300,          # 允许更大库存
    inventory_skew_factor=0.00005,  # 温和的库存管理
    max_volatility=0.20,        # 波动率 > 20% 暂停
    max_position_ratio=0.7,     # 最大仓位 70%
)
```

---

## 6. 实现方案

### **6.1 策略类结构**

```python
class MarketMakingStrategy(BaseStrategy):
    """
    Polymarket 做市策略

    核心功能：
    1. 同时挂买单和卖单（赚取价差）
    2. 库存管理（Skew）
    3. 动态价差调整
    4. 风险控制
    """

    def on_order_book(self, order_book):
        # 1. 检查风险
        if not self.check_risk():
            return

        # 2. 计算参数
        mid = order_book.midpoint()
        spread = self.calculate_spread(order_book)
        skew = self.calculate_skew()

        # 3. 计算挂单价格
        bid_price = mid * (1 - spread/2 - skew)
        ask_price = mid * (1 + spread/2 + skew)

        # 4. 提交订单
        self.submit_quotes(bid_price, ask_price)

    def on_order_filled(self, event):
        # 1. 检查库存
        self.check_inventory_limits()

        # 2. 如果库存过多，对冲
        if self.need_hedge():
            self.hedge_inventory()
```

---

### **6.2 风险检查流程**

```python
def check_risk(self):
    """综合风险检查"""
    checks = [
        self.check_price_range(order_book),
        self.check_volatility(),
        self.check_inventory_limits(),
        self.check_position_limits(),
        self.check_daily_loss(),
    ]

    return all(checks)
```

---

### **6.3 性能指标**

#### **预期收益**

```python
# 假设条件：
# - 平均价差: 2%
# - 成交率: 30% (FOK 订单)
# - 每天交易次数: 100 次
# - 订单大小: 20 个
# - 平均价格: 0.60

# 计算：
daily_trades = 100
trade_size = 20
avg_price = 0.60
spread_pct = 0.02

# 每笔利润（单边）
profit_per_trade = trade_size * avg_price * spread_pct
                    = 20 * 0.60 * 0.02
                    = 0.24 USDC

# 每天（双向成交）
daily_profit = daily_trades * profit_per_trade * 0.3  # 30%成交率
             = 100 * 0.24 * 0.3
             = 7.2 USDC/天

# 每月
monthly_profit = 7.2 * 30 = 216 USDC
```

#### **风险指标**

```python
# 最大回撤预期: -10% 到 -20%
# 夏普比率预期: 0.5 到 1.5
# 胜率预期: 60% 到 70%
# 盈亏比预期: 1.5 到 2.0
```

---

## 7. 优化方向

### **7.1 短期优化**

1. **自适应价差**
   ```python
   # 根据历史成交率调整价差
   # 成交率高 → 降低价差（更激进）
   # 成交率低 → 提高价差（更保守）
   ```

2. **事件检测**
   ```python
   # 检测重大事件
   # - 价格快速变化
   # - 成交量激增
   # - 订单簿深度变化
   ```

3. **多层订单**
   ```python
   # 挂多个价位的订单
   # 增加成交概率
   ```

---

### **7.2 长期优化**

1. **机器学习**
   ```python
   # 预测最佳价差
   # 预测价格方向
   # 优化库存管理
   ```

2. **跨市场对冲**
   ```python
   # Polymarket vs 其他平台
   # 套利机会
   ```

3. **新闻分析**
   ```python
   # NLP 分析新闻情感
   # 提前调整仓位
   ```

---

## 8. 实施计划

### **阶段 1: 基础实现** (1-2天)

- [x] 策略设计文档
- [ ] 实现 MarketMakingStrategy 类
- [ ] 实现风险检查
- [ ] 实现库存管理
- [ ] 单元测试

### **阶段 2: 回测验证** (2-3天)

- [ ] 收集历史数据
- [ ] 使用 BacktestEngine 回测
- [ ] 参数优化
- [ ] 性能分析

### **阶段 3: 模拟测试** (1周)

- [ ] Paper Trading 测试
- [ ] 参数微调
- [ ] 性能监控
- [ ] Bug 修复

### **阶段 4: 实盘部署** (1周)

- [ ] 小资金测试
- [ ] 逐步扩大规模
- [ ] 持续优化

---

## 📊 预期结果

### **保守估计**

| 指标 | 预期值 |
|------|--------|
| 月收益率 | 10-20% |
| 最大回撤 | -10% |
| 夏普比率 | 0.8-1.2 |
| 胜率 | 65-70% |

### **激进估计**

| 指标 | 预期值 |
|------|--------|
| 月收益率 | 20-40% |
| 最大回撤 | -20% |
| 夏普比率 | 1.0-1.5 |
| 胜率 | 60-65% |

---

**文档版本**: v1.0
**日期**: 2026-01-28
**作者**: Claude Code
**下一步**: 实现代码
