"""
从私钥推导钱包地址
"""

import os
from pathlib import Path

project_root = Path(__file__).parent

# 加载私钥
private_key = os.getenv("POLYMARKET_PK")
if not private_key:
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if line.startswith('POLYMARKET_PK='):
                    private_key = line.split('=', 1)[1].strip()
                    break

if not private_key:
    print("[ERROR] 未找到私钥")
    exit(1)

print(f"[OK] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

# 推导钱包地址
try:
    from eth_account import Account
    account = Account.from_key(private_key)
    address = account.address

    print("\n" + "=" * 80)
    print("[OK] Wallet address derived successfully!")
    print("=" * 80)
    print(f"\nWallet address: {address}")
    print(f"\nPlease configure the following environment variable in Zeabur:\n")
    print(f"POLYMARKET_FUNDER={address}")
    print("\n" + "=" * 80)
    print("Instructions:")
    print("=" * 80)
    print("1. Copy the environment variable above")
    print("2. Add it in Zeabur project settings")
    print("3. Save and redeploy\n")

except Exception as e:
    print(f"[ERROR] 推导失败: {e}")
    import traceback
    traceback.print_exc()
