#!/usr/bin/env python3
"""
测试：使用 Funder 地址推导 API Key

假设：如果使用 funder 地址初始化客户端，API Key 应该与 funder 关联
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("测试：使用 Funder 地址推导 API Key")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}\n")

# 测试 1: 使用 Signer 地址初始化并推导 API Key
print("[测试 1] 使用 Signer 地址初始化")
client1 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
)
creds1 = client1.create_or_derive_api_creds()
print(f"  API Key: {creds1.api_key}")
print(f"  Signer: {signer_address}")

# 查询余额
print(f"\n  [查询余额] 使用 Signer 地址的 API Key...")
api_creds1 = ApiCreds(
    api_key=creds1.api_key,
    api_secret=creds1.api_secret,
    api_passphrase=creds1.api_passphrase,
)
client_test1 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    creds=api_creds1,
)
try:
    result1 = client_test1.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    balance1 = result1.get('balance', 'N/A')
    print(f"  结果: {balance1} USDC.e")
except Exception as e:
    print(f"  错误: {str(e)[:100]}")

# 测试 2: 使用 Funder 地址初始化并推导 API Key
print(f"\n[测试 2] 使用 Funder (Proxy) 地址初始化")
client2 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,  # ← 传入 funder
)
creds2 = client2.create_or_derive_api_creds()
print(f"  API Key: {creds2.api_key}")
print(f"  Funder: {proxy_address}")

# 关键检查：API Key 是否相同？
print(f"\n  [对比] API Key 是否相同: {creds1.api_key == creds2.api_key}")
if creds1.api_key != creds2.api_key:
    print(f"  [发现] 使用 funder 初始化生成了不同的 API Key!")
    print(f"  Signer API Key:  {creds1.api_key}")
    print(f"  Funder API Key:  {creds2.api_key}")

# 使用 Funder API Key 查询余额
print(f"\n  [查询余额] 使用 Funder 地址的 API Key...")
api_creds2 = ApiCreds(
    api_key=creds2.api_key,
    api_secret=creds2.api_secret,
    api_passphrase=creds2.api_passphrase,
)
client_test2 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
    creds=api_creds2,
)
try:
    result2 = client_test2.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    balance2 = result2.get('balance', 'N/A')
    print(f"  结果: {balance2} USDC.e")

    if int(balance2) > 0:
        print(f"\n  [成功] 使用 Funder API Key 查询到了余额!")
        print(f"  [结论] 需要使用 Funder 地址初始化客户端并推导 API Key")
    else:
        print(f"\n  [问题] 余额仍为 0")
except Exception as e:
    print(f"  错误: {str(e)[:200]}")

print("\n" + "=" * 80)
print("结论:")
print("如果测试 2 生成了不同的 API Key 并且查询到了余额，")
print("说明解决方案是：使用 Funder 地址初始化客户端并推导 API Key")
print("=" * 80)
