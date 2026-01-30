#!/usr/bin/env python3
"""
测试：直接下单，绕过余额检查

假设：虽然 get_balance_allowance 返回 Signer 的余额（0），
但实际下单时 Polymarket API 会检查 Funder 的余额
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# 导入修补模块（必须在导入 py_clob_client 之前）
import patches.py_clob_client_patch  # noqa: F401

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType, OrderArgs

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("测试：直接下单（绕过余额检查）")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}\n")

# 创建客户端（使用 funder）
print("[1/4] 创建 ClobClient（使用 funder）...")
client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,  # ← 关键：传入 funder
)

# 推导 API credentials
print("[2/4] 推导 API credentials...")
creds = client.create_or_derive_api_creds()
print(f"  API Key: {creds.api_key}")

# 使用 API credentials 重新创建客户端
print("[3/4] 重新创建客户端（使用 API credentials）...")
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

# 查询余额（预期返回 0）
print("[4/4] 查询余额（预期返回 0）...")
try:
    result = client.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    balance = result.get('balance', 'N/A')
    print(f"  Signer 余额: {balance} USDC.e")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

# 尝试下单 - 使用 BTC 市场（token ID: 47193）
print("\n" + "=" * 80)
print("[测试] 尝试下单（BTC 市场，最小金额）")
print("=" * 80)

# 获取市场信息
token_id = "47193"  # BTC > $100k by end of 2026
print(f"\nToken ID: {token_id}")
print("准备下单...")

try:
    # 获取市场信息
    from py_clob_client.constants import POLYGON
    markets_response = client.get_markets()

    # 打印响应类型以便调试
    print(f"  [DEBUG] markets_response type: {type(markets_response)}")

    # 处理响应
    if isinstance(markets_response, dict) and 'data' in markets_response:
        markets = markets_response['data']
    elif isinstance(markets_response, list):
        markets = markets_response
    else:
        print(f"  [错误] 无法解析市场响应")
        print(f"    响应类型: {type(markets_response)}")
        markets = []

    btc_market = None
    for m in markets:
        if isinstance(m, dict):
            tid = m.get('token_id') or m.get('condition_id')
            if tid == token_id:
                btc_market = m
                break

    if btc_market:
        print(f"  市场: {btc_market.get('question', 'N/A')}")
        print(f"  Tick size: {btc_market.get('tick_size', 'N/A')}")
        print(f"  Min order size: {btc_market.get('min_order_size', 'N/A')}")

        # 尝试创建一个小订单（0.01 USDC，极小金额测试）
        print(f"\n  创建订单:")
        print(f"    Side: BUY")
        print(f"    Size: 0.01 shares")
        print(f"    Price: $0.50")
        print(f"    Notional: $0.005")

        order_args = OrderArgs(
            token_id=token_id,
            amount=0.01,  # 极小金额
            price=0.50,   # 50 cents
            side=1,       # BUY
            order_type=0, # GTC
        )

        response = client.create_order(order_args)
        print(f"\n  [成功] 订单已创建!")
        print(f"    Response: {response}")
        print(f"    [结论] Polymarket API 接受了订单！")
        print(f"    [说明] API 内部检查的是 Funder 余额，而非 Signer 余额")

    else:
        print(f"  [错误] 未找到市场 {token_id}")
        print(f"    可用市场数量: {len(markets)}")
        if len(markets) > 0:
            print(f"    第一个市场: {markets[0]}")

except Exception as e:
    error_msg = str(e)
    print(f"\n  [失败] 订单被拒绝")
    print(f"    错误: {error_msg[:200]}")

    if "balance" in error_msg.lower() or "insufficient" in error_msg.lower():
        print(f"\n    [结论] Polymarket API 检查的是 Signer 余额（为 0）")
        print(f"    [说明] 需要将资金从 Proxy 转移到 Signer 地址")
    else:
        print(f"\n    [结论] 其他错误（需要进一步调查）")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
