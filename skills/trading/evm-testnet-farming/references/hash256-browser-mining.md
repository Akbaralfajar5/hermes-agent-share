# HASH256 Browser Mining — hash256.org

## What It Is
- **$HASH** — ERC-20 on Ethereum mainnet, single immutable contract
- Contract = ERC20 + Uniswap V4 hook + PoW miner in one address
- Address: `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc`
- No team treasury, no premine, no admin key. Bitcoin-style halving schedule.

## Mining Mechanism
- Browser-based **keccak256 WASM workers** (not GPU, not ethash)
- Challenge = `keccak256(chainId ‖ contract ‖ miner_address ‖ epoch)`
- Valid nonce: `keccak256(challenge ‖ nonce) < currentDifficulty`
- N WASM workers run in parallel (auto-detected from CPU cores), each searching disjoint nonce-prefix ranges
- On hit → auto-submit `mine(nonce)` tx from connected wallet
- Epoch rotates every ~100 blocks (~20 min) → challenge hot-swaps automatically
- Max 10 mints per block (no burst exploitation)
- Difficulty retargets every 2,016 mints to hold 1 mint/minute globally

## Tokenomics
- Total supply: 21,000,000 HASH
- Genesis (5%): 1,050,000 HASH @ 0.01 ETH per 1,000 HASH
- LP side (5%): 1,050,000 HASH locked in Uniswap V4
- Mining (90%): 18,900,000 HASH via PoW halvings
- Era 1: 100 HASH/mint (100,000 mints = 10M HASH)
- Era 2: 50 HASH/mint, Era 3: 25, Era 4: 12.5, Era 5+: 6.25
- Cap: 21,000,000. Full distribution ~290 days at 1 mint/min target.

## Status (May 2026)
- Era 1, reward 100 HASH/mint
- Difficulty: `0x00000000…ffffff` (early, relatively easy)
- ~269,300 HASH minted (1.42% of total)

## Hardware Recommendations
Mining is CPU-bound (keccak256 WASM), NOT GPU.

**Key metric: CPU clock speed per core + core count**

| Tier | CPU | Threads | Notes |
|------|-----|---------|-------|
| Best | AMD Threadripper PRO 7985WX | 32 | Zen 4, 5.1GHz boost, $0.74/hr on QuickPod |
| Budget | AMD Threadripper 3970X | 40 | Zen 2, more threads but lower clock, $0.20/hr |
| Minimum | Any 4-core 2.5GHz+ | 4 | Viable for single wallet |

**Browser choice matters:** Chrome/Brave (V8 WASM) > Firefox for WASM performance.

## VPS Headless Mining Setup Plan
Since mining requires browser + wallet connect, VPS setup needs:
1. **Generate fresh wallets** via `eth_account` or `ethers.Wallet.createRandom()` — NEVER random hex
2. **Install headless Chromium + Playwright** on VPS
3. **Automate wallet connect** — inject private key via MetaMask extension or use a custom signing approach
4. **Keep WASM workers running** — disable background tab throttling via Chrome flags:
   ```
   --disable-background-timer-throttling
   --disable-renderer-backgrounding
   --disable-backgrounding-occluded-windows
   ```
5. **Auto-submit tx** — Playwright intercepts the `mine(nonce)` call, signs with wallet PK
6. **Loop 24/7** with watchdog (screen + Hermes cronjob pattern)

## Multi-Wallet Strategy
- Each wallet has its own address-bound challenge → solutions can't be shared
- Multi-wallet = multiple headless browser instances, each with own wallet
- Each instance needs ETH mainnet for gas (each `mine(nonce)` tx costs gas)
- Budget: ~0.001–0.003 ETH gas per mint depending on network congestion

## Pitfalls
1. **Browser throttling** — headless Chrome may throttle WASM workers. Use flags above.
2. **Gas cost** — every successful mint = 1 Ethereum mainnet tx. At high gas prices, mining may not be profitable. Monitor gas before scaling.
3. **Epoch expiry** — if miner finds nonce after epoch rotates, tx reverts. The browser miner handles this automatically, but custom scripts must handle epoch rotation.
4. **10 mints/block cap** — if many miners submit simultaneously, some txs revert. Not a loss (no gas charged on revert? verify), but reduces effective throughput.
5. **MetaMask in headless** — MetaMask extension in headless Chrome is complex. Alternative: use a custom ethers.js signer that intercepts the contract call and signs directly, bypassing MetaMask entirely.
6. **QuickPod reliability** — Threadripper 3970X pod (78.77% reliable) vs PRO 7985WX (96.74%). For 24/7 mining, prefer higher reliability score.
