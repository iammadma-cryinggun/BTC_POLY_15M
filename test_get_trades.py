#!/usr/bin/env python3
"""
测试：通过查询交易历史来计算 Proxy 地址的实际余额

思路：
  1. 查询所有历史交易
  2. 计算买入总额、卖出总额、费用
  3. 推算当前余额
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
print("测试：查询交易历史以计算实际余额")
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

print("\n[测试 1] 查询交易历史 (get_trades)...")
try:
    trades = client.get_trades()
    print(f"  交易数量: {len(trades) if trades else 0}")

    if trades and len(trades) > 0:
        print(f"\n  最近的交易:")
        for i, trade in enumerate(trades[:5]):  # 显示前 5 个
            print(f"    [{i+1}] {trade}")

        # 分析交易
        total_spent = 0
        total_earned = 0
        for trade in trades:
            if hasattr(trade, 'side'):
                if trade.side == 'BUY':
                    total_spent += trade.price * trade.size
                elif trade.side == 'SELL':
                    total_earned += trade.price * trade.size

        print(f"\n  统计:")
        print(f"    总买入: ${total_spent:.2f}")
        print(f"    总卖出: ${total_earned:.2f}")
        print(f"    净额: ${total_earned - total_spent:.2f}")
    else:
        print(f"  [提示] 没有找到交易历史")

except Exception as e:
    error_msg = str(e)
    print(f"  错误: {error_msg[:200]}")

    # 检查是否是认证错误
    if '401' in error_msg or 'unauthorized' in error_msg.lower():
        print(f"\n  [问题] 认证失败")
        print(f"  [说明] 可能需要使用不同的 API 凭证")

print("\n[测试 2] 查询 builder trades...")
try:
    builder_trades = client.get_builder_trades()
    print(f"  Builder trades 数量: {len(builder_trades) if builder_trades else 0}")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

print("\n" + "=" * 80)
print("结论")
print("=" * 80)
print("""
如果能获取交易历史：
  → 可以通过分析历史交易来计算当前余额
  → 但这需要初始余额作为基准

如果没有交易历史：
  → 说明账户可能是新账户或没有交易记录
  → 余额应该是初始充值金额

如果查询失败（401/403）：
  → 说明当前 API 凭证无法查询交易历史
  → 可能需要使用不同的认证方式
""")
