"""
检查 Polymarket 钱包余额

用于诊断为什么策略显示余额为 0
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def load_private_key():
    """加载私钥"""
    private_key = os.getenv("POLYMARKET_PK")
    if not private_key:
        env_file = project_root / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('POLYMARKET_PK='):
                        private_key = line.split('=', 1)[1].strip()
                        break
    return private_key


def check_balance_with_clob_client(private_key: str):
    """使用 ClobClient 检查余额"""
    try:
        from py_clob_client.client import ClobClient

        POLYMARKET_API_URL = "https://clob.polymarket.com"
        POLYMARKET_CHAIN_ID = 137  # Polygon

        print(f"[1] 创建 ClobClient...")
        client = ClobClient(
            POLYMARKET_API_URL,
            key=str(private_key),
            signature_type=2,  # Magic Wallet
            chain_id=POLYMARKET_CHAIN_ID,
        )

        print(f"[2] 获取 API 凭证...")
        api_creds = client.create_or_derive_api_creds()
        print(f"    API Key: {api_creds.api_key[:10]}...")

        print(f"\n[3] 查询余额...")
        # 获取余额
        response = client.get_balance()
        print(f"\n=== 原始余额响应 ===")
        print(response)

        return response

    except Exception as e:
        print(f"\n[ERROR] 查询失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("Polymarket 钱包余额检查")
    print("=" * 80)

    # 1. 加载私钥
    print("\n[INFO] 加载私钥...")
    private_key = load_private_key()
    if not private_key:
        print("\n[ERROR] 未找到私钥")
        print("请在 .env 文件中配置: POLYMARKET_PK=0x...")
        return 1

    print(f"[OK] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

    # 2. 从私钥推导钱包地址
    try:
        from eth_account import Account
        account = Account.from_key(private_key)
        address = account.address
        print(f"\n[INFO] 钱包地址: {address}")
        print(f"[提示] 请确认这个地址是你充值的地址")
    except Exception as e:
        print(f"\n[ERROR] 无法推导钱包地址: {e}")

    # 3. 检查余额
    print(f"\n{'='*80}")
    balance = check_balance_with_clob_client(private_key)

    if balance:
        print(f"\n{'='*80}")
        print("\n[结论]")
        print("如果上面显示的余额是 0，可能的原因：")
        print("1. 你充值的是 native USDC，但 Polymarket 需要的是 USDC.e (bridged)")
        print("2. 资金还在另一个地址（不是从私钥推导的地址）")
        print("3. 需要在 Polymarket 网站上先进行一次交易来激活账户")
        print("\n建议：")
        print("- 访问 https://polymarket.com/")
        print("- 连接你的钱包")
        print("- 检查余额是否显示正确")
        print("- 如果余额正确，尝试在网站上做一次小额交易")
        print(f"{'='*80}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已停止")
        sys.exit(0)
