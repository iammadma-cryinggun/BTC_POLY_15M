"""
查询两个地址的余额和交易记录
"""

import requests
import json
from datetime import datetime

POLYGONSCAN_API_KEY = "YourApiKeyToken"  # 免费API key，或留空

# 两个地址
PRIVATE_KEY_ADDRESS = "0x852cE059A9A96b3dA3eCe019FC527fAF9Ace8D8e"
POLYMARKET_DEPOSIT_ADDRESS = "0x18DdcbD977e5b7Ff751A3BAd6F274b67A311CD2d"

# USDC.e 合约地址 (Polygon)
USDC_E_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Native USDC 合约地址 (Polygon)
USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c335"


def get_balance(address):
    """Get USDC and USDC.e balance for address"""
    print(f"\n{'='*80}")
    print(f"Checking address: {address}")
    print(f"{'='*80}")

    balances = {}

    # USDC.e
    url = f"https://api.polygonscan.com/api"
    params = {
        "module": "account",
        "action": "tokenbalance",
        "contractaddress": USDC_E_CONTRACT,
        "address": address,
        "tag": "latest",
        "apikey": POLYGONSCAN_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "1":
            balance_wei = int(data.get("result", 0))
            balance_usdc = balance_wei / 1e6  # USDC has 6 decimals
            balances["USDC.e"] = balance_usdc
            print(f"[OK] USDC.e balance: {balance_usdc:.6f} USDC")
        else:
            print(f"[X] USDC.e query failed: {data.get('message', 'Unknown error')}")
            balances["USDC.e"] = 0

    except Exception as e:
        print(f"[X] USDC.e query error: {e}")
        balances["USDC.e"] = 0

    # Native USDC
    params["contractaddress"] = USDC_NATIVE
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "1":
            balance_wei = int(data.get("result", 0))
            balance_usdc = balance_wei / 1e6
            balances["USDC"] = balance_usdc
            print(f"[OK] USDC balance: {balance_usdc:.6f} USDC")
        else:
            print(f"[X] USDC query failed: {data.get('message', 'Unknown error')}")
            balances["USDC"] = 0

    except Exception as e:
        print(f"[X] USDC query error: {e}")
        balances["USDC"] = 0

    # MATIC balance (for gas)
    params = {
        "module": "account",
        "action": "balance",
        "address": address,
        "tag": "latest",
        "apikey": POLYGONSCAN_API_KEY
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "1":
            balance_wei = int(data.get("result", 0))
            balance_matic = balance_wei / 1e18
            balances["MATIC"] = balance_matic
            print(f"[OK] MATIC balance: {balance_matic:.4f} MATIC (for gas)")
        else:
            print(f"[X] MATIC query failed")
            balances["MATIC"] = 0

    except Exception as e:
        print(f"[X] MATIC query error: {e}")
        balances["MATIC"] = 0

    return balances


def get_recent_transactions(address):
    """Get recent transactions"""
    print(f"\n--- Recent transactions (USDC.e) ---")

    url = "https://api.polygonscan.com/api"
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": USDC_E_CONTRACT,
        "address": address,
        "page": 1,
        "offset": 5,
        "sort": "desc",
        "apikey": POLYGONSCAN_API_KEY
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "1" and data.get("result"):
            txs = data["result"]
            if len(txs) == 0:
                print("No USDC.e transactions found")
                return

            for i, tx in enumerate(txs[:5], 1):
                tx_type = "RECEIVED" if tx["to"].lower() == address.lower() else "SENT"
                value = int(tx["value"]) / 1e6
                time_str = datetime.fromtimestamp(int(tx["timeStamp"])).strftime('%Y-%m-%d %H:%M:%S')

                print(f"\n[{i}] {tx_type}")
                print(f"    Time: {time_str}")
                print(f"    Amount: {value:.6f} USDC.e")
                print(f"    From: {tx['from']}")
                print(f"    To: {tx['to']}")
                print(f"    Hash: {tx['hash']}")
        else:
            print("No transactions found")

    except Exception as e:
        print(f"Transaction query failed: {e}")


def main():
    print("="*80)
    print("Polymarket Address Balance Check")
    print("="*80)

    print("\n[Address 1] Private key address (bot uses this)")
    print(f"  {PRIVATE_KEY_ADDRESS}")
    balances1 = get_balance(PRIVATE_KEY_ADDRESS)
    get_recent_transactions(PRIVATE_KEY_ADDRESS)

    print("\n" + "="*80)
    print("\n[Address 2] Polymarket deposit address (you deposited here)")
    print(f"  {POLYMARKET_DEPOSIT_ADDRESS}")
    balances2 = get_balance(POLYMARKET_DEPOSIT_ADDRESS)
    get_recent_transactions(POLYMARKET_DEPOSIT_ADDRESS)

    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)

    if balances2.get("USDC.e", 0) > 0 or balances2.get("USDC", 0) > 0:
        print(f"\n[?] Your funds are on the deposit address:")
        print(f"   Address 2: {POLYMARKET_DEPOSIT_ADDRESS}")
        print(f"   USDC.e: {balances2.get('USDC.e', 0):.6f}")
        print(f"   USDC: {balances2.get('USDC', 0):.6f}")
        print(f"\n[!] Need to transfer funds from Address 2 to Address 1")

    elif balances1.get("USDC.e", 0) > 0 or balances1.get("USDC", 0) > 0:
        print(f"\n[OK] Funds are on the private key address! Bot should work")
        print(f"   Address 1: {PRIVATE_KEY_ADDRESS}")
        print(f"   USDC.e: {balances1.get('USDC.e', 0):.6f}")
        print(f"   USDC: {balances1.get('USDC', 0):.6f}")

    else:
        print(f"\n[X] No funds detected on either address")
        print(f"\nPossible reasons:")
        print(f"1. Transaction still confirming (takes a few minutes)")
        print(f"2. Deposited to wrong address")
        print(f"3. Using different token (not USDC or USDC.e)")
        print(f"\nSuggestions:")
        print(f"1. Check deposit address on PolygonScan:")
        print(f"   https://polygonscan.com/address/{POLYMARKET_DEPOSIT_ADDRESS}")
        print(f"2. Check 'Token Transfers' tab")
        print(f"3. Look for recent USDC transfers")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
