# $HASH Mining Competition Analysis

## Quick Competition Check Script

Analyze who's mining, their hashrate estimates, and whether it's worth competing.

```javascript
// Run from /tmp with ethers installed
const {ethers} = require('./node_modules/ethers');
const p = new ethers.JsonRpcProvider('https://rpc.mevblocker.io', 1, {staticNetwork:true});

async function main() {
  const CONTRACT = '0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc';
  const latest = await p.getBlockNumber();
  const from = '0x' + (latest - 2000).toString(16);
  
  const logs = await p.getLogs({ address: CONTRACT, fromBlock: from, toBlock: 'latest' });
  
  // Count per miner
  const miners = {};
  for (const l of logs) {
    const raw = l.topics[1] || '';
    const miner = raw.length >= 42 ? '0x' + raw.slice(-40) : raw;
    miners[miner] = (miners[miner]||0) + 1;
  }
  const sorted = Object.entries(miners).sort((a,b) => b[1]-a[1]);
  
  console.log('Total mints (last 2000 blocks):', logs.length);
  console.log('Unique miners:', sorted.length);
  console.log('Avg mints/block:', (logs.length/2000).toFixed(2));
  console.log('\nTOP MINERS:');
  for (const [m, c] of sorted.slice(0, 10)) {
    const mintsPerHour = c / (2000*12/3600);
    console.log(m + ' | ' + c + ' mints | ' + mintsPerHour.toFixed(1) + '/hr');
  }
}
main().catch(console.error);
```

## Operator Analysis (who controls multiple wallets)

Check `from` address of mint txs to identify operators running multiple wallets:

```javascript
// Sample 30 unique miners, get their tx.from
const sampled = new Set();
const fromToMiners = {};
for (const l of logs) {
  const miner = '0x' + l.topics[1].slice(-40);
  if (sampled.has(miner)) continue;
  sampled.add(miner);
  if (sampled.size > 30) break;
  const tx = await p.getTransaction(l.transactionHash);
  if (tx) {
    const sender = tx.from.toLowerCase();
    if (!fromToMiners[sender]) fromToMiners[sender] = new Set();
    fromToMiners[sender].add(miner);
  }
}
// Operators with 2+ wallets are farms
```

## Known Top Miners (May 12 2026)

| Address | Mints (2000 blk) | Behavior | Notes |
|---------|-------------------|----------|-------|
| `0x000000000004444c...` | 801 | Accumulating (691K HASH held) | Vanity address, 2 wallets, operator `0x79c5a7...` |
| `0xac7b5d06fa1e77...` | 761 | Holding (contract address) | Dev/owner, operator `0x3e697046...` |
| `0x163f3103de041d...` | 523 | Mining ~68/hr | Operator `0x95963e...`, 2 wallets |
| `0x3e697046fb45...` | 225 | Dev team | Same operator as contract |
| `0x66a9893cc07d...` | 167 | Active miner | Single wallet |

## Gas Patterns of Top Miners

- Top miners use **0.3-0.6 gwei** gas — far below our 10 gwei setting
- They use private mempools (Flashbots/MEV Blocker) for submission
- Gas is NOT the differentiator — hashrate + latency is

## Whale/Accumulation Check

Check if external buyers (non-miners) are accumulating:

```javascript
// Get Transfer events, track net flows per address
const transferTopic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
const logs = await p.getLogs({
  address: CONTRACT,
  topics: [transferTopic],
  fromBlock: from, toBlock: 'latest'
});
// Track balances[to] += value, balances[from] -= value
// Positive = accumulator, Negative = seller
```

## Liquidity Check (Uniswap V3)

```javascript
const factoryV3 = '0x1F98431c8aD98523631AE4a59f267346ea31F984';
const WETH = '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2';
// Try fee tiers: 500, 3000, 10000
const getPool = ethers.id('getPool(address,address,uint24)').slice(0,10);
// Encode params and call factory
// Then check balanceOf(pool) for both tokens
```

**May 12 2026 result:**
- V3 Pool (1% fee): `0xe9f419a0f4425523aeb9b78756a9caa7b83c052d`
- Liquidity: 626 HASH + 0.0045 WETH = **~$23 total** (dead)
- Price: ~$0.018/HASH
- No V2 pair exists

## Decision Framework

**Mine if ALL true:**
1. `HASH price × 100 (reward) > VPS cost per mint` (profitable)
2. Liquidity > $5,000 (can actually sell)
3. Difficulty allows reasonable mint frequency (< 2 hours at your hashrate)

**Stop mining if ANY true:**
1. Liquidity < $1,000 (can't sell)
2. Price < breakeven for your VPS cost
3. Difficulty requires > 4 hours per mint at your hashrate
4. Top miners have 100x+ your hashrate (can't compete)
