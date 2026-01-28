# 做市策略测试指南

> **Polymarket Market Making Strategy Testing**
>
> **日期**: 2026-01-28
> **版本**: v1.0

---

## 📋 目录

1. [测试方法](#测试方法)
2. [单元测试](#单元测试)
3. [快速验证](#快速验证)
4. [Paper Trading 测试](#paper-trading-测试)
5. [测试清单](#测试清单)

---

## 1. 测试方法

### **1.1 为什么没有历史数据？**

Polymarket 是一个新兴的预测市场，目前**没有公开的历史订单簿数据**。但这不影响我们测试策略。

### **1.2 我们的测试方法**

参考 `poly-sdk-trader` 项目，我们采用**实时测试**方法：

| 测试类型 | 目的 | 数据源 | 是否需要私钥 |
|---------|------|--------|------------|
| **单元测试** | 测试计算逻辑 | Mock 数据 | ❌ 不需要 |
| **快速验证** | 验证基本功能 | 实时 API | ❌ 不需要 |
| **Paper Trading** | 模拟真实交易 | 实时订单簿 | ⚠️ 可选 |
| **真实交易** | 真实盈亏 | 实时订单簿 | ✅ 需要 |

### **1.3 测试流程**

```bash
# 1. 单元测试（验证计算逻辑）
pytest tests/unit/test_market_making.py -v

# 2. 快速验证（验证基本功能）
python tests/quick_validation.py

# 3. Paper Trading（模拟运行 1 小时）
python tests/test_paper_trading.py --duration=60

# 4. 真实交易（从小资金开始）
python run_market_making.py --mode portfolio
```

---

## 2. 单元测试

### **2.1 测试范围**

单元测试验证**核心计算逻辑**，不涉及真实市场数据：

| 测试函数 | 测试内容 |
|---------|---------|
| `test_calculate_dynamic_spread()` | 动态价差计算 |
| `test_calculate_inventory_skew()` | 库存倾斜计算 |
| `test_calculate_order_size()` | 订单大小计算 |
| `test_calculate_volatility()` | 波动率计算 |
| `test_check_price_range()` | 价格范围检查 |
| `test_check_volatility_limit()` | 波动率限制检查 |
| `test_check_inventory_limits()` | 库存限制检查 |
| `test_check_position_limits()` | 仓位限制检查 |
| `test_check_daily_loss_limit()` | 日亏损限制检查 |
| `test_need_hedge()` | 对冲触发条件 |

### **2.2 运行单元测试**

```bash
# 运行所有单元测试
pytest tests/unit/test_market_making.py -v

# 运行单个测试
pytest tests/unit/test_market_making.py::test_calculate_inventory_skew -v

# 查看测试覆盖率
pytest tests/unit/ --cov=strategies --cov-report=html
```

### **2.3 测试示例**

```python
# tests/unit/test_market_making.py
def test_calculate_inventory_skew():
    """测试库存倾斜计算"""
    # Mock 数据
    strategy = MarketMakingStrategy(config)
    strategy.cache.portfolio = MockPortfolio(
        position=Position(side=Long, quantity=100, avg_px_open=0.60)
    )

    # 计算倾斜
    skew = strategy._calculate_inventory_skew()

    # 持有过多 YES（+100），目标库存 0
    # skew = (100 - 0) * 0.0001 = 0.01 (1%)
    assert skew == Decimal("0.01")
```

---

## 3. 快速验证

### **3.1 目的**

快速验证检查：
- ✅ 策略配置是否正确
- ✅ 核心方法是否可用
- ✅ NautilusTrader 集成是否正常
- ✅ 日志输出是否正常

**无需私钥**，无需真实交易，30秒内完成。

### **3.2 运行快速验证**

```bash
python tests/quick_validation.py
```

**预期输出**：

```
============================================================
Market Making Strategy - Quick Validation
============================================================

✅ Configuration validation
   - base_spread: 0.02 (2%)
   - order_size: 20
   - max_inventory: 200
   - All parameters valid

✅ Method availability
   - _calculate_dynamic_spread: ✓
   - _calculate_inventory_skew: ✓
   - _calculate_order_size: ✓
   - _check_risk: ✓
   - All methods available

✅ NautilusTrader integration
   - Portfolio system: ✓
   - Instrument cache: ✓
   - Order factory: ✓
   - All integrations working

✅ Risk checks
   - Price range check: ✓
   - Volatility limit check: ✓
   - Inventory limits check: ✓
   - Position limits check: ✓
   - Daily loss limit check: ✓
   - All risk checks available

============================================================
✅ Quick validation PASSED (2.5 seconds)
============================================================
```

---

## 4. Paper Trading 测试

### **4.1 目的**

Paper Trading 模拟真实交易环境：
- ✅ 使用实时订单簿数据
- ✅ 模拟订单成交
- ✅ 模拟持仓和盈亏
- ✅ **不真实下单**（无需私钥）

### **4.2 运行 Paper Trading**

```bash
# 运行 1 小时 Paper Trading
python tests/test_paper_trading.py --duration=60

# 运行 4 小时并保存详细日志
python tests/test_paper_trading.py --duration=240 --verbose

# 运行并显示实时统计
python tests/test_paper_trading.py --duration=60 --stats
```

### **4.3 测试指标**

**关键指标**：
- 订单成交率（应该 > 20%）
- 平均价差（应该 2-5%）
- 库存周转率（应该 > 0.5）
- 最大回撤（应该 < -20%）
- 总盈亏（应该 > 0）

**预期输出示例**：

```
============================================================
Paper Trading Results (2026-01-28 15:30:00)
============================================================

Duration: 60 minutes
Total orders placed: 240 (120 bid, 120 ask)
Orders filled: 58 (24.2% fill rate)

📊 Performance Metrics:
  Total trades: 58
  Winning trades: 38 (65.5%)
  Losing trades: 20 (34.5%)
  Total PnL: +12.45 USDC
  Average spread: 2.8%
  Max drawdown: -8.2%

📦 Inventory Management:
  Max inventory: 85 (42.5% of limit)
  Inventory turnover: 2.3x
  Hedge triggered: 2 times

🛡️ Risk Management:
  Volatility protection: 5 times paused
  Daily loss limit: Never triggered
  Max position limit: Never breached

✅ Paper Trading PASSED
```

---

## 5. 测试清单

### **5.1 部署前检查** ✅

在开始真实交易前，确保：

- [ ] 单元测试全部通过
  ```bash
  pytest tests/unit/test_market_making.py -v
  ```

- [ ] 快速验证通过
  ```bash
  python tests/quick_validation.py
  ```

- [ ] Paper Trading 至少运行 10 小时
  ```bash
  python tests/test_paper_trading.py --duration=600
  ```

- [ ] Paper Trading 盈利 > 100 USDC
  ```bash
  # 检查日志中的 Total PnL
  ```

- [ ] 订单成交率 > 20%
  ```bash
  # 检查日志中的 fill rate
  ```

- [ ] 最大回撤 < -20%
  ```bash
  # 检查日志中的 max drawdown
  ```

### **5.2 首次真实交易** 🚨

- [ ] 从小资金开始（100-200 USDC）
- [ ] 降低订单大小（10 个）
- [ ] 降低最大库存（50 个）
- [ ] 监控前 24 小时
- [ ] 准备随时停止

### **5.3 监控指标** 📊

真实交易期间，每日检查：

| 指标 | 正常范围 | 警告 | 停止策略 |
|------|---------|------|---------|
| **成交率** | > 20% | 10-20% | < 10% |
| **平均价差** | 2-5% | 1-2% 或 5-8% | < 1% 或 > 8% |
| **库存周转率** | > 1.0 | 0.5-1.0 | < 0.5 |
| **日盈亏** | > -50 USDC | -50 to -100 | < -100 |
| **最大回撤** | < -10% | -10% to -20% | > -20% |

---

## 6. 故障排除

### **6.1 单元测试失败**

**问题**：`test_calculate_inventory_skew` 失败

**排查**：
```python
# 打印中间值
print(f"Inventory: {position['quantity']}")
print(f"Target: {strategy.target_inventory}")
print(f"Delta: {inventory_delta}")
print(f"Skew: {skew}")
```

### **6.2 Paper Trading 成交率过低**

**问题**：成交率 < 10%

**原因**：
1. 价差过大（降低 `base_spread`）
2. 订单太大（降低 `order_size`）
3. 市场流动性太低（更换市场）

**解决**：
```python
# 调整参数
MM_CONFIG['base_spread'] = 0.015  # 从 2% 降到 1.5%
MM_CONFIG['order_size'] = 10      # 从 20 降到 10
```

### **6.3 Paper Trading 库存累积**

**问题**：库存持续增长

**原因**：
1. `inventory_skew_factor` 太小
2. 单边市场行情

**解决**：
```python
# 增加倾斜强度
MM_CONFIG['inventory_skew_factor'] = 0.0002  # 从 0.0001 增加到 0.0002

# 或降低对冲阈值
MM_CONFIG['hedge_threshold'] = 60  # 从 80 降到 60
```

---

## 7. 总结

### **测试金字塔**

```
        /\
       /  \
      / REAL \
     / TRADING \
    /----------\
   / Paper Trading \
  /----------------\
 /   Quick Valid    \
/--------------------\
/    Unit Tests       \
========================
```

**测试原则**：
1. **先单元，后集成** - 确保每个函数正确
2. **先验证，后运行** - 确保基本功能正常
3. **先模拟，后真实** - Paper Trading 充分测试
4. **小资金，慢增长** - 真实交易从小开始

### **时间表**

| 阶段 | 时长 | 目标 |
|------|------|------|
| 单元测试 | 1-2 天 | 所有测试通过 |
| 快速验证 | 10 分钟 | 基本功能正常 |
| Paper Trading | 1-2 周 | 盈利 > 100 USDC |
| 真实交易（小资金） | 1-2 周 | 盈利 > 50 USDC |
| 真实交易（正常资金） | 长期 | 持续盈利 |

---

**版本**: v1.0
**日期**: 2026-01-28
**作者**: Claude Code
**状态**: ✅ 已完成

**重要提示**:
- 充分测试后再真实交易
- 从小资金开始
- 密切监控指标
- 及时调整参数
