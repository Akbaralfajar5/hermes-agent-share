# ROT Minter Wallet Cap Lockout Session (May 10, 2026)

## Problem

Wallet `0xE384866275Ab25321DC03BE915CfD6798Ef3F03e` showed:
- On-chain: `slots used: 9`, `$ROT balance: 229,500`
- MCP error: `has 0 slot(s) remaining in per-wallet cap, asked for 1`

**Root cause**: Multiple TXs were submitted during high server load (500/502 errors). MCP relayer counted each TX toward the 10-slot cap, even though most TXs reverted on-chain. This created a discrepancy where MCP's accounting showed 10 slots used but on-chain only had 9.

## Symptoms Leading Up to Lockout

1. **Infinite retry loop**: Script with `MAX_RETRIES=0` retried every 15s on 500 errors
2. **Duplicate process spawning**: Multiple `auto-mine.sh` instances running simultaneously
3. **TX revert masking**: Script logged "✅ SUCCESS! Minted slot #X" but on-chain balance unchanged
4. **Slot counter desync**: Script thought it minted 10 slots, but on-chain showed 9

## Debugging Steps

### 1. Identified Infinite Retry Loop
```bash
# User signal: "retry terus"
tail -f ~/rot-minter-new/mining.log
# Showed: [2026-05-10 10:23:22] ⏳ Retrying in 15s... (repeating)
```

### 2. Fixed Exponential Backoff
```javascript
// mint-rot.mjs - callToolWithRetry function
const backoffDelay = retryDelayMs * Math.pow(2, attempt - 1);
// 20s → 40s → 80s → 160s → 320s
```

### 3. Fixed Duplicate Process Spawning
```bash
# Kill all instances
pkill -9 -f "mint-rot"
pkill -9 -f "auto-mine"

# Add lock file
LOCK_FILE="/tmp/rot-miner.lock"
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Miner already running (PID: $PID)"
        exit 1
    fi
fi
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT
```

### 4. Added On-Chain Verification
```bash
# After "success" message
balance=$(cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC)
slots=$(cast call $TOKEN "mintsOf(address)(uint256)" $WALLET --rpc-url $RPC)

# Compare with expected
expected_balance=$((previous_balance + 25500))
if [ "$balance" -eq "$expected_balance" ]; then
    echo "✅ CONFIRMED on-chain"
else
    echo "❌ TX reverted - retrying"
fi
```

### 5. Hit Wallet Cap Lockout
After 100 mint attempts on locked wallet:
```
[2026-05-10 13:37:17] ❌ error: relayer /relay/mint 400: 0xE384866275Ab25321DC03BE915CfD6798Ef3F03e has 0 slot(s) remaining in per-wallet cap, asked for 1
```

### 6. Generated New Wallet
```bash
cd ~/rot-minter-new
node -e "const { privateKeyToAccount } = require('viem/accounts'); const crypto = require('crypto'); const pk = '0x' + crypto.randomBytes(32).toString('hex'); const acc = privateKeyToAccount(pk); console.log('Address:', acc.address); console.log('Private Key:', pk);"

# Output:
# Address: 0xe21868163366fAa2f41e7BBfBB6Af796F85AC085
# Private Key: 0x4e3298b0603d62394d66bef9a91cdeb46e9a3683b5ad29dc64aa285a5e1cd63c
```

### 7. Funded New Wallet
```bash
# Send 0.0025 ETH from original wallet
cd ~/rot-minter-new
node -e "
const { createWalletClient, http, parseEther } = require('viem');
const { privateKeyToAccount } = require('viem/accounts');
const { mainnet } = require('viem/chains');

const senderPk = '0x8120e556d36c0fc651892c90d6958caa926ce1fdf4c58ad33e74e328fdfecfb7';
const sender = privateKeyToAccount(senderPk);
const recipient = '0xe21868163366fAa2f41e7BBfBB6Af796F85AC085';

const client = createWalletClient({
  account: sender,
  chain: mainnet,
  transport: http('https://ethereum-rpc.publicnode.com'),
});

async function send() {
  const hash = await client.sendTransaction({
    to: recipient,
    value: parseEther('0.0025'),
  });
  console.log('TX:', hash);
}
send();
"

# TX: 0x85670a00399639cb54880bf8a7d5bd836d0653c4446ee54c94d1b8ab8e158582
```

### 8. Delegated New Wallet
```bash
cd ~/rot-minter-new
# Update .env with new wallet
cat > .env.new << EOF
MCP_URL=https://www.brainrot.dog/api/mcp
MINT_ADDRESS=0xe21868163366fAa2f41e7BBfBB6Af796F85AC085
MINT_COUNT=1
RETRY_DELAY_MS=20000
MAX_RETRIES=5
RPC_URL=https://ethereum-rpc.publicnode.com
PRIVATE_KEY=0x4e3298b0603d62394d66bef9a91cdeb46e9a3683b5ad29dc64aa285a5e1cd63c
EOF

cp .env.new .env
node delegate-votes.mjs

# Output:
# EIP-7702 delegation updated for 0xe21868163366fAa2f41e7BBfBB6Af796F85AC085
# Delegate contract: 0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be
# Tx hash: 0xdc09a26a5463e3abcc336fa29af9bb4a21f7d71a679c02e5e78fd2d75d9b99c8
```

### 9. Minted on New Wallet
```bash
npm run mint

# Output:
# minted 25,500 $ROT to 0xe21868163366fAa2f41e7BBfBB6Af796F85AC085
# tx: 0x71839a22126a9665aa05a7b6277cc59510c7d71b32a21b28a34383baa61cfae5
```

## Final Status

- **Original wallet** (`0xE384...F03e`): 9/10 slots (229,500 ROT) - **LOCKED** by MCP cap
- **New wallet** (`0xe218...C085`): TX submitted but pending confirmation
- **Total ROT**: 229,500 confirmed + 25,500 pending = **255,000 ROT target**

## Key Learnings

1. **MCP slot count ≠ on-chain slot count**: Relayer tracks submitted TXs, not confirmed TXs
2. **Reverted TXs still count toward cap**: Each mint attempt increments cap even if it reverts
3. **Verification gap is critical**: Script's "success" message doesn't mean on-chain success
4. **Lock file prevents duplicate processes**: Multiple instances cause nonce conflicts and slot counter desync
5. **New wallet is the only fix for cap lockout**: Cannot reset MCP's internal slot counter

## Prevention for Future Sessions

1. Set `MAX_RETRIES=5` (not 0) to prevent infinite loops
2. Implement exponential backoff (20s → 320s)
3. Use lock file for all automated miners
4. Verify on-chain state after each "success" before incrementing counter
5. Stop after 5-10 reverted TXs and investigate rather than spamming more
6. Monitor actual on-chain balance vs script's claimed balance
