#!/usr/bin/env python3
"""
Zeabur 完整测试脚本
输出所有配置信息
"""
import os
import sys
from pathlib import Path

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
from dotenv import load_dotenv
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
    print(f"[INFO] 已加载 .env 文件")

print("=" * 80)
print("Zeabur 完整配置检查")
print("=" * 80)

# 1. 环境变量
print("\n[1] 环境变量:")
print(f"  POLYMARKET_PK: {os.getenv('POLYMARKET_PK', 'NOT SET')[:20]}...")
print(f"  POLYMARKET_PROXY_ADDRESS: {os.getenv('POLYMARKET_PROXY_ADDRESS', 'NOT SET')}")
print(f"  POLYMARKET_FUNDER: {os.getenv('POLYMARKET_FUNDER', 'NOT SET')}")
print(f"  POLYMARKET_API_KEY: {os.getenv('POLYMARKET_API_KEY', 'NOT SET')[:20] if os.getenv('POLYMARKET_API_KEY') else 'NOT SET'}")

# 2. 加载私钥
private_key = os.getenv("POLYMARKET_PK")
if not private_key:
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('POLYMARKET_PK='):
                    private_key = line.split('=', 1)[1].strip()
                    break

if not private_key:
    print("\n[ERROR] 未找到私钥")
    sys.exit(1)

print(f"\n[2] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

# 3. 推导地址
from eth_account import Account
account = Account.from_key(private_key)
signer_address = account.address
print(f"\n[3] 地址推导:")
print(f"  Signer address: {signer_address}")

# 4. 检查 Proxy 地址
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")
if proxy_address:
    print(f"\n[4] Proxy 地址:")
    print(f"  配置的 Proxy: {proxy_address}")
    print(f"  将使用 Proxy 作为 funder")
    os.environ['POLYMARKET_FUNDER'] = proxy_address
else:
    print(f"\n[4] Proxy 地址:")
    print(f"  未配置 POLYMARKET_PROXY_ADDRESS")
    print(f"  将使用 Signer 作为 funder")
    os.environ['POLYMARKET_FUNDER'] = signer_address

print(f"\n[5] 最终 funder:")
print(f"  {os.getenv('POLYMARKET_FUNDER')}")

# 6. 测试 API
print(f"\n[6] 测试 Polymarket API...")
try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds

    client = ClobClient(
        "https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
    )

    # Derive API keys
    creds = client.derive_api_key()
    print(f"  API Key derived: {creds.api_key[:10]}...")

    # Create client with creds
    api_creds = ApiCreds(
        api_key=creds.api_key,
        api_secret=creds.api_secret,
        api_passphrase=creds.api_passphrase,
    )

    client_with_creds = ClobClient(
        "https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
        creds=api_creds,
    )

    # Test get_orders
    orders = client_with_creds.get_orders([])
    print(f"  Orders: {len(orders)} found")
    print(f"  [SUCCESS] API Key 有效！")

except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
