#!/usr/bin/env python3
"""
诊断 401 错误的精确位置

测试所有需要 Level 2 认证的 API 调用
"""
import os
import sys
from pathlib import Path

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# 应用补丁
import patches  # noqa: F401

from eth_account import Account
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds, BalanceAllowanceParams, AssetType

private_key = os.getenv("POLYMARKET_PK")
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("401 错误诊断 - 测试所有 Level 2 API")
print("=" * 80)
print(f"\nSigner: {Account.from_key(private_key).address}")
print(f"Proxy:  {proxy_address}\n")

# 创建客户端（带 funder）
print("[1/5] 创建 ClobClient（带 funder）...")
client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
    funder=proxy_address,
)

# 推导 API Key
print("[2/5] 推导 API Key...")
creds = client.create_or_derive_api_creds()
print(f"  API Key: {creds.api_key[:10]}...")

# 创建带凭证的客户端
print("[3/5] 创建带凭证的客户端...")
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

# 测试各个 API
print("\n[4/5] 测试 Level 2 API 调用...")

tests = [
    ("get_orders", lambda: client_with_creds.get_orders([])),
    ("get_balance_allowance", lambda: client_with_creds.get_balance_allowance(
        BalanceAllowanceParams(asset_type=AssetType.COLLATERAL, signature_type=2)
    )),
]

for name, func in tests:
    print(f"\n  测试 {name}()...")
    try:
        result = func()
        print(f"    [OK] 成功！")
        if isinstance(result, dict):
            print(f"    返回: {list(result.keys())}")
        elif isinstance(result, list):
            print(f"    返回: {len(result)} 项")
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"    [401 ERROR] {error_msg[:100]}")
        else:
            print(f"    [ERROR] {error_msg[:100]}")

print("\n[5/5] 检查 builder.funder...")
print(f"  builder 存在: {hasattr(client_with_creds, 'builder')}")
if hasattr(client_with_creds, 'builder'):
    print(f"  builder.funder: {client_with_creds.builder.funder}")

print("\n" + "=" * 80)
print("诊断完成")
print("=" * 80)
