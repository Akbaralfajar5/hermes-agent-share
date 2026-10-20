# EIP-7702 + MCP Minting Pattern

Pattern used by brainrot.dog ($ROT token) and similar projects that combine:
- EIP-7702 delegation (Pectra upgrade)
- MCP (Model Context Protocol) for gasless minting via relayer

## Architecture

1. **Wallet delegates** to a contract via EIP-7702 authorization
2. **MCP server** (e.g., `brainrot.dog/api/mcp`) exposes tools:
   - `check_wallet` - verify delegation status
   - `get_supply` - check token supply
   - `mint` / `batch_mint` - trigger relayer to mint
3. **Relayer pays gas** - user doesn't send tx directly

## Multi-Wallet Farming Script Structure

### Core Scripts

```
generate-wallets.mjs    # Generate N wallets with viem
distribute-eth.mjs      # Send ETH from wallet #1 to all others
farm-all.mjs           # Delegate + mint loop for all wallets
check-balances.mjs     # Monitor ETH balances
```

### Key Implementation Details

**Wallet Generation:**
```javascript
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts';

const privateKey = generatePrivateKey();
const account = privateKeyToAccount(privateKey);
// Save: { index, address, privateKey }
```

**EIP-7702 Delegation:**
```javascript
const hash = await walletClient.sendTransaction({
  to: DELEGATE_CONTRACT,
  value: 0n,
  authorizationList: [{
    contractAddress: DELEGATE_CONTRACT,
    chainId: chain.id,
    nonce: await publicClient.getTransactionCount({ address })
  }]
});
```

**Check if already delegated:**
```javascript
const code = await publicClient.getCode({ address });
if (code && code !== '0x') {
  // Already delegated
}
```

**MCP Mint Call:**
```javascript
const response = await fetch(MCP_URL, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: count === 1 ? 'mint' : 'batch_mint',
      arguments: {
        wallet_address: address,
        ...(count > 1 ? { count } : {})
      }
    }
  })
});
```

### Retry Logic

MCP servers can be flaky. Implement exponential backoff:

```javascript
let retries = 0;
while (MAX_RETRIES === 0 || retries < MAX_RETRIES) {
  try {
    // ... mint call
    return true;
  } catch (error) {
    retries++;
    if (MAX_RETRIES > 0 && retries >= MAX_RETRIES) break;
    await new Promise(resolve => setTimeout(resolve, RETRY_DELAY_MS));
  }
}
```

### Environment Variables

```bash
RPC_URL=https://your-eip7702-rpc-url  # MUST support Pectra
MCP_URL=https://project.domain/api/mcp
MINT_COUNT=10                          # Mints per wallet
RETRY_DELAY_MS=15000                   # 15s between retries
MAX_RETRIES=3                          # 0 = unlimited
```

### Shell Wrappers

Create `.sh` wrappers that load `.env` automatically:

```bash
#!/bin/bash
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$RPC_URL" ]; then
    echo "❌ RPC_URL not set!"
    exit 1
fi

npm run farm
```

This avoids `export $(grep .env)` in every command.

## Pitfalls

### "RPC_URL not set" despite .env file
`npm run` doesn't inherit shell env. Use wrapper scripts that `export $(grep .env)` first.

### "Missing or invalid parameters" from RPC
Default RPC in script (e.g., `ankr.com/eth`) requires API key. Always check env var is actually loaded.

### "RELAYER_SERVER_URL not configured"
Error from MCP server, not your wallet. Implement retry logic with configurable `MAX_RETRIES=0` for unlimited.

### Delegation fails silently
Not all RPCs support EIP-7702 yet (Pectra upgrade). Use providers that explicitly advertise support (e.g., drpc.live).

### Rate limiting
Add delays between wallets (3-5s) and between retries (15s+). MCP servers can throttle aggressive clients.

## Gas Estimation

- **Delegation:** ~0.0001 ETH per wallet (one-time)
- **Minting:** FREE (relayer pays)
- **Distribution tx:** ~0.00002 ETH per send

For 50 wallets with 0.001 ETH each:
- Distribution: 0.05 ETH
- Gas: ~0.01 ETH
- **Total: ~0.06 ETH**

## User Experience Patterns

### Progress Logging
Log to both console and file:
```javascript
function log(msg) {
  const timestamp = new Date().toISOString();
  console.log(msg);
  appendFileSync('farming-log.txt', `[${timestamp}] ${msg}\n`);
}
```

### Summary Stats
Track and report:
- Total wallets processed
- Successful delegations
- Successful mints
- Failed operations
- Total tokens minted

### Backup Automation
Generate backup on wallet creation:
```bash
tar -czf backup-$(date +%Y%m%d).tar.gz wallets.json .env
```

## Example Projects

- **brainrot.dog** ($ROT) - 10 mints/wallet, 25,500 ROT per mint
- **dogeshit.meme** ($SHIT) - Similar pattern

## References

- EIP-7702: https://eips.ethereum.org/EIPS/eip-7702
- MCP Spec: https://modelcontextprotocol.io/
