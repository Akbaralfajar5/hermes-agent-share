#!/usr/bin/env python3
"""
Bulk WL submission via Supabase REST API.
Usage: Edit SUPABASE_URL, SUPABASE_KEY, TABLE_NAME, and PAYLOAD_TEMPLATE below.
       Provide accounts as JSON list and wallets as JSON list of {address, private_key}.
"""
import json
import subprocess
import time
import sys

# === CONFIGURATION (edit per project) ===
SUPABASE_URL = "https://PROJECT.supabase.co"
SUPABASE_KEY = "eyJ..."  # anon key from JS bundle
TABLE_NAME = "ferryman_wl"  # table name from .from('...').insert(...)
BATCH_SIZE = 50

def make_payload(username: str, wallet_address: str) -> dict:
    """Edit this to match the project's insert schema."""
    return {
        "x_username": username.replace("@", ""),
        "wallet_address": wallet_address.lower(),
        "followed": True,
        "liked_rt": True,
        "commented": True
    }

# === EXECUTION ===
def submit_batch(payloads: list) -> tuple:
    """Submit a batch of payloads. Returns (success_count, error_msg)."""
    cmd = [
        "curl", "-s", "-w", "\n%{http_code}",
        "-X", "POST",
        f"{SUPABASE_URL}/rest/v1/{TABLE_NAME}",
        "-H", f"apikey: {SUPABASE_KEY}",
        "-H", f"Authorization: Bearer {SUPABASE_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payloads)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout.strip()
    lines = output.split("\n")
    status_code = lines[-1] if lines else "000"
    body = "\n".join(lines[:-1])
    
    if status_code == "201":
        return len(payloads), None
    else:
        return 0, f"HTTP {status_code}: {body[:200]}"

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 supabase_wl_submit.py <accounts.json> <wallets.json>")
        print("  accounts.json: [\"username1\", \"username2\", ...]")
        print("  wallets.json: [{\"address\": \"0x...\", \"private_key\": \"0x...\"}, ...]")
        sys.exit(1)
    
    with open(sys.argv[1]) as f:
        accounts = json.load(f)
    with open(sys.argv[2]) as f:
        wallets = json.load(f)
    
    assert len(accounts) == len(wallets), "Account and wallet counts must match"
    
    total_success = 0
    total_failed = 0
    
    for i in range(0, len(accounts), BATCH_SIZE):
        batch_accounts = accounts[i:i+BATCH_SIZE]
        batch_wallets = wallets[i:i+BATCH_SIZE]
        
        payloads = [
            make_payload(acc, wal['address'])
            for acc, wal in zip(batch_accounts, batch_wallets)
        ]
        
        success, error = submit_batch(payloads)
        if error:
            print(f"✗ Batch {i//BATCH_SIZE + 1} FAILED: {error}")
            total_failed += len(payloads)
        else:
            total_success += success
            print(f"✓ Batch {i//BATCH_SIZE + 1}: {success} submitted (total: {total_success})")
        
        time.sleep(0.5)  # gentle rate limiting
    
    print(f"\n{'='*50}")
    print(f"TOTAL SUCCESS: {total_success}/{len(accounts)}")
    print(f"TOTAL FAILED: {total_failed}")

if __name__ == "__main__":
    main()
