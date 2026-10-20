#!/usr/bin/env python3
"""
Ethereum Wallet Generator for Mining/Farming

Generates a new Ethereum wallet (address + private key) for use in mining/farming operations.

Requirements:
    pip install eth-account web3

Usage:
    python3 generate-wallet.py

Output:
    - Prints address and private key to stdout
    - Saves to .wallet file (chmod 600)
    - Updates .env file with address
"""

from eth_account import Account
import secrets
import os

def generate_wallet():
    """Generate new Ethereum wallet"""
    # Generate random 32-byte private key
    private_key = "0x" + secrets.token_hex(32)
    
    # Derive address from private key
    account = Account.from_key(private_key)
    
    return {
        "address": account.address,
        "private_key": private_key
    }

def save_wallet(wallet, wallet_file=".wallet", env_file=".env"):
    """
    Save wallet to files
    
    Args:
        wallet: dict with 'address' and 'private_key'
        wallet_file: path to save full credentials (chmod 600)
        env_file: path to .env file to update with address
    """
    # Save full credentials to .wallet (secure)
    with open(wallet_file, 'w') as f:
        f.write(f"# Ethereum Wallet\n")
        f.write(f"ADDRESS={wallet['address']}\n")
        f.write(f"PRIVATE_KEY={wallet['private_key']}\n")
    
    # Set restrictive permissions (owner read/write only)
    os.chmod(wallet_file, 0o600)
    
    # Update .env with address only
    if os.path.exists(env_file):
        # Read existing .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update ETH_ADDRESS line
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('ETH_ADDRESS='):
                lines[i] = f"ETH_ADDRESS={wallet['address']}\n"
                updated = True
                break
        
        # Append if not found
        if not updated:
            lines.append(f"ETH_ADDRESS={wallet['address']}\n")
        
        # Write back
        with open(env_file, 'w') as f:
            f.writelines(lines)
    else:
        # Create new .env
        with open(env_file, 'w') as f:
            f.write(f"ETH_ADDRESS={wallet['address']}\n")

def print_wallet(wallet):
    """Print wallet info to stdout"""
    print("=" * 60)
    print("🔐 NEW ETHEREUM WALLET GENERATED")
    print("=" * 60)
    print(f"Address: {wallet['address']}")
    print(f"Private Key: {wallet['private_key']}")
    print("=" * 60)
    print("")
    print("⚠️  IMPORTANT:")
    print("1. Save private key securely (backup offline)")
    print("2. Fund address with ETH for gas fees")
    print("3. Never share private key with anyone")
    print("")

if __name__ == "__main__":
    # Generate wallet
    wallet = generate_wallet()
    
    # Print to stdout
    print_wallet(wallet)
    
    # Save to files
    save_wallet(wallet)
    
    print("✅ Wallet saved to: .wallet (chmod 600)")
    print("✅ Address updated in: .env")
    print("")
