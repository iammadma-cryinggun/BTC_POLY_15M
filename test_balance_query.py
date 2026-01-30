#!/usr/bin/env python3
"""
测试余额查询是否使用 POLY_ADDRESS 头确定查询地址
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
print("测试余额查询的地址")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}")
print(f"预期 Proxy 余额: 17.75 USDC.e\n")

# 创建客户端（使用 Proxy 作为 funder）
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

client_with_creds = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
    creds=api_creds,
)

# 查询余额
print("[测试] 查询余额...")
result = client_with_creds.get_balance_allowance(
    BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
)

balance = result.get('balance', 'N/A')
print(f"\n返回的余额: {balance}")

if int(balance) == 0:
    print("\n[问题] 余额为 0 - 说明查询的是 Signer 地址，不是 Proxy 地址")
    print("\n需要检查 API 是否需要在 URL 参数中指定查询地址")
elif int(balance) > 0:
    print(f"\n[成功] 余额为 {balance} - 说明正确查询了 Proxy 地址")

print("\n" + "=" * 80)
