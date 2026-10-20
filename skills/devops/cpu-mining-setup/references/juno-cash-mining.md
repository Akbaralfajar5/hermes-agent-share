# Juno Cash (JUNO) CPU Mining Reference

## Overview
- **Algorithm:** RandomX (CPU-optimized, no ASIC)
- **Privacy:** Mandatory shielded transactions (Orchard technology, no transparent addresses)
- **Address format:** j1 addresses
- **Protocol:** Stratum (stratum+tcp), default port 3333

## Requirements
- **CPU:** x86-64 (Intel/AMD). More cores = more hashrate. AMD Ryzen (large L3 cache) best.
- **RAM:** 2GB free per mining thread
- **OS:** Linux, Windows, macOS
- **Network:** Stable internet

## Software
- `junocashd` — full node + built-in wallet
- `junorig` — pool mining software (like xmrig for Juno)
- **Releases:** https://github.com/juno-cash/junocash/releases
- **Web wallet:** https://thejunowallet.com/

## Pool Mining Setup (3 steps)

```bash
# 1. Download binaries
wget <junocashd-linux-url> && chmod +x junocashd
wget <junorig-linux-url> && chmod +x junorig

# 2. Run node, press E to get j1 address
./junocashd

# 3. Start pool mining
./junorig -o stratum+tcp://POOL:3333 -u YOUR_J1_ADDRESS -p x
```

## Available Pools
- junopool.com
- junohash.com
- juno.suprnova.cc
- juno-cash.minerlab.io

## Solo Mining (advanced, needs significant hashpower)
```bash
./junocashd -gen=1 -genproclimit=-1
# -genproclimit=-1 = all cores, or set specific number
```

## Troubleshooting
- **Low hashrate:** Ensure 2GB free RAM per thread, close other apps, check CPU AES support
- **Node not syncing:** Check internet, firewall ports, try adding peers manually

## Block Explorers
- junocash.dedoo.xyz
- junocash.xplorer.info

## Docs
- Mining guide: https://juno.cash/mining/
- Get started: https://juno.cash/get-started/
