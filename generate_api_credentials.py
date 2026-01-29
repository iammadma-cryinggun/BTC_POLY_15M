"""
生成 Polymarket API Credentials

使用方法：
    python generate_api_credentials.py

注意：
    - 请确保你的邮箱钱包中有少量 MATIC（用于 Gas 费）
    - API Key 生成后会自动保存到环境变量
"""

import os
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("Polymarket API Credentials 生成工具")
    print("=" * 80)

    # 读取私钥
    print("\n[步骤 1] 获取私钥")
    print("-" * 80)

    private_key = None

    # 方法 1: 从环境变量读取
    private_key = os.getenv("POLYMARKET_PK")

    # 方法 2: 从 .env 文件读取
    if not private_key:
        project_root = Path(__file__).parent
        env_file = project_root / '.env'
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key.strip() == "POLYMARKET_PK":
                            private_key = value.strip()
                            break

    # 方法 3: 手动输入
    if not private_key:
        print("\n请输入你的 Polymarket 邮箱钱包私钥（0x 开头）:")
        print("提示: 登录 Polymarket → Settings → Magic Wallet → Reveal Private Key")
        private_key = input("\n私钥: ").strip()

    if not private_key:
        print("[错误] 未找到私钥，无法继续")
        return 1

    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    print(f"[OK] 私钥已加载: {private_key[:10]}...{private_key[-6:]}")

    # 生成 API Credentials
    print("\n[步骤 2] 生成 API Credentials")
    print("-" * 80)

    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.constants import POLYGON

        # 创建客户端（使用主网）
        print("[INFO] 正在连接到 Polymarket 主网...")
        client = ClobClient(
            host="https://clob.polymarket.com",
            chain_id=POLYGON,  # Polygon Mainnet (137)
            key=private_key,
            signature_type=2,  # 邮箱/Magic 钱包使用 type 2
        )

        print("[OK] 客户端创建成功")

        # 获取钱包地址
        address = client.get_address()
        print(f"[OK] 钱包地址: {address}")
        print(f"\n请确认：")
        print(f"  1. 这是你的 Polymarket 邮箱钱包地址")
        print(f"  2. 请充值到这个地址（Polygon 网络的 USDC）")

        # 生成 API Key
        print("\n[INFO] 正在生成 API Credentials...")

        api_creds = client.create_api_key()

        print("\n" + "=" * 80)
        print("API Credentials 生成成功！")
        print("=" * 80)
        print(f"\nAPI Key:     {api_creds.api_key}")
        print(f"API Secret:  {api_creds.api_secret}")
        print(f"Passphrase:  {api_creds.api_passphrase}")

        # 保存到 .env 文件
        print("\n[步骤 3] 保存到 .env 文件")
        print("-" * 80)

        env_file = Path(__file__).parent / '.env'

        # 备份旧的 .env 文件
        if env_file.exists():
            backup_file = Path(__file__).parent / '.env.backup'
            import shutil
            shutil.copy(env_file, backup_file)
            print(f"[INFO] 已备份旧配置到: {backup_file}")

        # 写入新的配置
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write("# Polymarket 配置\n")
            f.write("# 生成时间: " + str(__import__('datetime').datetime.now()) + "\n\n")
            f.write(f"POLYMARKET_PK={private_key}\n")
            f.write(f"POLYMARKET_API_KEY={api_creds.api_key}\n")
            f.write(f"POLYMARKET_API_SECRET={api_creds.api_secret}\n")
            f.write(f"POLYMARKET_PASSPHRASE={api_creds.api_passphrase}\n")

        print(f"[OK] 配置已保存到: {env_file}")

        # 输出 Zeabur 环境变量配置
        print("\n" + "=" * 80)
        print("Zeabur 环境变量配置")
        print("=" * 80)
        print("\n请在 Zeabur 项目中设置以下环境变量：\n")
        print(f"POLYMARKET_PK={private_key}")
        print(f"POLYMARKET_API_KEY={api_creds.api_key}")
        print(f"POLYMARKET_API_SECRET={api_creds.api_secret}")
        print(f"POLYMARKET_PASSPHRASE={api_creds.api_passphrase}")

        print("\n" + "=" * 80)
        print("完成！")
        print("=" * 80)
        print("\n接下来的步骤：")
        print(f"  1. 充值 USDC 到钱包地址: {address}")
        print("  2. 在 Zeabur 上更新上述环境变量")
        print("  3. 重新部署服务")
        print("  4. 观察日志，确认余额正确")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n[错误] 生成失败: {e}")
        print("\n可能的原因：")
        print("  1. 钱包中没有足够的 MATIC（用于 Gas 费）")
        print("  2. 私钥格式错误（确保是 0x 开头的 66 位十六进制字符串）")
        print("  3. 网络连接问题")
        print("  4. 邮箱钱包未在 Polymarket 上激活（需要先在网页上交易一次）")

        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
