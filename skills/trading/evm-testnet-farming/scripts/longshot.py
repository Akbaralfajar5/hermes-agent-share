#!/usr/bin/env python3
"""
RPOW2 Long Shot Auto-Spinner
- Odds: 1:1 only
- Stake: 0.97 RPOW (970000000 base units) — just under 1 RPOW
- Stops if balance drops below MIN_BALANCE
- Handles 429 rate limit with 10s retry
Usage: update COOKIE, then run in screen:
  screen -dmS longshot bash -c 'cd ~/rpow2-miner && python3 -u longshot.py >> longshot.log 2>&1'
"""

import requests
import time
import random
import sys
import os
from datetime import datetime

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buffering=1)

# === CONFIG ===
COOKIE = "rpow_session=PASTE_COOKIE_HERE"
API_BASE = "https://api.rpow2.com"
STAKE_BASE_UNITS = 970000000       # 0.97 RPOW (just under 1)
ODDS_CHOICE = "1:1"
MIN_BALANCE = 10_000_000_000       # Stop if balance < 10 RPOW
DELAY_MIN = 1.5
DELAY_MAX = 3.0

HEADERS = {
    "Cookie": COOKIE,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
    "Origin": "https://longshot.rpow2.com",
    "Referer": "https://longshot.rpow2.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}


def get_balance():
    try:
        r = requests.get(f"{API_BASE}/me", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            return int(r.json().get("balance_base_units", 0))
    except Exception as e:
        print(f"[-] Balance error: {e}")
    return None


def spin():
    try:
        payload = {"stake_base_units": str(STAKE_BASE_UNITS), "odds_choice": ODDS_CHOICE}
        r = requests.post(f"{API_BASE}/api/longshot/spin", headers=HEADERS, json=payload, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"[-] Spin failed {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"[-] Spin error: {e}")
        return None


def fmt(base_units):
    return f"{int(base_units) / 1e9:.4f} RPOW"


def main():
    print("=" * 55)
    print("  RPOW2 Long Shot Auto-Spinner")
    print(f"  Odds: {ODDS_CHOICE} | Stake: {fmt(STAKE_BASE_UNITS)}")
    print(f"  Stop if balance < {fmt(MIN_BALANCE)}")
    print("=" * 55)

    balance = get_balance()
    if balance is None:
        print("[!] Cannot fetch balance. Check cookie.")
        sys.exit(1)
    print(f"[*] Starting balance: {fmt(balance)}\n")

    spin_num = 0
    wins = 0
    losses = 0
    net_change = 0

    while True:
        if balance < MIN_BALANCE:
            print(f"\n[!] Balance {fmt(balance)} below minimum {fmt(MIN_BALANCE)}. Stopping.")
            break

        spin_num += 1
        ts = datetime.now().strftime("%H:%M:%S")

        result = spin()
        if result is None:
            print(f"[{ts}] #{spin_num} Spin error, retrying in 10s...")
            time.sleep(10)
            continue

        outcome = result.get("outcome", "?")
        net = int(result.get("net_user_change_base_units", 0))
        balance_after = int(result.get("new_balance_base_units", balance + net))

        balance = balance_after
        net_change += net

        if outcome == "WIN":
            wins += 1
            icon = "✅ WIN "
        else:
            losses += 1
            icon = "❌ LOSE"

        total_spins = wins + losses
        win_rate = (wins / total_spins * 100) if total_spins > 0 else 0

        print(
            f"[{ts}] #{spin_num} {icon} | "
            f"Net: {'+' if net >= 0 else ''}{fmt(net)} | "
            f"Bal: {fmt(balance)} | "
            f"W/L: {wins}/{losses} ({win_rate:.1f}%) | "
            f"Total P&L: {'+' if net_change >= 0 else ''}{fmt(net_change)}"
        )

        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[*] Stopped.")
        sys.exit(0)
