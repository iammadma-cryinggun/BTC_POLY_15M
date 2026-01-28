"""
私钥配置脚本 - 从 Zeabur 或直接输入获取私钥
"""

import os
import sys
from pathlib import Path

def setup_private_key():
    """配置私钥"""

    print("=" * 80)
    print("Polymarket 做市策略 - 私钥配置")
    print("=" * 80)

    print("\n选择私钥来源：")
    print("1. 直接输入私钥")
    print("2. 从 Zeabur 环境变量获取（需要先手动查看）")
    print("3. 稍后手动配置 .env 文件")

    choice = input("\n请选择 (1/2/3): ").strip()

    private_key = None

    if choice == "1":
        # 直接输入
        print("\n请输入你的 Polymarket 私钥：")
        print("格式：0x 开头的 64 位十六进制字符串")
        private_key = input("私钥: ").strip()

        # 验证格式
        if not private_key.startswith("0x"):
            print("[ERROR] 私钥必须以 0x 开头")
            return False

        if len(private_key) != 66:
            print(f"[WARN] 私钥长度不是 66 位（当前：{len(private_key)}）")

    elif choice == "2":
        # 从 Zeabur 获取
        print("\n请从 Zeabur 控制台复制环境变量：")
        print("1. 访问 https://zeabur.com")
        print("2. 选择你的项目")
        print("3. 进入服务的环境变量设置")
        print("4. 复制 POLYMARKET_PRIVATE_KEY 或 POLYMARKET_PK 的值")
        print("\n然后粘贴到这里：")
        private_key = input("私钥: ").strip()

    else:
        print("\n请手动配置：")
        print("1. 打开文件：D:\\翻倍项目\\polymarket_v2\\.env")
        print("2. 添加一行：POLYMARKET_PK=你的私钥")
        print("3. 保存文件")
        return False

    if not private_key:
        print("[ERROR] 私钥为空")
        return False

    # 保存到 .env 文件
    env_file = Path("D:\\翻倍项目\\polymarket_v2\\.env")

    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(f"# Polymarket 配置\n")
            f.write(f"POLYMARKET_PK={private_key}\n")
            f.write(f"SIGNATURE_TYPE=0\n")

        print(f"\n[OK] 私钥已保存到: {env_file}")
        print(f"[OK] 私钥: {private_key[:10]}...{private_key[-6:]}")

        # 同时设置环境变量（当前会话）
        os.environ["POLYMARKET_PK"] = private_key

        print("\n" + "=" * 80)
        print("配置完成！现在可以运行：")
        print("  python run_market_making_simple.py")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n[ERROR] 保存失败: {e}")
        return False


if __name__ == "__main__":
    try:
        success = setup_private_key()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
