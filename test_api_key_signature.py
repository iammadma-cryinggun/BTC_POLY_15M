#!/usr/bin/env python3
"""
测试 API Key 与地址的绑定关系
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
from eth_account import Account

load_dotenv()
private_key = os.getenv("POLYMARKET_PK")

# 推导地址
account = Account.from_key(private_key)
signer_address = account.address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("API Key 与地址绑定测试")
print("=" * 80)
print(f"\nSigner address: {signer_address}")
print(f"Proxy address:  {proxy_address}")

from py_clob_client.client import ClobClient

# 测试 1: 不使用 funder 推导 API Key
print("\n[测试 1] 推导 API Key（不使用 funder）...")
client1 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
)
creds1 = client1.create_or_derive_api_creds()
print(f"  API Key: {creds1.api_key[:10]}...")

# 测试 2: 使用 funder 推导 API Key
print("\n[测试 2] 推导 API Key（使用 funder）...")
client2 = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
)
creds2 = client2.create_or_derive_api_creds()
print(f"  API Key: {creds2.api_key[:10]}...")

print(f"\n[结论] API Key 是否相同: {creds1.api_key == creds2.api_key}")

if creds1.api_key == creds2.api_key:
    print("\n✅ API Key 相同 - 说明 API Key 与 funder 参数无关")
    print("   问题可能出在 HTTP 请求的签名地址上")
else:
    print("\n❌ API Key 不同 - 说明 API Key 与 funder 参数相关")
    print("   必须在推导 API Key 时使用正确的 funder")

print("=" * 80)
