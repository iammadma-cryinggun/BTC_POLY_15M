"""
直接查询 Proxy 地址余额
"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 直接设置 Proxy 地址
PROXY_ADDRESS = "0x18DdcbD977e5b7Ff751A3BAd6F274b67A311CD2d"

def main():
    print("=" * 80)
    print(f"查询 Proxy 地址余额: {PROXY_ADDRESS}")
    print("=" * 80)

    # 加载私钥
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
        print("[ERROR] 未找到私钥")
        return 1

    print(f"[OK] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

    # 使用 py_clob_client 查询余额
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON

        print("\n[1] 创建 ClobClient...")
        client = ClobClient(
            "https://clob.polymarket.com",
            key=str(private_key),
            signature_type=2,  # Magic Wallet
            chain_id=POLYGON,
        )

        print("[2] 获取 API 凭证...")
        api_creds = client.create_or_derive_api_creds()
        print(f"    API Key: {api_creds.api_key[:10]}...")

        print("\n[3] 查询余额...")
        balance_response = client.get_balance()

        print("\n=== 原始余额响应 ===")
        import json
        print(json.dumps(balance_response, indent=2, default=str))

        # 尝试直接调用 Polymarket API 查询 Proxy 地址余额
        print("\n=== 尝试直接查询 Proxy 地址余额 ===")
        try:
            # Polymarket Gamma API
            import requests

            headers = {
                'x-polymarket-access-key': api_creds.api_key,
                'x-polymarket-secret-key': api_creds.api_secret,
                'x-polymarket-passphrase': api_creds.passphrase,
            }

            # 查询账户余额
            url = "https://gamma-api.polymarket.com/wallets/balances"
            response = requests.get(url, headers=headers, timeout=10)

            print(f"\nGamma API 响应:")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(json.dumps(data, indent=2, default=str))
            else:
                print(f"Error: {response.text}")

        except Exception as e:
            print(f"[ERROR] Gamma API 查询失败: {e}")

    except Exception as e:
        print(f"\n[ERROR] 查询失败: {e}")
        import traceback
        traceback.print_exc()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已停止")
        sys.exit(0)
