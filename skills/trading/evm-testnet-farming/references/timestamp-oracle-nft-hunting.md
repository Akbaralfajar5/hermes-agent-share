# Timestamp Oracle NFT Hunting

Pattern for NFT projects that use timestamp-based minting mechanics (e.g., Claude Punks / unixpunks.xyz).

## Mechanism

1. **Batches** open at scheduled times with a range of unix timestamps (e.g., 1498196000-1498205999)
2. Within each batch, only ~11% of timestamps are "valid" (1111 out of 10000)
3. Hunter guesses timestamps via API, gets `mintCode` if valid
4. First to submit `mintCode` on-chain wins the NFT

## API Pattern

```javascript
// Check schedule
const schedule = await fetch('https://unixpunks.xyz/api/schedule').then(r => r.json());
// Returns: { activeBatch: 3, windows: [{ batch, tsRangeStart, tsRangeEnd, consumedCount, timestampsCount }] }

// Hunt for mintCode
const result = await fetch('https://unixpunks.xyz/api/find-mint-code', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ timestamp: 1498196500, wallet: '0x...' })
}).then(r => r.json());
// Success: { ok: true, mintCode: '0x3e0de07c8ee4e65620db1f525ee6d27e7c7ef4ced57da4b6e667d7d207e9d4de' }
// Miss: { ok: false, error: 'invalid_timestamp' }
// Rate limited: { ok: false, error: 'rate_limit', retryInMs: 9500 }
```

## Rate Limit Strategies

### Option 1: Respect rate limit (user preferred)
- Lower latency per request (~50-100ms)
- But forced to wait 10s between requests when rate limited
- Better for low-competition batches

```javascript
if (result.error === 'rate_limit') {
  await sleep(result.retryInMs || 10000);
  continue;
}
```

### Option 2: Rotating proxy (bypass rate limit)
- Higher latency per request (~200-500ms due to proxy hop)
- But can spam requests without waiting
- Better for high-competition batches

```javascript
const { HttpsProxyAgent } = require('https-proxy-agent');
const proxyAgent = new HttpsProxyAgent('http://user:pass@gw.dataimpulse.com:823');

const result = await fetch(url, { agent: proxyAgent });
```

**User preference signal:** "Itu kalo pake proxy lebih lambat kan?" → User understands tradeoff, prefers direct connection for lower latency.

## Hunting Script Pattern

```javascript
const { ethers } = require('ethers');

const WALLET = '0x...';
const CONTRACT = '0x9E464d954E07abeD84081F399feE729FF99f8f93';
const RPC = 'https://eth.drpc.org';

async function hunt(start, end) {
  const tried = new Set();
  
  for (let i = 0; i < 500; i++) {
    const ts = start + Math.floor(Math.random() * (end - start + 1));
    if (tried.has(ts)) { i--; continue; }
    tried.add(ts);
    
    const result = await findMintCode(ts);
    
    if (result.ok && result.mintCode) {
      console.log(`🎯 HIT! ts=${ts}`);
      return result.mintCode;
    }
    
    if (result.error === 'rate_limit') {
      await sleep(result.retryInMs || 10000);
      tried.delete(ts);
      i--;
      continue;
    }
    
    await sleep(100);
  }
  return null;
}

async function mint(mintCode) {
  const provider = new ethers.JsonRpcProvider(RPC);
  const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
  const contract = new ethers.Contract(CONTRACT, [
    'function mint(bytes32 mintCode) external payable'
  ], wallet);
  
  const tx = await contract.mint(mintCode, {
    value: ethers.parseEther('0.001111'),
    gasLimit: 150000
  });
  await tx.wait();
}
```

## Key Discoveries

1. **Contract discovery**: Check website footer for Etherscan link, or grep HTML for `0x[a-fA-F0-9]{40}`
2. **Batch timing**: API returns `startIso`/`endIso` - wait for `activeBatch` to match target
3. **Random vs sequential**: Random guessing is better - sequential from start gets all the already-claimed timestamps
4. **11.1% hit rate**: With 1111 valid out of 10000, expect ~9 guesses per hit on average (without rate limit)

## Pitfalls

1. **Rate limit is per-IP, not per-wallet** - Proxy rotation helps, but adds latency
2. **MintCode is wallet-bound** - Can't share mintCodes between wallets
3. **First on-chain wins** - Even with valid mintCode, someone else might submit first
4. **Batch sells out fast** - Popular batches can go from 0% to 100% in 30 minutes
5. **API returns HTML on overload** - Handle `Unexpected token '<'` errors gracefully

## Background Process Management

```bash
# Run hunter in background with logging
node hunt.js 2>&1 | tee hunt.log &

# Or use Hermes background process
terminal(background=true, command="node hunt.js", notify_on_complete=true)

# Monitor progress
tail -f hunt.log
```

## Project-Specific: Claude Punks (unixpunks.xyz)

- **Network**: Ethereum Mainnet
- **Contract**: `0x9E464d954E07abeD84081F399feE729FF99f8f93`
- **Mint price**: 0.001111 ETH
- **Total supply**: 9,999 NFTs
- **Batches**: 9 batches, 1111 NFTs each, 30-minute windows
- **Skill file**: Available at `unixpunks.xyz/skill.md` for Claude Code CLI users
