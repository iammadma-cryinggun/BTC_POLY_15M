#!/usr/bin/env python3
"""
测试：查询订单和其他信息，看是否可以间接获取 Funder 余额
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
print("测试：查询各种端点，寻找 Funder 余额信息")
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

print("\n[测试 1] 查询开放订单...")
try:
    orders = client.get_orders()
    print(f"  订单数量: {len(orders) if orders else 0}")
    if orders:
        print(f"  第一个订单: {orders[0]}")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

print("\n[测试 2] 查询地址信息...")
try:
    address = client.get_address()
    print(f"  Address: {address}")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

print("\n[测试 3] 检查 builder.funder...")
try:
    if hasattr(client, 'builder') and client.builder:
        funder = client.builder.funder
        print(f"  Builder.funder: {funder}")
        print(f"  [确认] Funder 地址已设置")
    else:
        print(f"  [警告] Builder 或 funder 未设置")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

print("\n[测试 4] 尝试使用 funder 地址创建新的 API credentials...")
try:
    # 看看传入不同的 address 参数是否会生成不同的 API key
    from py_clob_client.signing.hmac import build_api_key_creds

    # 使用 signer address
    creds1 = build_api_key_creds(private_key, 0)
    print(f"  API Key (nonce=0): {creds1.api_key}")

    # 使用 different nonce
    creds2 = build_api_key_creds(private_key, 1)
    print(f"  API Key (nonce=1): {creds2.api_key}")

    if creds1.api_key != creds2.api_key:
        print(f"  [发现] 不同 nonce 生成不同的 API key")
        print(f"  [说明] 可能可以使用不同的 API key 来查询不同的地址")
    else:
        print(f"  [说明] nonce 不影响 API key 生成")

except Exception as e:
    print(f"  错误: {str(e)[:100]}")

print("\n" + "=" * 80)
print("关键发现总结")
print("=" * 80)
print("""
如果 get_orders() 成功返回订单：
  → 说明认证成功，API 正常工作

如果 builder.funder 已正确设置：
  → 说明客户端配置正确

下一步：
  → 检查 NautilusTrader 是否正确使用了 builder.funder
  → 可能需要修改 NautilusTrader 的余额查询逻辑
  → 或者：使用不同的方法获取 Funder 的余额
""")
