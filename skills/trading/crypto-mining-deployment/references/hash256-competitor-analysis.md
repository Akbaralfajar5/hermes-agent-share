# $HASH Competitor Analysis — May 2026

## Top Miner: 0x2cced186c0b172443884b0dae52695e847ee010d

Observed via Etherscan token page: `https://etherscan.io/token/0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc?a=0x2cced186c0b172443884b0dae52695e847ee010d`

### Key Observations

- **Total TX count:** 1,476 (very active miner)
- **32 mints in 1 block** (block 25330321 = 3200 HASH in one transfer)
- **Average block gap:** ~35 blocks (~7 minutes) between mint clusters
- **Pattern:** Accumulates multiple nonces, then submits batch

### Recent Transfer Data (via Alchemy `alchemy_getAssetTransfers`)

```
Block 0x17e8a91 | 3200.0 HASH  ← 32 mints in 1 block!
Block 0x17e8a34 | 1000.0 HASH  ← 10 mints
Block 0x17e8a15 |  200.0 HASH
Block 0x17e8a04 |  100.0 HASH
Block 0x17e89f3 |  300.0 HASH
Block 0x17e89e5 |  100.0 HASH
Block 0x17e89b5 |  100.0 HASH
Block 0x17e897c |  100.0 HASH
Block 0x17e8962 |  200.0 HASH
Block 0x17e8955 |  100.0 HASH
```

Block gaps: [93, 31, 17, 17, 14, 48, 57, 26, 13] blocks

### How to Query Competitor Activity

```bash
# Get recent HASH transfers for any wallet
curl -s "https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY" \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"alchemy_getAssetTransfers","params":[{"fromAddress":"WALLET","contractAddresses":["0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc"],"category":["erc20"],"maxCount":"0x10","order":"desc"}],"id":1}' \
  | python3 -c "
import json,sys
r=json.load(sys.stdin)
transfers = r.get('result',{}).get('transfers',[])
print('Recent transfers:', len(transfers))
for t in transfers[:10]:
    print(f'  Block {t[\"blockNum\"]} | {t[\"value\"]} HASH')
"
```

### Likely Strategy

**Option A — 32 wallet paralel:**
- 32 wallets mining simultaneously
- Each wallet 1 GPU (or CPU)
- All submit in same block → 32 slots filled
- HASH goes to 32 different wallets, then consolidated

**Option B — Smart contract batch:**
- Custom contract that calls `mine()` in a loop
- 1 TX = multiple mints
- More gas efficient per mint

**Option A is more likely** (simpler, no custom contract needed).

## Priority Fee Competition (Real On-Chain Data)

Queried blocks 25070060-25070075 for `mine()` TXs to contract `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc`:

### Distribution

| Priority Fee | Frequency | Notes |
|-------------|-----------|-------|
| 0.0-0.2 gwei | Very common | `0xdee4534273` spams this — still gets included |
| 0.5-3 gwei | Most common | Majority of miners |
| 5-10 gwei | Common | Mid-tier |
| 10-20 gwei | Occasional | Top-tier miners |
| 20-38 gwei | Rare | Overkill, wastes gas |

### Notable Wallets

- `0xdee4534273` — spams 0.2 gwei, gets included in almost every block (multi-wallet farming)
- `0xf7a53279ac` & `0xda528d1529` — consistent 3 gwei, appear in nearly every block
- `0x995d6e1513` — 15.1 gwei, appears frequently
- `0xa046e04915` — 38 gwei (highest observed), rare

### Recommendation

**Sweet spot: 3-5 gwei** — consistently gets included, much cheaper than 25 gwei.
- 3 gwei → ~$0.63/mint (vs $5.24 at 25 gwei)
- 8x cheaper per mint
- Still competitive since many slots available per block (10 max, but often 13-26 TXs compete)

### Query Script

```bash
# Check current competition in last 15 blocks
for block_num in $(seq LATEST-15 LATEST); do
  curl -s -X POST "https://eth-mainnet.g.alchemy.com/v2/KEY" \
    -H "Content-Type: application/json" \
    -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_getBlockByNumber\",\"params\":[\"$(printf '0x%x' $block_num)\",true],\"id\":1}" | \
    python3 -c "
import json,sys
data=json.load(sys.stdin)
block=data.get('result')
if not block: sys.exit()
CONTRACT='0xac7b5d06fa1e77d08aea40d46cb7c5923a87a0cc'
txs=[tx for tx in block['transactions'] if tx.get('to') and tx['to'].lower()==CONTRACT]
if txs:
    print(f'Block {int(block[\"number\"],16)}: {len(txs)} mine txs')
    for tx in txs:
        pf=int(tx.get('maxPriorityFeePerGas') or '0x0',16)/1e9
        gp=int(tx.get('gasPrice') or '0x0',16)/1e9
        print(f'  {tx[\"from\"][:12]} priority={pf:.1f}gwei total={gp:.1f}gwei')
" 2>/dev/null
done
```
