#!/usr/bin/env python3
"""
使用已知凭证直接测试余额查询
"""
import os
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

import requests
from datetime import datetime
import hmac
import hashlib
from urllib.parse import urlencode

from eth_account import Account

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

# 使用已知的 API 凭证
API_KEY = os.getenv("POLYMARKET_API_KEY", "e66cd14b-997d-2da4-e2f6-a5c1d411d23a")
API_SECRET = os.getenv("POLYMARKET_API_SECRET")
API_PASSPHRASE = os.getenv("POLYMARKET_PASSPHRASE")

print("=" * 80)
print("测试 Polymarket API 余额查询（使用已知凭证）")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}")
print(f"API Key: {API_KEY[:20]}...")
print(f"API Secret: {API_SECRET[:20] if API_SECRET else 'None'}...")
print(f"API Passphrase: {API_PASSPHRASE[:20] if API_PASSPHRASE else 'None'}...\n")

base_url = "https://clob.polymarket.com"
endpoint = "/balance-allowance"

# 测试 1: 使用 Signer 地址（标准方式）
print("[测试 1] 使用 Signer 地址作为 POLY_ADDRESS")
timestamp = int(datetime.now().timestamp())
method = "GET"
request_path = endpoint
body = ""

hmac_sig = hmac.new(
    API_SECRET.encode(),
    f"{timestamp}{method}{request_path}{body}".encode(),
    hashlib.sha256,
).hexdigest()

headers = {
    "POLY_ADDRESS": signer_address,
    "POLY_SIGNATURE": hmac_sig,
    "POLY_TIMESTAMP": str(timestamp),
    "POLY_API_KEY": API_KEY,
    "POLY_PASSPHRASE": API_PASSPHRASE,
}

params = {
    "asset_type": "1",  # COLLATERAL
    "signature_type": "2",
}

url = f"{base_url}{endpoint}?{urlencode(params)}"
try:
    response = requests.get(url, headers=headers, timeout=10)
    result = response.json()
    balance = result.get('balance', 'N/A')
    print(f"  返回余额: {balance}")
except Exception as e:
    print(f"  错误: {e}")

# 测试 2: 尝试在 URL 中添加 address 参数
print("\n[测试 2] 在 URL 中添加 address 参数（使用 Proxy 地址）")
params_with_address = {
    "asset_type": "1",
    "signature_type": "2",
    "address": proxy_address,  # ← 添加 address 参数
}

url2 = f"{base_url}{endpoint}?{urlencode(params_with_address)}"
try:
    response2 = requests.get(url2, headers=headers, timeout=10)
    result2 = response2.json()
    balance2 = result2.get('balance', 'N/A')
    print(f"  返回余额: {balance2}")
except Exception as e:
    print(f"  错误: {e}")

# 测试 3: 使用 Proxy 地址作为 POLY_ADDRESS（可能会 401）
print("\n[测试 3] 使用 Proxy 地址作为 POLY_ADDRESS（可能认证失败）")
timestamp3 = int(datetime.now().timestamp())
hmac_sig3 = hmac.new(
    API_SECRET.encode(),
    f"{timestamp3}{method}{request_path}{body}".encode(),
    hashlib.sha256,
).hexdigest()

headers3 = {
    "POLY_ADDRESS": proxy_address,  # ← 使用 Proxy 地址
    "POLY_SIGNATURE": hmac_sig3,
    "POLY_TIMESTAMP": str(timestamp3),
    "POLY_API_KEY": API_KEY,
    "POLY_PASSPHRASE": API_PASSPHRASE,
}

url3 = f"{base_url}{endpoint}?{urlencode(params)}"
try:
    response3 = requests.get(url3, headers=headers3, timeout=10)
    print(f"  状态码: {response3.status_code}")
    if response3.status_code == 200:
        result3 = response3.json()
        balance3 = result3.get('balance', 'N/A')
        print(f"  返回余额: {balance3}")
    else:
        print(f"  错误: {response3.text[:100]}")
except Exception as e:
    print(f"  错误: {e}")

print("\n" + "=" * 80)
print("结论:")
print("如果测试 1 和 2 都返回 0，说明 API 使用 POLY_ADDRESS 确定查询地址")
print("如果测试 3 失败（401），说明 API Key 与 Signer 地址绑定")
print("=" * 80)
