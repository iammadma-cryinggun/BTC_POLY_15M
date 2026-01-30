#!/usr/bin/env python3
"""
通过分析交易历史来计算实际余额
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from dotenv import load_dotenv
load_dotenv()

import patches.py_clob_client_patch  # noqa: F401

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds

private_key = os.getenv("POLYMARKET_PK")
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("通过交易历史计算 Proxy 地址的实际余额")
print("=" * 80)

# 创建客户端
client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
)

creds = client.create_or_derive_api_creds()

api_creds = ApiCreds(
    api_key=creds.api_key,
    api_secret=creds.api_secret,
    api_passphrase=creds.api_passphrase,
)

client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
    creds=api_creds,
)

print("\n[步骤 1] 获取所有交易...")
trades = client.get_trades()
print(f"  总交易数: {len(trades)}")

if not trades or len(trades) == 0:
    print("  [错误] 没有交易历史")
    exit(1)

print("\n[步骤 2] 分析交易...")

# 统计
total_buy_spent = 0.0  # 买入花费的 USDC
total_sell_earned = 0.0  # 卖出获得的 USDC
total_fees = 0.0  # 总手续费

for trade in trades:
    side = trade.get('side')
    size = float(trade.get('size', 0))
    price = float(trade.get('price', 0))
    fee_rate_bps = int(trade.get('fee_rate_bps', 0))

    # 计算交易金额
    notional = size * price

    # 计算手续费 (fee_rate_bps 是基点，1000 bps = 10%)
    fee = notional * (fee_rate_bps / 10000.0)

    if side == 'BUY':
        # 买入：花费 notional + fee
        total_buy_spent += notional + fee
    elif side == 'SELL':
        # 卖出：获得 notional - fee
        total_sell_earned += notional - fee

    total_fees += fee

# 计算净额
net_change = total_sell_earned - total_buy_spent

print(f"\n  交易统计:")
print(f"    买入总额: ${total_buy_spent:.4f} USDC (含手续费)")
print(f"    卖出总额: ${total_sell_earned:.4f} USDC (扣除手续费)")
print(f"    总手续费: ${total_fees:.4f} USDC")
print(f"    净变化: ${net_change:+.4f} USDC")

print("\n[步骤 3] 查询当前 Signer 余额...")
from py_clob_client.clob_types import BalanceAllowanceParams, AssetType
result = client.get_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
)
signer_balance = int(result.get('balance', 0)) / 1_000_000  # 转换为 USDC
print(f"  Signer 余额: ${signer_balance:.4f} USDC.e")

print("\n[步骤 4] 计算实际余额...")

# 关键问题：我们需要知道初始余额
# 由于 Proxy 地址的余额无法直接查询，我们需要估算
print("\n  [问题] Proxy 地址的初始余额未知")
print(f"  [分析]")
print(f"    - 如果 Signer 有余额，那是系统转账或错误")
print(f"    - Proxy 地址的实际余额应该是：初始余额 + {net_change:+.4f}")

# 假设：所有交易都通过 Proxy 进行
# 那么净变化就是 Proxy 地址的余额变化
print(f"\n  [假设] 如果所有交易都通过 Proxy 地址进行:")
print(f"    - Proxy 余额变化: {net_change:+.4f} USDC")
print(f"    - 但我们仍然不知道初始余额")

# 尝试另一种方法：检查是否有充值记录
print("\n[步骤 5] 检查最早和最近的交易...")
trades_sorted = sorted(trades, key=lambda t: int(t.get('match_time', 0)))
earliest = trades_sorted[0]
latest = trades_sorted[-1]

from datetime import datetime
earliest_time = datetime.fromtimestamp(int(earliest.get('match_time', 0)))
latest_time = datetime.fromtimestamp(int(latest.get('match_time', 0)))

print(f"  最早交易: {earliest_time}")
print(f"    {earliest.get('side')} {earliest.get('size')} @ ${earliest.get('price')}")
print(f"  最近交易: {latest_time}")
print(f"    {latest.get('side')} {latest.get('size')} @ ${latest.get('price')}")

print("\n" + "=" * 80)
print("结论")
print("=" * 80)
print(f"""
通过分析 {len(trades)} 条交易历史：

1. 交易活动:
   - 总买入: ${total_buy_spent:.2f}
   - 总卖出: ${total_sell_earned:.2f}
   - 净变化: ${net_change:+.2f}

2. 余额计算问题:
   - 无法通过交易历史确定初始余额
   - 只能看到余额的净变化

3. 可能的解决方案:
   A. 检查 Polymarket 网站看当前余额
   B. 使用 Polymarket 的其他 API 端点
   C. 联系 Polymarket 支持获取账户信息
   D. 使用虚拟余额绕过 NautilusTrader 的检查（让 Polymarket API 自己验证）

4. 建议:
   由于无法自动确定初始余额，最佳方案是：
   → 使用虚拟余额（如 1000 USDC）让 NautilusTrader 放行订单
   → 让 Polymarket API 自己验证 Funder 的实际余额
   → 如果余额不足，Polymarket API 会拒绝订单并返回错误
""")
