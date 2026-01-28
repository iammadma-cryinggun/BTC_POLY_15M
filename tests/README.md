# 做市策略测试

本目录包含做市策略的测试脚本。

## 📁 文件结构

```
tests/
├── __init__.py
├── README.md
├── quick_validation.py       # 快速验证脚本
├── test_paper_trading.py     # Paper Trading 测试
└── unit/
    ├── __init__.py
    └── test_market_making.py # 单元测试
```

## 🚀 快速开始

### 1. 快速验证（推荐先运行）

无需私钥，无需真实交易，30 秒内完成：

```bash
python tests/quick_validation.py
```

### 2. 单元测试

测试核心计算逻辑：

```bash
# 运行所有单元测试
pytest tests/unit/test_market_making.py -v

# 运行单个测试
pytest tests/unit/test_market_making.py::test_calculate_inventory_skew -v

# 查看测试覆盖率
pytest tests/unit/ --cov=strategies --cov-report=html
```

### 3. Paper Trading

模拟真实交易环境：

```bash
# 运行 1 小时 Paper Trading
python tests/test_paper_trading.py --duration=60

# 运行 4 小时并显示详细日志
python tests/test_paper_trading.py --duration=240 --verbose

# 运行并显示实时统计
python tests/test_paper_trading.py --duration=60 --stats
```

## 📊 测试覆盖范围

### 单元测试（`test_market_making.py`）

- ✅ 动态价差计算
- ✅ 库存倾斜计算
- ✅ 订单大小计算
- ✅ 波动率计算
- ✅ 价格范围检查
- ✅ 波动率限制检查
- ✅ 库存限制检查
- ✅ 仓位限制检查
- ✅ 日亏损限制检查
- ✅ 对冲触发条件

### 快速验证（`quick_validation.py`）

- ✅ 配置验证
- ✅ 方法可用性
- ✅ NautilusTrader 集成
- ✅ 风险检查

### Paper Trading（`test_paper_trading.py`）

- ✅ 实时订单簿数据处理
- ✅ 订单成交模拟
- ✅ 持仓和盈亏计算
- ✅ 性能指标统计
- ✅ 风险管理验证

## 📈 预期结果

### 快速验证

```
✅ Quick validation PASSED (2.5 seconds)
```

### 单元测试

```
test_market_making.py::test_calculate_inventory_skew PASSED
test_market_making.py::test_check_price_range PASSED
...
========================= 25 passed in 2.5s =========================
```

### Paper Trading（1 小时）

```
Duration: 60 minutes
Orders placed: 240
Orders filled: 58 (24.2% fill rate)
Total PnL: +12.45 USDC
Average spread: 2.8%
Max drawdown: -8.2%

✅ Paper Trading PASSED
```

## ⚠️ 注意事项

1. **测试顺序**：先运行快速验证，再运行单元测试，最后 Paper Trading
2. **Paper Trading 时间**：建议至少运行 10 小时 Paper Trading
3. **参数调整**：如果成交率过低，调整 `base_spread` 和 `order_size`
4. **监控指标**：重点关注成交率、盈亏、库存周转率

## 🔗 相关文档

- [测试指南](../docs/TESTING_GUIDE.md) - 详细的测试说明
- [做市策略指南](../docs/MARKET_MAKING_GUIDE.md) - 策略使用说明
- [策略设计文档](../docs/MARKET_MAKING_STRATEGY.md) - 策略设计

## 🛠️ 故障排除

### 问题：导入失败

```
❌ 导入失败: No module named 'nautilus_trader'
```

**解决**：
```bash
pip install -r requirements.txt
```

### 问题：单元测试失败

```
FAILED test_calculate_inventory_skew
```

**解决**：
1. 检查测试代码中的 Mock 对象是否正确
2. 运行单个测试查看详细错误：
   ```bash
   pytest tests/unit/test_market_making.py::test_calculate_inventory_skew -vv
   ```

### 问题：Paper Trading 成交率过低

```
Orders filled: 5 (2.1% fill rate)
```

**解决**：
1. 降低 `base_spread`（如从 2% 降到 1.5%）
2. 降低 `order_size`（如从 20 降到 10）
3. 更换流动性更好的市场

---

**版本**: v1.0
**日期**: 2026-01-28
**作者**: Claude Code
