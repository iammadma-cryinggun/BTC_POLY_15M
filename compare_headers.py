#!/usr/bin/env python3
"""
对比 get_orders 和 get_balance_allowance 的 HTTP 请求头
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
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("对比 HTTP 请求头")
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

client_with_creds = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
    creds=api_creds,
)

# Monkey patch 来拦截 HTTP 请求
from py_clob_client.http_helpers import helpers as http_helpers
original_get = http_helpers.get

def patched_get(url, headers):
    print(f"\n[HTTP GET] {url}")
    print(f"[Headers]")
    for key, value in headers.items():
        if key == "POLY_ADDRESS":
            print(f"  {key}: {value} {'<- PROXY' if value == proxy_address else '<- SIGNER'}")
        else:
            print(f"  {key}: {value[:20]}..." if len(str(value)) > 20 else f"  {key}: {value}")
    return original_get(url, headers)

http_helpers.get = patched_get

# 测试 get_orders
print("\n" + "=" * 80)
print("测试 1: get_orders()")
print("=" * 80)
try:
    result = client_with_creds.get_orders([])
    print(f"\n[结果] 成功 - {len(result)} 个订单")
except Exception as e:
    print(f"\n[结果] 失败 - {e}")

# 测试 get_balance_allowance
print("\n" + "=" * 80)
print("测试 2: get_balance_allowance()")
print("=" * 80)
try:
    result = client_with_creds.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )
    print(f"\n[结果] 成功 - balance: {result.get('balance', 'N/A')}")
except Exception as e:
    print(f"\n[结果] 失败 - {e}")

print("\n" + "=" * 80)
