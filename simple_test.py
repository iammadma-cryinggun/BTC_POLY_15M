#!/usr/bin/env python3
"""
超简单的 Zeabur 测试程序
用来确认 Zeabur 是否在使用最新代码
"""

print("=" * 80)
print("ZEBAUR TEST - If you see this, Zeabur is running this file!")
print("=" * 80)
print("")
print("[1] Python version:")
import sys
print(f"    {sys.version}")
print("")
print("[2] Working directory:")
import os
print(f"    {os.getcwd()}")
print("")
print("[3] Files in current directory:")
for item in os.listdir('.'):
    print(f"    - {item}")
print("")
print("[4] Checking if patches directory exists:")
if os.path.exists('patches'):
    print("    YES - patches directory found!")
    print("    Files in patches:")
    for item in os.listdir('patches'):
        print(f"      - {item}")
else:
    print("    NO - patches directory NOT found!")
print("")
print("[5] Checking if .env exists:")
if os.path.exists('.env'):
    print("    YES - .env found!")
    with open('.env', 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]
        print(f"    Content ({len(lines)} non-comment lines):")
        for line in lines[:5]:  # 只显示前5行
            # 隐藏私钥的大部分内容
            if 'POLYMARKET_PK=' in line:
                print(f"      {line[:20]}...{line[-10:]}")
            else:
                print(f"      {line[:60]}")
else:
    print("    NO - .env NOT found (using Zeabur env vars)")
print("")
print("[6] Checking environment variables:")
env_vars = ['POLYMARKET_PK', 'POLYMARKET_PROXY_ADDRESS', 'POLYMARKET_API_KEY']
for var in env_vars:
    value = os.getenv(var)
    if value:
        if 'PK' in var:
            print(f"    {var} = {value[:20]}...{value[-10:]}")
        else:
            print(f"    {var} = {value}")
    else:
        print(f"    {var} = (not set)")
print("")
print("[7] Testing py_clob_client import:")
try:
    from py_clob_client import client
    print("    SUCCESS - py_clob_client imported")
    print(f"    ClobClient available: {hasattr(client, 'ClobClient')}")
except Exception as e:
    print(f"    FAILED - {e}")
print("")
print("[8] Testing patches import:")
try:
    import sys
    sys.path.insert(0, os.getcwd())
    import patches
    print("    SUCCESS - patches module imported")
except Exception as e:
    print(f"    FAILED - {e}")
print("")
print("=" * 80)
print("TEST COMPLETED")
print("=" * 80)
