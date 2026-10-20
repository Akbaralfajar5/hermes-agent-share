# $HASH Contract Reference (hash256.org)

## Addresses (Ethereum Mainnet)

- **Mining contract**: `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc`
- **Token contract**: `0x000000000004444c5dc75cB358380D2e3dE08A90`
- Old/wrong address (no bytecode): `0x000000000000B8c862` — DO NOT USE

## Event Topics

- **Mined event**: `0x94b5f8ac81f2e6e11c2d087499a0122e51fdfb3a8e07760065141257418cbe26`
  - Indexed: `miner` (address)
  - Data: `nonce`, `hash`, `reward`
- **Transfer event**: `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`
- **Approval event**: `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925`

## ABI (minimal for mining)

```json
[
  {"type":"function","stateMutability":"view","name":"getChallenge","inputs":[{"name":"miner","type":"address"}],"outputs":[{"type":"bytes32"}]},
  {"type":"function","stateMutability":"view","name":"currentDifficulty","inputs":[],"outputs":[{"type":"uint256"}]},
  {"type":"function","stateMutability":"view","name":"miningState","inputs":[],
   "outputs":[
    {"name":"era","type":"uint256"},{"name":"reward","type":"uint256"},
    {"name":"difficulty","type":"uint256"},{"name":"minted","type":"uint256"},
    {"name":"remaining","type":"uint256"},{"name":"epoch","type":"uint256"},
    {"name":"epochBlocksLeft","type":"uint256"}
  ]},
  {"type":"function","stateMutability":"nonpayable","name":"mine","inputs":[{"name":"nonce","type":"uint256"}],"outputs":[]}
]
```

## Mining Parameters (Era 1, May 2026)

- Reward: 100 HASH per mint
- Difficulty: `0x3ffffffffffffffffffffffffffffffffffffffffffffffffffff` (210 bits)
- Expected nonces per mint: ~70 trillion (`2^46`)
- Epoch: ~100 blocks (~20 minutes), challenge rotates per epoch per wallet
- Max mints per block: 10
- Total supply: ~18.9M HASH
- Total minted as of May 11 2026: ~1.57M HASH

## Wallets Used (the user) — 4-wallet setup as of May 11 2026

- W1 (GPU0): `0xFA8d81089006aeAD923378e744B7769d7935952C` — original wallet
- W2 (GPU1): `0x94226b7D8A288F03542F12EFB958d2c98882Fc62`
- W3 (GPU2): `0x2F124f676e09DC548a3Eb78eb79DD12ceb2Bd5d1`
- W4 (GPU3): `0x42Fa1c9C105bF7C558A167A6139c1B96232f6085`
- VPS 3 (deleted by user): `0x9847d0D202D1F6F95ffbbDdb553ee84cCec81e11`

## Miner Setup (VPS 4 — active)

- SSH: `ssh -p 26529 root@202.214.223.66`
- Binary: `/root/hash-miner/hash-miner-v4` (CUDA, fixed keccak endianness)
- Script: `/root/hash-miner/miner-gpu-v3.js`
- Startup: `/root/hash-miner/start-4wallet.sh` (4 wallet x 1 GPU)
- Screens: `hash-w1`, `hash-w2`, `hash-w3`, `hash-w4`
- Logs: `miner-w1.log` through `miner-w4.log`
- RPC: **Ankr Premium** `https://rpc.ankr.com/eth/923821b85ed523a84a04ab4af6dfe0ab4e46244b69418fefae48edf52b64e210` (switched May 11 2026 — Alchemy caused TIMEOUT with 4 wallets)

## Miner Setup (VPS 5 — new, setup in progress May 11 2026)

- SSH: `ssh -p 10339 root@ssh8.vast.ai`
- Status: SSH connection refused at time of session end — VPS still booting
- Plan: same setup as VPS 4 (clone start-4wallet.sh, same 4 wallets or new wallets)

## Debugging Session Notes (May 11 2026)

Root causes found and fixed:
1. Contract address was `0x0000...B8c862` (no bytecode) → fixed to `0xAC7b5d06...`
2. CUDA keccak256 output was little-endian per word, but comparison expected big-endian
   - Fix: change output loop from `(j*8)` to `((7-j)*8)` shift
   - Verified with test vector: `keccak256("")` = `c5d2460186f7...`
3. Difficulty display in log showed `0x000000000003ffff...` (padded) — misleading but correct value
4. W2 nonce reuse: after a reverted tx, GPU kept finding same nonce `0x00de0f0f...` — nonce offset not re-randomized between rounds

First successful mint after fix: block 25070726 (W1)
4-wallet setup confirmed working: W1 minted blocks 25070972 + 25071123, W2 minted block 25070344

## 4-Wallet Session Results (May 11 2026)

After switching from 4 GPU × 1 wallet → 1 GPU × 4 wallets:
- W1 (0xFA8d): 2 mints in ~1 hour (blocks 25070972, 25071123) ✅
- W2 (0x9422): 1 mint from earlier session (block 25070344), TIMEOUT issues in new session
- W3 (0x2F12): 0 mints — normal variance, GPU active
- W4 (0x42Fa): 0 mints — normal variance, GPU active

**RPC timeout observed**: All 4 wallets using same Alchemy key caused `TIMEOUT: refreshing challenge` loops on W2/W3/W4. W1 was unaffected (possibly timing difference). Miner recovered automatically after a few rounds.

**Variance note**: W1 getting 2 mints while W3/W4 get 0 over same period is within normal distribution for ~70T expected nonces per mint at 5.6 GH/s per GPU.

## Multi-VPS Same-Wallet Behavior (Confirmed)

User confirmed: running same wallet on multiple VPS is safe. Even if two VPS submit the same nonce simultaneously, both txs can land. Contract does not block duplicate submissions from same wallet. Use different nonce offsets per VPS to avoid redundant work.

## Competitor Analysis

- Top miner `0x2cced186...`: ~4 mints per 15 blocks, implied ~50+ GH/s
- `0x3e697046...`: 5 mints in 15 blocks — likely multi-VPS same wallet
- Network: ~3-5 mints per block globally, ~15-20 unique miners active
- A 3060 Ti minted within 5 minutes of starting — pure luck, not hashrate
