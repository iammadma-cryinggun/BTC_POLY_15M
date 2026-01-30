#!/usr/bin/env python3
"""
测试 API Key 与地址的绑定关系

假设：API Key 与推导时使用的钱包地址绑定
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# 应用补丁
import patches  # noqa: F401

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("API Key 绑定测试")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}\n")

# 创建客户端（不使用 funder）推导 API Key
print("[步骤 1] 推导 API Key（不使用 funder）...")
client1 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
)
creds1 = client1.create_or_derive_api_creds()
print(f"  API Key: {creds1.api_key[:10]}...")

# 测试 1: 使用 Signer 地址
print("\n[测试 1] 使用 Signer 地址发送请求...")
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
    funder=signer_address,  # ← 使用 Signer 地址
    creds=api_creds1,
)
try:
    result = client_test1.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    print(f"  [成功] Balance: {result.get('balance', 'N/A')}")
except Exception as e:
    print(f"  [失败] {str(e)[:80]}")

# 测试 2: 使用 Proxy 地址
print("\n[测试 2] 使用 Proxy 地址发送请求...")
client_test2 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,  # ← 使用 Proxy 地址
    creds=api_creds1,  # ← 使用相同的 API Key
)
try:
    result = client_test2.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    print(f"  [成功] Balance: {result.get('balance', 'N/A')}")
except Exception as e:
    print(f"  [失败] {str(e)[:80]}")

print("\n" + "=" * 80)
print("结论:")
print("如果测试 1 成功但测试 2 失败，说明 API Key 与地址绑定")
print("=" * 80)
