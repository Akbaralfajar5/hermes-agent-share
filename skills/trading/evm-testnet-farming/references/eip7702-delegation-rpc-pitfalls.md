# EIP-7702 Delegation RPC Pitfalls

Session: 2026-05-10 — brainrot.dog $ROT minting via EIP-7702 + MCP

## Core Issue: Delegated EOAs Cannot Send Normal Transfers

**Critical discovery:** Once an EOA is delegated via EIP-7702 (`signAuthorization` + `authorizationList`), it **cannot send normal ETH transfers** until delegation is revoked.

### Symptom
```
TransactionExecutionError: Execution reverted with reason: gas required exceeds allowance (10500).
```

Even though:
- Gas estimation shows sufficient balance
- Transaction is a simple `{to: address, value: amount}`
- No contract interaction involved

### Root Cause
The delegated EOA's code is now the delegate contract's bytecode. When you try to send ETH, the EVM executes the delegate contract's logic instead of a simple transfer. If the delegate contract doesn't have a payable fallback or the logic doesn't support arbitrary transfers, the tx reverts.

### Solution: Revoke Delegation First
```javascript
// Sign authorization to 0x0 (revoke)
const authorization = await walletClient.signAuthorization({
  account,
  contractAddress: '0x0000000000000000000000000000000000000000'
});

// Send self-tx with revoke authorization
const hash = await walletClient.sendTransaction({
  account,
  authorizationList: [authorization],
  to: account.address,
  data: '0x',
  value: 0n,
  gas: 100000n
});

await publicClient.waitForTransactionReceipt({ hash });

// Now normal transfers work
```

### Verification
```javascript
const code = await publicClient.getCode({ address: account.address });
// Delegated: 0xef01001d370cfced3c7f9101f5dca5ee626447276d20be
// Revoked: 0x (empty)
```

## RPC Timeout on waitForTransactionReceipt

**Issue:** Free-tier public RPCs (publicnode.com, drpc.live) timeout when waiting for tx confirmation, even though the tx is successfully broadcast and confirmed on-chain.

### Symptom
```javascript
const receipt = await publicClient.waitForTransactionReceipt({ hash, timeout: 60000 });
// Throws timeout error after 60s, but tx is confirmed in block explorer
```

### Workaround 1: Manual Polling
```javascript
const hash = await walletClient.sendTransaction({...});
console.log('Tx sent:', hash);

// Manual wait instead of RPC call
await new Promise(resolve => setTimeout(resolve, 30000));

console.log('Should be confirmed. Check etherscan.');
```

### Workaround 2: Retry with Exponential Backoff
```javascript
for (let i = 0; i < 10; i++) {
  await new Promise(resolve => setTimeout(resolve, 6000));
  
  const result = await fetch(RPC_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'eth_getTransactionReceipt',
      params: [hash],
      id: 1
    })
  }).then(r => r.json());
  
  if (result.result?.status) {
    console.log('Confirmed in block', parseInt(result.result.blockNumber, 16));
    break;
  }
}
```

## Gas Estimation Failures on Self-Transactions

**Issue:** `eth_estimateGas` fails for EIP-7702 self-transactions (delegation or revocation) with "gas required exceeds allowance" even when balance is sufficient.

### Solution: Always Set Explicit Gas Limit
```javascript
const hash = await walletClient.sendTransaction({
  account,
  authorizationList: [authorization],
  to: account.address,
  data: '0x',
  value: 0n,
  gas: 100000n  // REQUIRED — estimation will fail
});
```

Typical gas usage:
- Delegation: ~46,000 gas
- Revocation: ~46,000 gas
- Set `gas: 100000n` to be safe

## npm run Doesn't Inherit Shell Environment

**Issue:** `npm run script` does NOT inherit `export VAR=value` from the shell.

### Symptom
```bash
export RPC_URL="https://..."
npm run farm
# Script sees: process.env.RPC_URL === undefined
```

### Solution 1: Inline Env Vars
```bash
RPC_URL="https://..." npm run farm
```

### Solution 2: Shell Wrapper (Preferred for Multiple Vars)
```bash
#!/bin/bash
# farm.sh
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
npm run farm
```

Then: `chmod +x farm.sh && ./farm.sh`

### Solution 3: dotenv in Script
```javascript
// At top of script
import 'dotenv/config';
// or
require('dotenv').config();
```

But this requires `npm install dotenv` — shell wrapper is cleaner for one-off scripts.

## Test-First Workflow (User Frustration Signal)

**User correction:** "proses dulu mint di wallet pertama, jangan send dulu ke yg lain"

### Problem
Agent distributed ETH to 50 wallets immediately, then discovered:
1. Delegation tx sent but not confirmed (RPC timeout)
2. MCP server not responding (timeout on mint calls)
3. Web interface showing `delegated: false` despite on-chain confirmation

Result: Wasted gas on 17 wallets (distribution) before discovering the flow was broken.

### Correct Workflow
```
1. Generate 50 wallets
2. Deposit ETH to wallet #1 ONLY
3. TEST on wallet #1:
   a. Delegate
   b. Verify delegation (eth_getCode)
   c. Mint (via MCP or web)
   d. Confirm mint succeeded
4. ONLY AFTER SUCCESS: distribute ETH to remaining 49 wallets
5. Run batch delegation + mint
```

### Budget Planning
For 50 wallets with 0.013 ETH initial deposit:
- Test wallet #1: 0.013 ETH (delegation + mint test)
- If test succeeds: distribute 0.0002 ETH × 49 = 0.0098 ETH
- Remaining in wallet #1: ~0.003 ETH (buffer)

If test fails, you've only spent gas on 1 wallet, not 50.

## Web Interface Detection Issues

**Issue:** Even when delegation is confirmed on-chain (`eth_getCode` returns `0xef0100...`), web interfaces may show `delegated: false`.

### Causes
1. **Different RPC** — Web uses `eth.merkle.io`, you used `publicnode.com`. RPC sync lag.
2. **Caching** — Frontend caches delegation status, doesn't re-check on page load.
3. **CORS errors** — Web's RPC is blocked by CORS, can't fetch delegation status at all.

### Verification (Always Use Direct RPC)
```bash
# Check delegation on-chain
curl -s -X POST https://ethereum-rpc.publicnode.com \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0",
    "method":"eth_getCode",
    "params":["0x6F44E29ab341aC030F68F6ac97Ec43Da2c2FBBD5","latest"],
    "id":1
  }' | jq -r '.result'

# Delegated: 0xef01001d370cfced3c7f9101f5dca5ee626447276d20be
# Not delegated: 0x
```

Don't trust web UI — verify via RPC.

### Workaround: Force Refresh
1. Send a dummy transaction (0 ETH to self) to trigger state change
2. Hard refresh browser (Ctrl+Shift+R)
3. Disconnect + reconnect wallet
4. Try different wallet (MetaMask instead of Bitget Wallet)

## MCP Server Timeouts

**Issue:** `https://www.brainrot.dog/api/mcp` accepts requests but never responds (timeout after 30s+).

### Symptom
```javascript
const response = await fetch(MCP_URL, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json, text/event-stream'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'tools/call',
    params: { name: 'mint', arguments: { address: '0x...' } }
  })
});
// Hangs forever, no response
```

### Possible Causes
1. **Relayer not configured** — Server error mentioned in original README
2. **Server overload** — Too many concurrent mint requests
3. **Rate limiting** — IP-based throttling
4. **Maintenance** — Temporary downtime

### Diagnosis
```bash
# Check if server is up
curl -s -o /dev/null -w "%{http_code}" https://www.brainrot.dog/api/mcp
# 200 = up, 000 = down/timeout

# Check if MCP endpoint responds to any request
timeout 10 curl -X POST https://www.brainrot.dog/api/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### Workaround
If MCP is down:
1. **Wait** — Check back in 1-2 hours
2. **Manual mint via web** — If web interface works, use that
3. **Check community** — Telegram/Discord for status updates
4. **Alternative approach** — Some projects have direct contract calls (but brainrot.dog enforces `tx.origin == RELAYER`)

## Key Takeaways

1. **Always test on 1 wallet first** before scaling to 50+
2. **Delegated EOAs cannot send normal transfers** — revoke first
3. **RPC timeouts are common on free tiers** — use manual polling or paid RPC
4. **npm run doesn't inherit env vars** — use shell wrappers
5. **Web UI delegation status is unreliable** — verify via `eth_getCode`
6. **MCP servers can be down** — have fallback plan (manual mint, wait, community check)
