# BSC Keccak-256 PoW Mining (SAT / SatMiner)

## Overview

SAT (Satoshi) is a BSC-based PoW token replicating Bitcoin's economics: 21M supply, halving, Keccak-256 mining. Contract: `0x14Dc4b4929c664534f1d4D64107d8F36CbF906a0` (BSC Mainnet, chain_id 56).

**Key difference from Ethereum PoW tokens:** BSC gas is much cheaper (~$0.01-0.05 per tx vs $5+ on Ethereum), making CPU mining more viable economically.

## SatMiner Architecture

**Repo:** https://github.com/SatCoinBSC/SatMiner

Two mining modes:
- **CPU mode** (`satoshi_miner.py`) — GUI app (tkinter), uses `CpuPool` with multiprocessing "warm pool" (zero cold-start on new challenges). Needs headless wrapper for VPS.
- **GPU mode** (`gpu_miner.py`) — CLI app, OpenCL-based, significantly faster at high difficulty. Works on NVIDIA via OpenCL, Apple Silicon via Metal.

**Core mining class:** `ReactiveMiner` in `satoshi_miner.py` — handles WS challenge detection, CPU/GPU solving, multi-relay broadcasting, gas management. GUI (`SatoshiMinerApp`) is just a wrapper with tkinter callbacks.

**Keccak-256 PoW formula:**
```
digest = keccak256(challengeNumber(32 bytes) ++ minerAddress(20 bytes) ++ nonce(32 bytes))
Valid when: digest <= miningTarget
```

## Setup on Headless VPS (CPU Mode)

### Step 1: Install deps
```bash
cd ~ && git clone https://github.com/SatCoinBSC/SatMiner.git
cd SatMiner
pip3 install -r requirements.txt
apt-get install -y python3-tk  # Required — satoshi_miner.py imports tkinter at module level
python3 setup.py build_ext --inplace  # Build keccak_pow C extension
```

### Step 2: Test relay connectivity
```bash
# bloXroute may be unreachable from some VPS — test each relay
curl -s -m 10 -X POST https://bsc.rpc.blxrbdn.com -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],\"id\":1}'
curl -s -m 10 -X POST https://rpc-bsc.48.club -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],\"id\":1}'
curl -s -m 10 -X POST https://bsc-dataseed1.binance.org/ -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],\"id\":1}'

# Test WebSocket
# wss://bsc-rpc.publicnode.com and wss://bsc.drpc.org are common options
```

### Step 3: Write config.yaml
```yaml
private_key: "0xYOUR_PRIVATE_KEY"
contract_address: "0x14Dc4b4929c664534f1d4D64107d8F36CbF906a0"
chain_id: 56

use_network_gas: true
network_gas_multiplier: 1.0
min_gas_price_gwei: 0.01
max_gas_price_gwei: 5
gas_price_gwei: 0.05
gas_limit: 200000

solver: cpu

relay_urls:  # Use only tested-working relays
  - "https://rpc-bsc.48.club"
  - "https://0.48.club"
  - "https://bsc-dataseed1.binance.org"
  - "https://bsc-dataseed2.binance.org"

ws_urls:
  - "wss://bsc-rpc.publicnode.com"
detect_mode: auto
head_ws: "wss://bsc-rpc.publicnode.com"

dry_run: false
verbose_logs: true
```

### Step 4: Create headless wrapper
Since `satoshi_miner.py` is tkinter GUI, write a `headless.py` that imports `ReactiveMiner` directly:

```python
#!/usr/bin/env python3
"""Headless wrapper for SAT Miner."""
import sys, os, time, signal, yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(os.path.dirname(__file__), "config.yaml")) as f:
    cfg = yaml.safe_load(f)

import satoshi_miner

def on_log(msg, lv="INFO"):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] [{lv}] {msg}", flush=True)

def on_win(epoch):
    on_log(f"BLOCK WON! epoch={epoch}", "WIN")

def on_lose():
    on_log("Lost - another miner got it first", "LOSE")

def on_stats(s):
    on_log(f"Stats: sent={s.get('sent',0)} won={s.get('won',0)} lost={s.get('lost',0)}", "STAT")

def get_balance(miner):
    try:
        from web3 import Web3
        bal = miner.w3.eth.get_balance(miner.me)
        return f"{Web3.from_wei(bal, 'ether')} BNB"
    except:
        return "unknown"

def main():
    on_log("=" * 55)
    on_log("  SAT PoW CPU Miner - Headless Mode")
    on_log("=" * 55)
    miner = satoshi_miner.ReactiveMiner(cfg, on_log=on_log, on_win=on_win,
                                         on_lose=on_lose, on_stats=on_stats)
    def shutdown(sig, frame):
        on_log("Shutting down...", "WARN")
        miner.stop()
        sys.exit(0)
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    miner.start()
    on_log(f"Wallet: {miner.me}")
    on_log(f"Solver: CPU ({miner.pool.n} processes)")
    on_log(f"Balance: {get_balance(miner)}")
    while miner.running:
        time.sleep(1)

if __name__ == "__main__":
    main()
```

### Step 5: Run in background
```bash
cd ~/SatMiner && nohup python3 headless.py > miner.log 2>&1 &
```

## Pitfalls

### tkinter import on headless VPS
`apt-get install -y python3-tk` is REQUIRED even for headless mode because `satoshi_miner.py` does `import tkinter as tk` at module level. Without it, import fails with `ImportError: libtk8.6.so: cannot open shared object file`.

### bloXroute relay unreachable
Default config uses `bsc.rpc.blxrbdn.com` which is blocked/unreachable from many VPS providers. Always test relay connectivity before starting. Fallback: Binance public RPCs (`bsc-dataseed1.binance.org`), 48 Club (`rpc-bsc.48.club`).

### Miner hangs at ReactiveMiner init
If the miner hangs during `Creating ReactiveMiner...`, it's likely the first relay URL in config is unreachable (Web3 HTTPProvider timeout). Fix: reorder relay_urls to put working ones first.

### Balance requirement
BSC gas is cheap but you still need BNB. ~$1.5-2 is enough for 100+ submissions. The miner checks balance at startup and exits if too low (needs ~3x single-tx gas cost minimum).

### CPU pool defaults to nproc/2
`CpuPool` auto-detects CPU count and uses half the cores by default. On a 32-core Threadripper, it spawns 16 processes. This is intentional to leave headroom for the main process and OS.

### Difficulty vs CPU hashrate
BSC Keccak-256 difficulty of ~25,000-30,000 means CPU mining is probabilistic — could be minutes or hours per block. GPU miners have massive advantage (100-1000x hashrate). CPU mining on BSC is viable mainly because gas is cheap and difficulty may be lower than Ethereum equivalents.

## Dashboard / Stats
- Live stats: https://satcoinbsc.github.io/SatoshiMiner/SatInfo/
- Shows: total mined, current difficulty, epoch, reward era
