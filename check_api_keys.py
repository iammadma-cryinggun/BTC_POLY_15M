#!/usr/bin/env python3
"""
检查现有的 API Keys
"""
import os
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from eth_account import Account
from py_clob_client.client import ClobClient

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address

print("=" * 80)
print("检查现有的 API Keys")
print("=" * 80)
print(f"\n钱包地址: {signer_address}\n")

# 创建客户端并推导 API Key
client = ClobClient(
    "https://clob.polymarket.com",
    key=private_key,
    signature_type=2,
    chain_id=137,
)

try:
    # 先推导现有的 API Key
    print("[步骤 1] 推导现有的 API Key...")
    creds = client.create_or_derive_api_creds()
    print(f"  API Key: {creds.api_key[:20]}...")

    # 创建带凭证的客户端
    from py_clob_client.clob_types import ApiCreds
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
        creds=api_creds,
    )

    # 获取 API Keys
    print("\n[步骤 2] 获取所有的 API Keys...")
    api_keys = client_with_creds.get_api_keys()

    print(f"\n找到 {len(api_keys)} 个 API Key:\n")
    for i, api_key in enumerate(api_keys, 1):
        print(f"  [{i}] API Key: {api_key[:20]}...")
        print()

    # 尝试删除所有旧的 API Keys
    if len(api_keys) > 0:
        print("[步骤 3] 删除所有旧的 API Keys...")
        for api_key in api_keys:
            try:
                client_with_creds.delete_api_key()
                print(f"  [成功] 删除 API Key: {api_key[:20]}...")
            except Exception as e:
                print(f"  [失败] {api_key[:20]}... - {e}")

        print("\n[步骤 4] 创建新的 API Key...")
        try:
            new_creds = client_with_creds.create_api_key()
            print(f"\n  [成功] 创建了新的 API Key!")
            print(f"  API Key: {new_creds.api_key}")
            print(f"  Secret: {new_creds.api_secret}")
            print(f"  Passphrase: {new_creds.api_passphrase}")
            print("\n[重要] 请保存这些凭证并添加到 Zeabur 环境变量:")
            print(f"  POLYMARKET_API_KEY={new_creds.api_key}")
            print(f"  POLYMARKET_API_SECRET={new_creds.api_secret}")
            print(f"  POLYMARKET_PASSPHRASE={new_creds.api_passphrase}")
        except Exception as e:
            print(f"  [失败] {e}")
            print("\n可能需要到 https://polymarket.com/settings/api-keys 手动管理")

except Exception as e:
    print(f"[错误] {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
