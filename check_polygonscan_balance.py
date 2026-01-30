"""
使用 PolygonScan API 直接查询 Proxy 地址余额
"""
import requests

# Proxy 地址
PROXY_ADDRESS = "0x18DdcbD977e5b7Ff751A3BAd6F274b67A311CD2d"

# USDC.e 合约地址 (Polygon)
USDC_E_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Native USDC 合约地址 (Polygon)
USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c335"

def get_balance(address, token_contract):
    """查询 token 余额"""
    url = "https://api.polygonscan.com/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": token_contract,
        "address": address,
        "tag": "latest",
        "apikey": "YourApiKeyToken"  # 免费API key
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "1":
            balance_wei = int(data.get("result", 0))
            balance_usdc = balance_wei / 1e6  # USDC has 6 decimals
            return balance_usdc
        else:
            print(f"查询失败: {data.get('message', 'Unknown error')}")
            return 0

    except Exception as e:
        print(f"查询错误: {e}")
        return 0


def main():
    print("=" * 80)
    print(f"查询 Proxy 地址余额")
    print(f"地址: {PROXY_ADDRESS}")
    print("=" * 80)

    # 查询 USDC.e
    print("\n[1] 查询 USDC.e 余额...")
    balance_e = get_balance(PROXY_ADDRESS, USDC_E_CONTRACT)
    print(f"    USDC.e: {balance_e:.6f} USDC")

    # 查询 Native USDC
    print("\n[2] 查询 Native USDC 余额...")
    balance_native = get_balance(PROXY_ADDRESS, USDC_NATIVE)
    print(f"    USDC: {balance_native:.6f} USDC")

    # 总结
    total = balance_e + balance_native
    print("\n" + "=" * 80)
    print(f"总余额: {total:.6f} USDC")
    print("=" * 80)

    if total > 0:
        print("\n[OK] Proxy 地址上有余额！")
        print("如果机器人显示余额为 0，说明：")
        print("1. NautilusTrader adapter 可能不支持 Proxy 地址")
        print("2. 或者需要使用特殊的 API 调用方式")
    else:
        print("\n[!] Proxy 地址上没有 USDC 余额")
        print("可能的原因：")
        print("1. 充值还未确认（需要等待几个区块确认）")
        print("2. 充值到了错误的地址")
        print("3. 使用了错误的 token（不是 USDC 或 USDC.e）")

    print("\n建议操作：")
    print("1. 访问 Polymarket 网站，确认你的钱包余额")
    print("2. 如果网站上显示有余额，但机器人显示 0")
    print("   → 这是 adapter 的问题，可能需要直接使用 py_clob_client")
    print("3. 如果网站上也是 0")
    print("   → 检查充值是否成功，或者重新充值")

    return 0


if __name__ == "__main__":
    import sys
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n已停止")
        sys.exit(0)
