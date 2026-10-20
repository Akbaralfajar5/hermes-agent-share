# Brainrot `$ROT` Token Minting

**Project:** brainrot.dog  
**Token:** `$ROT` (ERC-20 on Ethereum mainnet)  
**Pattern:** EIP-7702 delegation + MCP-gated minting via relayer  
**Repo:** https://github.com/AganFebro/rot-minter (community helper scripts)

## Architecture

```
User Wallet (EOA)
    ↓ EIP-7702 delegation
FeedDelegate Contract (0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be)
    ↓ MCP tool call
brainrot.dog MCP Server (https://www.brainrot.dog/api/mcp)
    ↓ relayer executes mint
$ROT Token Contract
```

**Key insight:** Minting is NOT done by sending transactions directly. The user delegates their wallet to `FeedDelegate`, then calls the MCP server's `mint` or `batch_mint` tool. The MCP server's relayer executes the actual mint transaction on-chain.

## Contracts

- **FeedDelegate:** `0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be` (delegation target)
- **$ROT Token:** (address not documented in helper repo, likely returned by MCP `get_supply` tool)

## Workflow

### 1. Delegate Wallet (EIP-7702)

**Using Foundry `cast`:**
```bash
export RPC_URL="https://ethereum-rpc.publicnode.com"  # or any Pectra-enabled RPC
export PRIVATE_KEY="0x..."

cast send $WALLET_ADDRESS \
  --private-key $PRIVATE_KEY \
  --rpc-url $RPC_URL \
  --auth 0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be \
  --value 0 \
  --gas-limit 100000
```

**Using viem (Node.js):**
```javascript
import { createWalletClient, createPublicClient, http } from 'viem';
import { privateKeyToAccount } from 'viem/accounts';

const DELEGATE_CONTRACT = '0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be';
const RPC_URL = process.env.RPC_URL;

const account = privateKeyToAccount(process.env.PRIVATE_KEY);
const chain = {
  id: 1,
  name: 'Ethereum',
  rpcUrls: { default: { http: [RPC_URL] } }
};

const publicClient = createPublicClient({ chain, transport: http(RPC_URL) });
const walletClient = createWalletClient({ account, chain, transport: http(RPC_URL) });

// Check if already delegated
const code = await publicClient.getCode({ address: account.address });
if (code && code !== '0x') {
  console.log('Already delegated');
} else {
  // Delegate via EIP-7702
  const hash = await walletClient.sendTransaction({
    to: DELEGATE_CONTRACT,
    value: 0n,
    authorizationList: [{
      contractAddress: DELEGATE_CONTRACT,
      chainId: chain.id,
      nonce: await publicClient.getTransactionCount({ address: account.address })
    }]
  });
  await publicClient.waitForTransactionReceipt({ hash });
  console.log('Delegation confirmed:', hash);
}
```

**Verification:**
```bash
cast code $WALLET_ADDRESS --rpc-url $RPC_URL
# Should return: 0xef0100 + 20-byte address (lowercase)
# Example: 0xef01001d370cfced3c7f9101f5dca5ee626447276d20be
```

### 2. Mint via MCP

**MCP Endpoint:** `https://www.brainrot.dog/api/mcp`

**Available Tools:**
- `check_wallet` — Check if wallet is delegated
- `get_supply` — Get current $ROT supply
- `mint` — Mint 1 slot (25,500 ROT)
- `batch_mint` — Mint multiple slots (max 10 per wallet)

**Mint 1 slot:**
```javascript
const response = await fetch('https://www.brainrot.dog/api/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: 'mint',
      arguments: {
        wallet_address: '0x...'
      }
    }
  })
});

const data = await response.json();
console.log(data.result.content[0].text);
```

**Batch mint (10 slots = 255,000 ROT):**
```javascript
const response = await fetch('https://www.brainrot.dog/api/mcp', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: '2.0',
    id: Date.now(),
    method: 'tools/call',
    params: {
      name: 'batch_mint',
      arguments: {
        wallet_address: '0x...',
        count: 10
      }
    }
  })
});
```

## Multi-Wallet Farming

**Repo structure (from AganFebro/rot-minter):**
```
rot-minter/
├── generate-wallets.mjs    # Generate N wallets
├── distribute-eth.mjs       # Distribute ETH from wallet #1
├── farm-all.mjs            # Auto delegate + mint all wallets
├── check-balances.mjs      # Check balance all wallets
├── delegate-votes.mjs      # Single wallet delegation
├── mint-rot.mjs           # Single wallet mint
├── wallets.json           # Generated wallets (PRIVATE!)
└── farming-log.txt        # Activity log
```

**Key scripts:**

1. **Generate wallets:**
```bash
WALLET_COUNT=50 npm run generate
# Creates wallets.json, wallets.csv, wallets.env
```

2. **Distribute ETH:**
```bash
export RPC_URL="https://ethereum-rpc.publicnode.com"
AMOUNT_PER_WALLET=0.001 npm run distribute
# Sends ETH from wallet #1 to all others
```

3. **Farm all:**
```bash
export RPC_URL="https://ethereum-rpc.publicnode.com"
npm run farm
# Delegates + mints 10x for each wallet
# Logs to farming-log.txt
```

**Budget for 50 wallets:**
- Delegation gas: ~0.0001 ETH per wallet = 0.005 ETH
- Mint gas: FREE (relayer pays)
- Distribution gas: ~0.00002 ETH per tx = 0.001 ETH
- ETH per wallet: 0.001 ETH (buffer for delegation)
- **Total: ~0.06 ETH**

**Expected yield:**
- 50 wallets × 10 mint × 25,500 ROT = **12,750,000 ROT**

## Retry Logic

The MCP server can return errors like `RELAYER_SERVER_URL not configured` during high load. The helper scripts implement auto-retry:

```javascript
const RETRY_DELAY_MS = 15000;  // 15 seconds
const MAX_RETRIES = 3;         // 0 = unlimited

let retries = 0;
while (MAX_RETRIES === 0 || retries < MAX_RETRIES) {
  try {
    // ... mint call ...
    break;
  } catch (error) {
    retries++;
    if (MAX_RETRIES > 0 && retries >= MAX_RETRIES) break;
    await sleep(RETRY_DELAY_MS);
  }
}
```

## Pitfalls

1. **RPC must support EIP-7702 (Pectra)** — Not all Ethereum RPCs have upgraded. Use: `ethereum-rpc.publicnode.com`, Alchemy, Infura (check their docs for Pectra support).

2. **Delegation target confusion** — The delegation target is `FeedDelegate` (`0x1D37...20be`), NOT the $ROT token contract. Delegating to the wrong address wastes gas and requires re-delegation.

3. **Failed tx still applies delegation** — EIP-7702 delegation txs may show `status: 0 (failed)` in explorers but the delegation IS applied. Always verify with `cast code $ADDRESS`.

4. **MCP server errors are transient** — `RELAYER_SERVER_URL not configured` means the relayer is temporarily unavailable. Retry with exponential backoff. Don't spam the server.

5. **Max 10 mints per wallet** — The contract enforces a per-wallet mint limit. Attempting more will fail.

6. **Gas estimation fails for self-txs** — When delegating (sending to your own address), `cast` gas estimation often fails. Always set explicit `--gas-limit 100000`.

7. **Wallet security** — `wallets.json` contains private keys. Never commit to git. Add to `.gitignore`.

8. **Funding math** — With 0.001 ETH per wallet, you can delegate + mint. If you need to do other operations (transfers, approvals), increase the amount.

9. **Rate limiting** — When farming 50+ wallets, add delays between operations (3-5 seconds between wallets) to avoid rate limits on both RPC and MCP server.

10. **No direct on-chain minting** — You CANNOT call the $ROT contract directly. Minting is only possible via the MCP server's relayer. This is by design (anti-bot measure).

11. **Process health monitoring** — Miners running in background can crash silently without updating logs. Symptoms: log shows repeated attempts then stops, but `process list` shows no running processes. Always verify with `process list` or check if the process PID is alive, not just tail the log. The MCP server can also degrade to returning HTML instead of JSON (maintenance mode), causing all mint attempts to fail with parse errors.

12. **Per-wallet cap confusion** — When relayer returns "has 0 slot(s) remaining in per-wallet cap", the wallet is FULL (10/10 complete). This is SUCCESS, not failure. However, if the log shows a lower slot count (e.g., "Slots: 3/10") but the error says "0 remaining", check on-chain balance — the relayer may be reporting stale state or there may be a global cap change.

## Monitoring

**Check delegation status:**
```bash
cast code $WALLET_ADDRESS --rpc-url $RPC_URL
```

**Check balance:**
```bash
cast balance $WALLET_ADDRESS --rpc-url $RPC_URL
```

**Monitor farming log:**
```bash
tail -f farming-log.txt
```

**Check all wallet balances:**
```bash
npm run balance
```

## VPS Deployment

The helper scripts are designed to run on VPS for 24/7 farming:

```bash
# Clone repo
git clone https://github.com/AganFebro/rot-minter.git
cd rot-minter
npm install

# Generate wallets
WALLET_COUNT=50 npm run generate

# Deposit ETH to wallet #1 (shown in output)

# Setup RPC
export RPC_URL="https://ethereum-rpc.publicnode.com"

# Distribute
npm run distribute

# Farm (run in screen/tmux)
screen -dmS rot npm run farm

# Monitor
tail -f farming-log.txt
```

## Related Patterns

- **EIP-7702 delegation** — See `references/eip7702-mcp-minting.md` for dogeshit.meme (similar pattern but with Claude.ai MCP connector requirement)

## References

- Repo: https://github.com/AganFebro/rot-minter
- MCP endpoint: https://www.brainrot.dog/api/mcp
- FeedDelegate: `0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be`
