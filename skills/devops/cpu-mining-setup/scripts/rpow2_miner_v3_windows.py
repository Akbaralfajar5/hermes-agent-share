#!/usr/bin/env python3
"""
RPOW2 Multi-process CPU Miner v3 - Windows Compatible
Fixed multiprocessing issues and added better debugging.
"""

import hashlib
import struct
import time
import requests
import sys
import os
import multiprocessing as mp
from multiprocessing import Process, Value, Queue
from datetime import datetime, timezone
import random

# Force unbuffered output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

# === CONFIGURATION ===
COOKIE = "rpow_session=YOUR_SESSION_COOKIE_HERE"
API_BASE = "https://api.rpow2.com"

# Full browser headers to bypass detection
HEADERS = {
    "Cookie": COOKIE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://rpow2.com",
    "Referer": "https://rpow2.com/",
    "sec-ch-ua": '"Google Chrome";v="135", "Chromium";v="135", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site"
}

NUM_WORKERS = mp.cpu_count()


def count_trailing_zeros(hash_bytes):
    """Count trailing zero bits in hash (from the END/LSB)"""
    count = 0
    for byte in reversed(hash_bytes):
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count


def mine_worker(prefix_hex, difficulty_bits, start_nonce, step, found_flag, result_queue, worker_id):
    """Worker process that mines a range of nonces"""
    prefix = bytes.fromhex(prefix_hex)
    nonce = start_nonce
    checked = 0
    
    while found_flag.value == 0:
        data = prefix + struct.pack('<Q', nonce)
        h = hashlib.sha256(data).digest()
        
        trailing_zeros = count_trailing_zeros(h)
        
        if trailing_zeros >= difficulty_bits:
            found_flag.value = 1
            result_queue.put(('found', nonce, trailing_zeros))
            return
        
        nonce += step
        checked += 1
        
        # Report progress every 100k hashes
        if checked % 100000 == 0:
            result_queue.put(('progress', worker_id, checked))


def mine_challenge_parallel(nonce_prefix_hex, difficulty_bits, challenge_id, expires_at):
    """Mine using multiple processes with expiry awareness"""
    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    time_left = (expires_dt - datetime.now(timezone.utc)).total_seconds()

    print(f"[*] Mining challenge: {challenge_id}")
    print(f"[*] Difficulty: {difficulty_bits} bits | Time left: {time_left:.0f}s")
    print(f"[*] Prefix: {nonce_prefix_hex}")
    print(f"[*] Workers: {NUM_WORKERS}")
    print(f"[*] Starting mining...")

    if time_left < 10:
        print("[-] Challenge almost expired, skipping...")
        return None

    found_flag = Value('i', 0)
    result_queue = Queue()

    start_time = time.time()

    # Start workers
    workers = []
    for i in range(NUM_WORKERS):
        p = Process(target=mine_worker, args=(
            nonce_prefix_hex, difficulty_bits, i, NUM_WORKERS,
            found_flag, result_queue, i
        ))
        p.start()
        workers.append(p)

    # Monitor progress and check expiry
    solution_nonce = None
    total_hashes = 0
    
    while found_flag.value == 0:
        # Check queue for messages
        while not result_queue.empty():
            msg = result_queue.get()
            if msg[0] == 'progress':
                worker_id, checked = msg[1], msg[2]
                total_hashes += checked
        
        time.sleep(1)
        elapsed = time.time() - start_time
        remaining = (expires_dt - datetime.now(timezone.utc)).total_seconds()
        hashrate = total_hashes / elapsed if elapsed > 0 else 0

        if remaining < 5:
            print(f"\n[!] Challenge expiring in {remaining:.0f}s, aborting...")
            found_flag.value = -1
            for p in workers:
                p.terminate()
            for p in workers:
                p.join(timeout=2)
            return None

        print(f"  [{elapsed:.0f}s] Mining... {hashrate/1000:.1f}K H/s | Remaining: {remaining:.0f}s", end='\r')

    # Get solution from queue
    while not result_queue.empty():
        msg = result_queue.get()
        if msg[0] == 'found':
            solution_nonce = msg[1]
            trailing_zeros = msg[2]
            break

    # Wait for workers to finish
    for p in workers:
        p.join(timeout=5)
        if p.is_alive():
            p.terminate()

    if solution_nonce is not None:
        elapsed = time.time() - start_time
        print(f"\n[+] FOUND! Nonce: {solution_nonce} ({trailing_zeros} trailing zeros)")
        print(f"[+] Time: {elapsed:.1f}s | Hashrate: {total_hashes/elapsed/1000:.1f}K H/s")
        return str(solution_nonce)

    return None


def get_challenge():
    """Request a new mining challenge"""
    try:
        # Add small random delay to mimic human behavior
        time.sleep(random.uniform(0.5, 1.5))
        
        resp = requests.post(f"{API_BASE}/challenge", headers=HEADERS, json={}, timeout=60)
        if resp.status_code != 200:
            print(f"[-] Challenge request failed: {resp.status_code} {resp.text}")
            return None
        return resp.json()
    except Exception as e:
        print(f"[-] Challenge request error: {e}")
        return None


def submit_solution(challenge_id, solution_nonce):
    """Submit mining solution"""
    data = {
        "challenge_id": challenge_id,
        "solution_nonce": solution_nonce
    }
    try:
        # Add small random delay
        time.sleep(random.uniform(0.3, 0.8))
        
        resp = requests.post(f"{API_BASE}/mint", headers=HEADERS, json=data, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            print(f"[+] MINTED! {result}")
            return result
        else:
            print(f"[-] Mint failed: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        print(f"[-] Mint submit error: {e}")
        return None


def get_balance():
    """Check current balance"""
    try:
        resp = requests.get(f"{API_BASE}/me", headers=HEADERS, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            # Convert base_units to readable format (divide by 1e9)
            balance = float(data.get('balance_base_units', 0)) / 1e9
            minted = float(data.get('minted_base_units', 0)) / 1e9
            daily_minted = float(data.get('daily_minted_base_units', 0)) / 1e9
            daily_remaining = float(data.get('daily_remaining_base_units', 0)) / 1e9
            
            return {
                'email': data.get('email'),
                'balance': balance,
                'minted': minted,
                'daily_minted': daily_minted,
                'daily_remaining': daily_remaining
            }
    except Exception as e:
        print(f"[-] Balance check error: {e}")
    return None


def main():
    print("=" * 60)
    print("  RPOW2 Multi-Core CPU Miner v3")
    print(f"  Workers: {NUM_WORKERS} cores")
    print("=" * 60)

    me = get_balance()
    if me:
        print(f"[*] Account: {me.get('email', 'unknown')}")
        print(f"[*] Balance: {me['balance']:.2f} RPOW")
        print(f"[*] Total Minted: {me['minted']:.2f} RPOW")
        print(f"[*] Daily: {me['daily_minted']:.2f} / {me['daily_minted'] + me['daily_remaining']:.2f} RPOW")
    else:
        print("[!] Could not fetch balance - continuing anyway...")

    round_num = 0
    minted_count = 0
    expired_count = 0

    while True:
        round_num += 1
        print(f"\n{'='*60}")
        print(f"  Round #{round_num} | {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Minted: {minted_count} | Expired: {expired_count}")
        print(f"{'='*60}")

        # Get challenge
        challenge = get_challenge()
        if not challenge:
            print("[-] Failed to get challenge, retrying in 60s...")
            time.sleep(60)
            continue

        # Mine it
        solution = mine_challenge_parallel(
            challenge['nonce_prefix'],
            challenge['difficulty_bits'],
            challenge['challenge_id'],
            challenge['expires_at']
        )

        if solution:
            # Submit immediately
            result = submit_solution(challenge['challenge_id'], solution)
            if result:
                minted_count += 1
            else:
                expired_count += 1
        else:
            expired_count += 1
            print("[!] Could not solve in time, getting new challenge...")

        # Show balance periodically
        if round_num % 5 == 0 or minted_count > 0:
            me = get_balance()
            if me:
                print(f"[*] Balance: {me['balance']:.2f} RPOW | Daily: {me['daily_minted']:.2f}")

        # Random delay between rounds (1-3 seconds) to mimic human
        time.sleep(random.uniform(1, 3))


if __name__ == "__main__":
    # Windows multiprocessing fix
    mp.freeze_support()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Miner stopped.")
        sys.exit(0)
