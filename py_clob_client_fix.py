"""
修复 py_clob_client 库，使其支持使用 funder 地址查询余额

问题描述：
- py_clob_client 的 create_level_2_headers 函数始终使用 signer.address()
- 导致查询余额时使用的是 Signer 地址而不是 Proxy/Deposit 地址
- 即使传递了 funder 参数，余额查询仍然返回 0

解决方案：
修改 create_level_2_headers 函数，添加可选的 address 参数
"""

import os
import shutil

def patch_py_clob_client():
    """修补 py_clob_client 以支持 funder 地址"""

    # py_clob_client 安装目录
    client_dir = r"C:\Users\Martin\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages\py_clob_client"
    headers_file = os.path.join(client_dir, "headers", "headers.py")
    client_file = os.path.join(client_dir, "client.py")

    # 备份原文件
    headers_backup = headers_file + ".backup"
    client_backup = client_file + ".backup"

    if not os.path.exists(headers_backup):
        shutil.copy2(headers_file, headers_backup)
        print(f"[OK] 已备份原文件: {headers_backup}")

    if not os.path.exists(client_backup):
        shutil.copy2(client_file, client_backup)
        print(f"[OK] 已备份原文件: {client_backup}")

    # ========== 修复 1: 修改 create_level_2_headers 函数 ==========
    headers_content = '''
from ..clob_types import ApiCreds, RequestArgs
from ..signing.hmac import build_hmac_signature
from ..signer import Signer
from ..signing.eip712 import sign_clob_auth_message

from datetime import datetime

POLY_ADDRESS = "POLY_ADDRESS"
POLY_SIGNATURE = "POLY_SIGNATURE"
POLY_TIMESTAMP = "POLY_TIMESTAMP"
POLY_NONCE = "POLY_NONCE"
POLY_API_KEY = "POLY_API_KEY"
POLY_PASSPHRASE = "POLY_PASSPHRASE"


def create_level_1_headers(signer: Signer, nonce: int = None):
    """
    Creates Level 1 Poly headers for a request
    """
    timestamp = int(datetime.now().timestamp())

    n = 0
    if nonce is not None:
        n = nonce

    signature = sign_clob_auth_message(signer, timestamp, n)
    headers = {
        POLY_ADDRESS: signer.address(),
        POLY_SIGNATURE: signature,
        POLY_TIMESTAMP: str(timestamp),
        POLY_NONCE: str(n),
    }

    return headers


def create_level_2_headers(
    signer: Signer,
    creds: ApiCreds,
    request_args: RequestArgs,
    address: str = None,  # ← 新增参数：允许覆盖地址
):
    """
    Creates Level 2 Poly headers for a request using pre-serialized body if provided

    Parameters
    ----------
    signer : Signer
        The signer for authentication
    creds : ApiCreds
        The API credentials
    request_args : RequestArgs
        The request arguments
    address : str, optional
        The address to use in POLY_ADDRESS header.
        If None, uses signer.address() (default behavior).
        For proxy wallets, this should be the funder address.
    """
    timestamp = int(datetime.now().timestamp())

    # Prefer the pre-serialized body string for deterministic signing if available
    body_for_sig = (
        request_args.serialized_body
        if request_args.serialized_body is not None
        else request_args.body
    )

    hmac_sig = build_hmac_signature(
        creds.api_secret,
        timestamp,
        request_args.method,
        request_args.request_path,
        body_for_sig,
    )

    # 修复：优先使用传入的 address 参数（funder），否则使用 signer.address()
    address_to_use = address if address is not None else signer.address()

    return {
        POLY_ADDRESS: address_to_use,  # ← 修复：使用 funder 地址
        POLY_SIGNATURE: hmac_sig,
        POLY_TIMESTAMP: str(timestamp),
        POLY_API_KEY: creds.api_key,
        POLY_PASSPHRASE: creds.api_passphrase,
    }


def enrich_l2_headers_with_builder_headers(
    headers: dict, builder_headers: dict
) -> dict:
    return {**headers, **builder_headers}
'''

    # 写入修复后的 headers.py
    with open(headers_file, 'w', encoding='utf-8') as f:
        f.write(headers_content)

    print(f"[OK] 已修复: {headers_file}")
    print("     - create_level_2_headers 现在接受可选的 address 参数")

    # ========== 修复 2: 修改 ClobClient.get_balance_allowance 方法 ==========
    # 先读取原文件
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换 get_balance_allowance 方法
    old_method = '''    def get_balance_allowance(self, params: BalanceAllowanceParams = None):
        """
        Fetches the balance & allowance for a user
        Requires Level 2 authentication
        """
        self.assert_level_2_auth()
        request_args = RequestArgs(method="GET", request_path=GET_BALANCE_ALLOWANCE)
        headers = create_level_2_headers(self.signer, self.creds, request_args)'''

    new_method = '''    def get_balance_allowance(self, params: BalanceAllowanceParams = None):
        """
        Fetches the balance & allowance for a user
        Requires Level 2 authentication
        """
        self.assert_level_2_auth()
        request_args = RequestArgs(method="GET", request_path=GET_BALANCE_ALLOWANCE)
        # 修复：如果设置了 funder（proxy 地址），使用它来查询余额
        funder_address = self.builder.funder if hasattr(self, 'builder') and self.builder else None
        headers = create_level_2_headers(self.signer, self.creds, request_args, address=funder_address)'''

    if old_method in content:
        content = content.replace(old_method, new_method)

        # 写回文件
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[OK] 已修复: {client_file}")
        print("     - get_balance_allowance 现在使用 funder 地址（如果已设置）")
    else:
        print(f"[WARN] 未找到目标代码，可能已经修改过或版本不同")

    print("\n" + "=" * 80)
    print("修复完成！")
    print("=" * 80)
    print("\n说明：")
    print("1. 修改了 create_level_2_headers 函数，添加了可选的 address 参数")
    print("2. 修改了 get_balance_allowance 方法，使用 funder 地址查询余额")
    print("3. 原文件已备份到 *.backup")
    print("\n现在重新运行机器人，余额应该能正确显示了！")
    print("=" * 80)


if __name__ == "__main__":
    print("=" * 80)
    print("py_clob_client 余额查询修复工具")
    print("=" * 80)

    response = input("\n是否继续修复？这会修改 py_clob_client 库文件。(y/n): ")

    if response.lower() == 'y':
        try:
            patch_py_clob_client()
        except Exception as e:
            print(f"\n[ERROR] 修复失败: {e}")
            import traceback
            traceback.print_exc()
            print("\n请手动恢复备份文件")
    else:
        print("\n已取消")
