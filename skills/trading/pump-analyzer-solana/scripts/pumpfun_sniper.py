#!/usr/bin/env python3
"""Pump.fun sniper scanner — real-time WebSocket, minimal filter, instant alert.
Usage: python3 pumpfun_sniper.py [duration_sec]
Default: 120 seconds

Requires: pip install websockets requests
"""
import asyncio
import json
import sys
import time
import requests
import websockets

DURATION = int(sys.argv[1]) if len(sys.argv) > 1 else 120

# Minimal spam filter
SKIP_PREFIXES = ('test', 'Test', 'TEST', ' ', '.')
SKIP_WORDS = ('test', 'test1', 'test2', 'testing', 'testcoin', 'scam', 'honeypot', 'rug')
MIN_NAME_LEN = 3

async def run():
    uri = "wss://pumpportal.fun/api/data"
    good = []
    total = 0
    start = time.time()
    
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({"method": "subscribeNewToken"}))
        
        while time.time() - start < DURATION:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=3)
                data = json.loads(msg)
                
                if data.get('txType') != 'create':
                    continue
                
                total += 1
                name = (data.get('name') or '').strip()
                symbol = (data.get('symbol') or '').strip()
                mint = data.get('mint', '')
                mcap = float(data.get('marketCapSol', 0))
                
                if not mint.endswith('pump'):
                    continue
                if not name or len(name) < MIN_NAME_LEN:
                    continue
                if any(name.startswith(p) for p in SKIP_PREFIXES):
                    continue
                if any(w in name.lower() for w in SKIP_WORDS):
                    continue
                if name == symbol:
                    continue
                if mcap < 3:
                    continue
                
                good.append({
                    'name': name, 'symbol': symbol, 'mint': mint,
                    'mcap': mcap, 'time': time.strftime('%H:%M:%S'),
                })
                
                ts = time.strftime('%H:%M:%S')
                print(f"🆕 [{ts}] {name} (${symbol}) | {mcap:.1f} SOL")
                print(f"   https://pump.fun/{mint}")
                print(f"   CA: {mint}")
                print()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                break
    
    print(f"\n{'='*50}")
    print(f"DURATION: {DURATION}s | Total new: {total} | Filtered: {len(good)}")
    
    if good:
        print(f"\n=== ALL FILTERED TOKENS ===")
        for i, t in enumerate(good):
            print(f"#{i+1} {t['time']} | {t['name']} (${t['symbol']}) | {t['mcap']:.1f} SOL")
            print(f"   {t['mint']}")
    
    print(f"\n=== RUGCHECK TOP 3 ===")
    for t in good[:3]:
        try:
            rc = requests.get(
                f"https://api.rugcheck.xyz/v1/tokens/{t['mint']}/report",
                timeout=4
            )
            d = rc.json()
            m = '✅' if d.get('mintAuthority') is None else '🚨'
            f = '✅' if d.get('freezeAuthority') is None else '🚨'
            top = d.get('topHolders', [])
            t1 = top[0].get('pct', 100) if top else 100
            s = d.get('score', 0)
            print(f"{t['name']} (${t['symbol']}) — Mint:{m} Freeze:{f} RC:{s} T1:{t1:.0f}%")
        except:
            print(f"{t['name']} (${t['symbol']}) — RC: timeout")

if __name__ == '__main__':
    asyncio.run(run())
