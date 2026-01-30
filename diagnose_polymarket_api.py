#!/usr/bin/env python3
"""
Polymarket API 诊断脚本
检查当前钱包的 API Key 状态
"""
import os
import sys
from pathlib import Path

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:15236'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:15236'

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from py_clob_client.client import ClobClient

def check_api_key_status(private_key: str):
    """检查 API Key 状态"""

    POLYMARKET_API_URL = "https://clob.polymarket.com"
    POLYMARKET_CHAIN_ID = 137

    print("=" * 80)
    print("Polymarket API 诊断")
    print("=" * 80)

    # 创建客户端
    print("\n[1/4] 创建 ClobClient...")
    client = ClobClient(
        POLYMARKET_API_URL,
        key=private_key,
        chain_id=POLYMARKET_CHAIN_ID,
    )
    print("[OK] 客户端创建成功")

    # 尝试获取/推导 API Key
    print("\n[2/4] 检查是否已有 API Key...")
    try:
        # derive_api_key 会返回已存在的 API Key（如果有）
        creds = client.derive_api_key()
        print(f"[INFO] 发现已存在的 API Key:")
        print(f"  - API Key: {creds.api_key[:10]}...{creds.api_key[-10:]}")
        print(f"  - Secret: {creds.api_secret[:10]}...{creds.api_secret[-10:]}")
        print(f"  - Passphrase: {creds.api_passphrase[:10]}...{creds.api_passphrase[-10:]}")

        # 尝试使用这个 Key 进行一个简单的 API 调用来验证是否有效
        print("\n[3/4] 验证 API Key 是否有效...")
        try:
            from py_clob_client.clob_types import ApiCreds

            # 创建 ApiCreds 对象
            api_creds = ApiCreds(
                api_key=creds.api_key,
                api_secret=creds.api_secret,
                api_passphrase=creds.api_passphrase,
            )

            # 创建新的客户端，带上 API 凭证
            client_with_creds = ClobClient(
                POLYMARKET_API_URL,
                key=private_key,
                chain_id=POLYMARKET_CHAIN_ID,
                creds=api_creds,  # 传入凭证
            )

            # 尝试一个更简单的 API 调用来验证 Key 是否有效
            print("[INFO] 尝试获取订单（需要 Level 2 认证）...")
            try:
                # 尝试获取当前订单
                orders = client_with_creds.get_orders([])
                print(f"[OK] API Key 有效！找到了 {len(orders)} 个订单")
                return api_creds
            except Exception as order_error:
                # 如果获取订单失败，尝试其他方法
                print(f"[INFO] get_orders 失败: {order_error}")

                # 尝试获取余额（使用默认参数）
                print("[INFO] 尝试查询余额...")
                try:
                    from py_clob_client.clob_types import BalanceAllowanceParams
                    # 不传参数，使用默认值
                    balance = client_with_creds.get_balance_allowance()
                    print(f"[OK] API Key 有效！余额信息:")
                    print(f"  {balance}")
                    return api_creds
                except Exception as balance_error:
                    balance_error_msg = str(balance_error)
                    if "401" in balance_error_msg or "Unauthorized" in balance_error_msg or "Invalid api key" in balance_error_msg:
                        raise balance_error
                    else:
                        # 如果不是 401 错误，说明 Key 是有效的，只是参数不对
                        print(f"[OK] API Key 有效！（余额查询参数问题: {balance_error_msg[:100]}）")
                        return api_creds

        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "Unauthorized" in error_msg or "Invalid api key" in error_msg:
                print(f"[ERROR] API Key 已失效！")
                print(f"  错误: {error_msg}")
                print("\n[解决方案]")
                print("  1. 登录 https://polymarket.com")
                print("  2. 进入 Settings -> API Keys")
                print("  3. 删除所有旧的 API Keys")
                print("  4. 重新运行此脚本创建新的 API Key")
                return None
            else:
                print(f"[ERROR] API Key 验证失败（其他错误）:")
                print(f"  {error_msg}")
                return None

    except Exception as e:
        error_msg = str(e)
        import traceback
        print(f"[INFO] 没有找到已存在的 API Key")
        print(f"  错误类型: {type(e).__name__}")
        print(f"  错误信息: {error_msg}")
        print(f"  详细堆栈:\n{traceback.format_exc()}")

        # 尝试创建新的 API Key
        print("\n[4/4] 尝试创建新的 API Key...")
        try:
            new_creds = client.create_api_key()
            print(f"[OK] 新 API Key 创建成功！")
            print(f"  - API Key: {new_creds.api_key}")
            print(f"  - Secret: {new_creds.api_secret}")
            print(f"  - Passphrase: {new_creds.api_passphrase}")

            print("\n[重要] 请立即保存这些凭证，它们无法恢复！")
            print("建议添加到 Zeabur 环境变量：")
            print(f"  POLYMARKET_API_KEY={new_creds.api_key}")
            print(f"  POLYMARKET_API_SECRET={new_creds.api_secret}")
            print(f"  POLYMARKET_PASSPHRASE={new_creds.api_passphrase}")

            return new_creds

        except Exception as create_error:
            create_error_msg = str(create_error)
            print(f"[ERROR] 创建新 API Key 失败:")
            print(f"  {create_error_msg}")

            if "Could not create api key" in create_error_msg:
                print("\n[可能的原因]")
                print("  1. 这个钱包已经达到了 API Key 数量限制")
                print("  2. 需要去网页端手动管理 API Keys")
                print("\n[建议操作]")
                print("  1. 登录 https://polymarket.com")
                print("  2. 进入 Settings -> API Keys")
                print("  3. 查看并管理现有的 API Keys")
                print("  4. 如有需要，删除旧的 Keys 后再创建新的")

            return None


if __name__ == "__main__":
    # 从环境变量或 .env 文件加载私钥
    private_key = os.getenv("POLYMARKET_PK")

    if not private_key:
        # 尝试从 .env 文件读取
        env_file = project_root / ".env"
        if env_file.exists():
            print("[INFO] 从 .env 文件读取私钥...")
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('POLYMARKET_PK='):
                        private_key = line.split('=', 1)[1].strip()
                        break

    if not private_key:
        print("[ERROR] 未找到 POLYMARKET_PK")
        print("请设置环境变量或在 .env 文件中配置私钥")
        sys.exit(1)

    print(f"[INFO] 私钥: {private_key[:10]}...{private_key[-6:]}")

    # 运行诊断
    result = check_api_key_status(private_key)

    print("\n" + "=" * 80)
    if result:
        print("[SUCCESS] API Key 可用")
    else:
        print("[FAILED] API Key 不可用，请按照上述提示操作")
    print("=" * 80)
