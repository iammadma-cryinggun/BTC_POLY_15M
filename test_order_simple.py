#!/usr/bin/env python3
"""
测试：直接下单，看 Polymarket API 检查的是哪个地址的余额

关键问题：虽然 get_balance_allowance 返回 Signer 的余额（0），
但实际下单时 Polymarket API 是检查 Signer 余额还是 Funder 余额？
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from dotenv import load_dotenv
load_dotenv()

# 导入修补模块
import patches.py_clob_client_patch  # noqa: F401

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType, OrderArgs

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("测试：Polymarket API 检查哪个地址的余额？")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy (Funder): {proxy_address}\n")

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

# 查询余额（预期返回 Signer 的余额 = 0）
print("[步骤 1] 查询余额...")
try:
    result = client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    balance = result.get('balance', 'N/A')
    print(f"  Signer 余额: {balance} USDC.e")
    print(f"  [预期] Signer 余额应该为 0（资金在 Proxy 地址）")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")
    exit(1)

# 尝试下单 - 使用一个可能存在的 token ID
print("\n[步骤 2] 尝试下单...")
print("  Token ID: 73470541315377973562501025254719659796416871135081220986683321361000395461644")
print("  (这是一个已关闭的市场，用于测试 API 响应)")

try:
    order_args = OrderArgs(
        token_id="73470541315377973562501025254719659796416871135081220986683321361000395461644",
        size=0.01,
        price=0.50,
        side="BUY",
    )

    response = client.create_order(order_args)
    print(f"\n  [意外] 订单被接受!")
    print(f"    Response: {response}")
    print(f"    [结论] API 没有检查余额（或市场未关闭）")

except Exception as e:
    error_msg = str(e)
    print(f"\n  [预期] 订单被拒绝")
    print(f"    错误类型: {type(e).__name__}")
    print(f"    错误信息: {error_msg[:300]}")

    # 分析错误信息
    error_lower = error_msg.lower()

    if "balance" in error_lower or "insufficient" in error_lower:
        print(f"\n  [关键发现]")
        print(f"    错误包含 'balance' 或 'insufficient'")
        print(f"    这说明 Polymarket API **确实检查了余额**")

        # 检查错误信息中是否提到了地址
        if proxy_address.lower() in error_lower:
            print(f"    错误信息包含 Proxy 地址 → API 检查的是 **Proxy 余额** ✓")
            print(f"    [结论] 解决方案：修复余额查询逻辑，使其返回 Proxy 余额")
        elif signer_address.lower() in error_lower:
            print(f"    错误信息包含 Signer 地址 → API 检查的是 **Signer 余额**")
            print(f"    [结论] 解决方案：需要将资金从 Proxy 转移到 Signer")
        else:
            print(f"    错误信息不包含具体地址")
            print(f"    [需要进一步调查] API 检查的是哪个地址的余额？")

    elif "market" in error_lower or "closed" in error_lower or "inactive" in error_lower:
        print(f"\n  [关键发现]")
        print(f"    错误是关于市场状态（已关闭/不活跃），而不是余额")
        print(f"    这说明 API **没有检查余额**就拒绝了订单")
        print(f"    [结论] 如果市场是活跃的，API 可能会接受订单")

        print(f"\n  [下一步]")
        print(f"    需要找到一个活跃的市场并重新测试")
        print(f"    或者：检查 Polymarket 网站看是否有活跃的 BTC 市场")

    else:
        print(f"\n  [需要分析]")
        print(f"    其他类型的错误，无法确定余额检查行为")

print("\n" + "=" * 80)
print("测试总结")
print("=" * 80)
print("""
如果错误包含 "balance/insufficient":
  → Polymarket API 检查余额
  → 需要确定检查的是 Signer 还是 Proxy 余额

如果错误包含 "market/closed/inactive":
  → Polymarket API 因为市场状态拒绝订单
  → 可能没有检查余额（或余额检查在市场检查之后）

如果订单被接受：
  → API 不检查余额，或余额检查通过了
  → 需要查看订单是否真的被执行
""")
