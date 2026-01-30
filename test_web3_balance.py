#!/usr/bin/env python3
"""
直接从 Polygon 区块链查询 USDC.e 余额

USDC.e (USD Coin) contract on Polygon:
Contract Address: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
Decimals: 6
"""
import os
from dotenv import load_dotenv
load_dotenv()

from eth_account import Account
from web3 import Web3

# Polygon RPC endpoint (public)
POLYGON_RPC = "https://polygon-rpc.com"

# USDC.e contract address on Polygon
USDC_E_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

# Minimal ERC20 ABI for balanceOf function
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    }
]

private_key = os.getenv("POLYMARKET_PK")
signer_address = Account.from_key(private_key).address
proxy_address = os.getenv("POLYMARKET_PROXY_ADDRESS")

print("=" * 80)
print("从 Polygon 区块链查询 USDC.e 余额")
print("=" * 80)
print(f"\nSigner: {signer_address}")
print(f"Proxy:  {proxy_address}")
print(f"\n连接到 Polygon RPC: {POLYGON_RPC}\n")

try:
    # Connect to Polygon
    w3 = Web3(Web3.HTTPProvider(POLYGON_RPC))
    print(f"[OK] 已连接到 Polygon (Chain ID: {w3.eth.chain_id})")

    # Get USDC.e contract
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC_E_CONTRACT), abi=ERC20_ABI)

    # Query token info
    symbol = usdc.functions.symbol().call()
    decimals = usdc.functions.decimals().call()
    print(f"[OK] Token: {symbol} (Decimals: {decimals})\n")

    # Query Signer balance
    print(f"[查询] Signer 地址余额...")
    signer_balance_raw = usdc.functions.balanceOf(Web3.to_checksum_address(signer_address)).call()
    signer_balance = signer_balance_raw / (10 ** decimals)
    print(f"  Signer 余额: {signer_balance:.6f} {symbol}\n")

    # Query Proxy balance
    print(f"[查询] Proxy 地址余额...")
    proxy_balance_raw = usdc.functions.balanceOf(Web3.to_checksum_address(proxy_address)).call()
    proxy_balance = proxy_balance_raw / (10 ** decimals)
    print(f"  Proxy 余额:  {proxy_balance:.6f} {symbol}\n")

    # Also check MATIC balance (for gas)
    print(f"[查询] MATIC 余额（用于 gas 费）...")
    signer_matic = w3.eth.get_balance(Web3.to_checksum_address(signer_address))
    proxy_matic = w3.eth.get_balance(Web3.to_checksum_address(proxy_address))
    print(f"  Signer MATIC: {signer_matic / 1e18:.4f} MATIC")
    print(f"  Proxy MATIC:  {proxy_matic / 1e18:.4f} MATIC\n")

    print("=" * 80)
    print("结论:")
    if proxy_balance > 0:
        print(f"  Proxy 地址有 {proxy_balance:.6f} {symbol}")
        print("  解决方案：修改 NautilusTrader 适配器，使用 Web3 直接查询余额")
        print("  或者：将资金从 Proxy 转到 Signer 地址")
    else:
        print("  Proxy 地址余额为 0")
    print("=" * 80)

except Exception as e:
    print(f"[错误] {e}")
    import traceback
    traceback.print_exc()
