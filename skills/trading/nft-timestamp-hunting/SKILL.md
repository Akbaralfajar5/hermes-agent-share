---
name: NFT Timestamp Hunting
description: Hunt and mint NFTs using timestamp-based oracle mechanics (e.g., Claude Punks / unixpunks.xyz)
version: 1
tags: [nft, ethereum, hunting, minting, timestamp, oracle]
triggers:
  - timestamp hunting
  - cpunks
  - claude punks
  - unixpunks
  - mint code hunting
  - nft oracle
---

# NFT Timestamp Hunting

Hunt NFTs that use timestamp-based oracle mechanics where you guess a unix timestamp, get a mintCode if valid, then mint on-chain.

## Mechanism

1. **Batch system**: NFTs released in batches, each with a timestamp range (e.g., 1498206000-1498215999)
2. **Valid timestamps**: Only ~11% of timestamps in range are valid (1111 out of 10000)
3. **Oracle API**: POST timestamp + wallet → get mintCode if valid
4. **Race condition**: First to mint on-chain with mintCode wins

## Workflow

### 1. Check Schedule
```bash
curl -s https://unixpunks.xyz/api/schedule | jq '.activeBatch, .windows[]'
```

### 2. Hunt for MintCode
```bash
curl -s -X POST https://unixpunks.xyz/api/find-mint-code \
  -H 'content-type: application/json' \
  -d '{"timestamp": 1498206500, "wallet": "0xYOUR_WALLET"}'
```

Responses:
- `{"ok":true,"mintCode":"0x..."}` → HIT! Use this to mint
- `{"ok":false,"error":"invalid_timestamp"}` → Miss, try another
- `{"ok":false,"error":"rate_limit","retryInMs":9700}` → Wait or use proxy

### 3. Mint On-Chain
```javascript
const tx = await contract.mint(mintCode, {
  value: ethers.parseEther('0.001111'),
  gasLimit: 200000
});
```

## Rate Limiting Strategy

**Problem**: API rate limits ~10 seconds per IP

**Solutions**:
1. **Respect rate limit**: Slow but reliable, ~10s per attempt
2. **Rotating proxy**: Bypass rate limit, faster hunting
3. **Hybrid**: Hunt direct (fast), switch to proxy on rate limit

User preference: Hunt WITHOUT proxy (lower latency), mint WITH proxy if RPC rate limited.

## Key Pitfalls

1. **WRONG ENDPOINT**: The `/api/oracle?ts=X` GET endpoint returns `NOT_FOUND`. Always use `/api/find-mint-code` POST endpoint!
2. **Race condition**: MintCode can be claimed by others before your TX confirms
2. **TX revert**: If mintCode already claimed, TX reverts with wasted gas
3. **RPC timeout**: Free RPC tiers may timeout on receipt polling (drpc.org times out, use 1rpc.io/eth or eth.llamarpc.com)
4. **Batch timing**: Batches have fixed windows, miss it = wait for next
5. **TX submitted but null receipt**: TX may still be pending - check etherscan manually
6. **Continuous hunting**: When batch sells out mid-hunt, auto-advance to next batch

## Proxy Strategy (User Preference)

- **Hunt API**: Direct connection preferred (lower latency ~50-100ms vs ~200-500ms with proxy)
- **Mint RPC**: Use proxy only if RPC rate limits (most free RPCs don't rate limit mints)
- **When rate limited on hunt**: Either wait 10s or switch to rotating proxy
- **DataImpulse proxy**: `http://user:pass@gw.dataimpulse.com:823` (rotating residential)

## Contract Info (Claude Punks)

- **Contract**: `0x9E464d954E07abeD84081F399feE729FF99f8f93`
- **Network**: Ethereum Mainnet
- **Mint price**: 0.001111 ETH
- **Website**: https://unixpunks.xyz

## Continuous Hunter Script

See `templates/hunt-continuous.js` for a full auto-hunter that:
- Waits for batch to open
- Hunts timestamps randomly
- Respects rate limits
- Mints via proxy when hit found
- Loops through batches until success

## References

- `references/api-responses.md` - API response formats and error codes
