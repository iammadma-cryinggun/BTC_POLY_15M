#!/usr/bin/env python3
"""
Zeabur 部署诊断脚本

一次性检查所有可能的问题，不要反复修改
运行: python diagnose_zeabur.py
"""

import os
import sys
from pathlib import Path

print("=" * 80)
print("Zeabur 部署完整诊断")
print("=" * 80)

# ========== 1. 检查文件结构 ==========
print("\n[1/7] 检查关键文件是否存在...")
critical_files = [
    "run_15m_market.py",
    "patches/__init__.py",
    "patches/py_clob_client_patch.py",
    "start.sh",
    "Dockerfile",
    "requirements.txt",
]

all_exist = True
for file in critical_files:
    path = Path(file)
    if path.exists():
        print(f"  [OK] {file}")
    else:
        print(f"  [FAIL] {file} - 文件不存在！")
        all_exist = False

if not all_exist:
    print("\n[FAIL] 关键文件缺失，无法继续")
    sys.exit(1)

# ========== 2. 检查 patches/__init__.py ==========
print("\n[2/7] 检查 patches/__init__.py 内容...")
with open("patches/__init__.py", "r", encoding="utf-8") as f:
    init_content = f.read()

if "from patches import py_clob_client_patch" in init_content:
    print("  [OK] __init__.py 正确导入了 py_clob_client_patch")
else:
    print("  [FAIL] __init__.py 没有导入 py_clob_client_patch")
    print(f"  内容: {init_content}")
    sys.exit(1)

# ========== 3. 检查 run_15m_market.py 的导入语句 ==========
print("\n[3/7] 检查 run_15m_market.py 的补丁导入...")
with open("run_15m_market.py", "r", encoding="utf-8") as f:
    main_content = f.read()

if "import patches" in main_content:
    print("  [OK] run_15m_market.py 正确导入了 patches")
elif "from patches import py_clob_client_patch" in main_content:
    print("  [FAIL] 使用了错误的导入方式: from patches import py_clob_client_patch")
    print("  应该使用: import patches")
    sys.exit(1)
else:
    print("  [FAIL] run_15m_market.py 没有导入 patches")
    sys.exit(1)

# ========== 4. 检查 force_regenerate 参数 ==========
print("\n[4/7] 检查 API 凭证生成配置...")
if "force_regenerate=True" in main_content:
    print("  [OK] 已设置 force_regenerate=True")
else:
    print("  [FAIL] 没有设置 force_regenerate=True")
    sys.exit(1)

# ========== 5. 检查补丁代码 ==========
print("\n[5/7] 检查补丁代码...")
with open("patches/py_clob_client_patch.py", "r", encoding="utf-8") as f:
    patch_content = f.read()

required_elements = [
    "def patch_py_clob_client():",
    "def create_level_2_headers_patched(",
    "address=None",
    "address_to_use = address if address is not None else signer.address()",
    "def get_balance_allowance_patched(",
    "funder_address = self.builder.funder",
    "patch_py_clob_client()",
]

all_present = True
for element in required_elements:
    if element in patch_content:
        print(f"  [OK] {element}")
    else:
        print(f"  [FAIL] 缺少: {element}")
        all_present = False

if not all_present:
    print("\n[FAIL] 补丁代码不完整")
    sys.exit(1)

# ========== 6. 测试补丁加载 ==========
print("\n[6/7] 测试补丁是否能正确加载...")
try:
    # 添加项目根目录到路径
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    # 导入补丁（这会自动执行修补）
    import patches  # noqa: F401

    print("  [OK] 补丁模块导入成功")

    # 验证补丁是否真的应用了
    from py_clob_client.headers import headers as headers_module
    from py_clob_client import client as client_module

    # 检查函数签名是否包含 address 参数
    import inspect
    sig = inspect.signature(headers_module.create_level_2_headers)
    if 'address' in sig.parameters:
        print("  [OK] create_level_2_headers 已被修补（包含 address 参数）")
    else:
        print("  [FAIL] create_level_2_headers 未被修补")
        sys.exit(1)

    # 检查 get_balance_allowance 是否被替换
    if hasattr(client_module.ClobClient.get_balance_allowance, '__name__'):
        method_name = client_module.ClobClient.get_balance_allowance.__name__
        if 'patched' in method_name.lower():
            print("  [OK] get_balance_allowance 已被修补")
        else:
            print("  [WARN] get_balance_allowance 可能未被修补")

except Exception as e:
    print(f"  [FAIL] 补丁加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ========== 7. 检查环境变量配置 ==========
print("\n[7/7] 检查环境变量配置示例...")
env_file = Path(".env")
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        env_content = f.read()

    if "POLYMARKET_PROXY_ADDRESS" in env_content:
        print("  [OK] .env 包含 POLYMARKET_PROXY_ADDRESS")
    else:
        print("  [WARN] .env 不包含 POLYMARKET_PROXY_ADDRESS（推荐配置）")
else:
    print("  [WARN] .env 文件不存在（Zeabur 上使用环境变量）")

# ========== 最终诊断结果 ==========
print("\n" + "=" * 80)
print("[SUCCESS] 所有检查通过！代码配置正确")
print("=" * 80)
print("\n下一步：在 Zeabur 上部署时，日志应该显示：")
print("  1. [PATCH] py_clob_client 已成功修补 - 余额查询现在使用 funder 地址")
print("  2. [INFO] 强制重新生成 API 凭证...")
print("  3. [OK] API 凭证已生成")
print("  4. [OK] Using Proxy/Deposit address: 0x18DdcbD977e5b7Ff751A3BAd6F274b67A311CD2d")
print("\n如果仍然出现 401 错误，可能的原因：")
print("  1. Zeabur 没有拉取最新代码（检查部署日志的 git commit）")
print("  2. Zeabur 环境变量中仍有旧的 API 凭证（删除它们）")
print("  3. 私钥不正确（检查 POLYMARKET_PK 环境变量）")
print("  4. Docker 镜像缓存问题（在 Zeabur 上重新构建镜像）")
print("=" * 80)
