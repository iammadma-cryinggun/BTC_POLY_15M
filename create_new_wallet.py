#!/usr/bin/env python3
"""
Create a brand new Polymarket wallet address and API credentials
This will generate a new private key and wallet address
"""
from eth_account import Account
import secrets

# Generate strong random private key
priv = secrets.token_bytes(32)
private_key = "0x" + priv.hex()

# Create account from private key
account = Account.from_key(private_key)

print("=" * 80)
print("NEW WALLET GENERATED")
print("=" * 80)
print(f"\nPrivate Key (POLYMARKET_PK):")
print(f"{private_key}\n")
print(f"Wallet Address: {account.address}\n")
print(f"Proxy Address (deposit USDC.e here): {account.address}\n")
print("=" * 80)
print("\nIMPORTANT:")
print("1. Copy the private key above to Zeabur's POLYMARKET_PK environment variable")
print("2. Deposit USDC.e to this new address")
print("3. Redeploy Zeabur service")
print("=" * 80)
