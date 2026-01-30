#!/usr/bin/env python3
"""
手动测试 Polymarket API 的余额查询
尝试不同的方式来查询 Proxy 地址的余额
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import requests
from datetime import datetime
import hmac
import hashlib
from urllib.parse import urlencode

from eth_account import Account
from py_clob_client.signer import Signer
from py_clob_client.clob_types import ApiCreds

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("手动测试 Polymarket API 余额查询")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}\n")

# 推导 API Key
from py_clob_client.client import ClobClient
client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
)
creds = client.create_or_derive_api_creds()

base_url = "https://clob.polymarket.com"
endpoint = "/balance-allowance"

# 测试 1: 使用 Signer 地址（标准方式）
print("[测试 1] 使用 Signer 地址作为 POLY_ADDRESS")
timestamp = int(datetime.now().timestamp())
method = "GET"
request_path = endpoint

body = ""
hmac_sig = hmac.new(
    creds.api_secret.encode(),
    f"{timestamp}{method}{request_path}{body}".encode(),
    hashlib.sha256,
).hexdigest()

headers1 = {
    "POLY_ADDRESS": signer_address,
    "POLY_SIGNATURE": hmac_sig,
    "POLY_TIMESTAMP": str(timestamp),
    "POLY_API_KEY": creds.api_key,
    "POLY_PASSPHRASE": creds.api_passphrase,
}

params = {
    "asset_type": "1",  # COLLATERAL
    "signature_type": "2",
}

url1 = f"{base_url}{endpoint}?{urlencode(params)}"
response1 = requests.get(url1, headers=headers1)
result1 = response1.json()
balance1 = result1.get('balance', 'N/A')
print(f"  返回余额: {balance1}")

# 测试 2: 尝试在 URL 中添加 address 参数
print("\n[测试 2] 尝试在 URL 中添加 address 参数")
params_with_address = {
    "asset_type": "1",
    "signature_type": "2",
    "address": proxy_address,  # ← 添加 address 参数
}

url2 = f"{base_url}{endpoint}?{urlencode(params_with_address)}"
response2 = requests.get(url2, headers=headers1)
result2 = response2.json()
balance2 = result2.get('balance', 'N/A')
print(f"  返回余额: {balance2}")

# 测试 3: 使用 Proxy 地址作为 POLY_ADDRESS（可能会 401）
print("\n[测试 3] 使用 Proxy 地址作为 POLY_ADDRESS（可能认证失败）")
timestamp3 = int(datetime.now().timestamp())
hmac_sig3 = hmac.new(
    creds.api_secret.encode(),
    f"{timestamp3}{method}{request_path}{body}".encode(),
    hashlib.sha256,
).hexdigest()

headers3 = {
    "POLY_ADDRESS": proxy_address,  # ← 使用 Proxy 地址
    "POLY_SIGNATURE": hmac_sig3,
    "POLY_TIMESTAMP": str(timestamp3),
    "POLY_API_KEY": creds.api_key,
    "POLY_PASSPHRASE": creds.api_passphrase,
}

url3 = f"{base_url}{endpoint}?{urlencode(params)}"
response3 = requests.get(url3, headers=headers3)
print(f"  状态码: {response3.status_code}")
if response3.status_code == 200:
    result3 = response3.json()
    balance3 = result3.get('balance', 'N/A')
    print(f"  返回余额: {balance3}")
else:
    print(f"  错误: {response3.text[:100]}")

print("\n" + "=" * 80)
print("结论:")
if int(balance1) == 0 and int(balance2) == 0 and response3.status_code == 401:
    print("  无法查询 Proxy 地址的余额 - API 设计限制")
    print("  解决方案: 需要将资金转到 Signer 地址，或使用其他方法")
elif response3.status_code == 200:
    balance3 = response3.json().get('balance', 'N/A')
    if int(balance3) > 0:
        print("  可以使用 Proxy 地址作为 POLY_ADDRESS - 需要修改代码")
print("=" * 80)
