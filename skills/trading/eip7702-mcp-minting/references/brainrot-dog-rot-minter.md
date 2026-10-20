# Brainrot.dog $ROT Minter Session (May 2026)

Session where user attempted to mint $ROT via brainrot.dog using EIP-7702 + MCP, encountered multiple RPC/web interface issues, and ultimately discovered the MCP server was non-responsive.

## Project Details

- **URL**: https://www.mining-project.live/play (redirects to brainrot.dog)
- **Token**: $ROT (brainrot memecoin)
- **Chain**: Ethereum mainnet
- **Delegate Contract**: `0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be`
- **MCP URL**: `https://www.brainrot.dog/api/mcp`
- **Reward**: 25,500 $ROT per slot, 10 slots max per wallet

## Troubleshooting Path

### 1. RPC Selection Critical

**Failed RPC**: `https://lb.drpc.live/ethereum/AuchdA0wR03lp6HZlnn8J5xmgvPzJv4R8IO0EjfP07KJ`
- Timeout on `waitForTransactionReceipt` (120s+)
- Delegation tx sent but never confirmed in script
- Free tier limitation

**Working RPC**: `https://ethereum-rpc.publicnode.com`
- Fast confirmation (<10s)
- No timeout issues
- Reliable for EIP-7702 txs

**Lesson**: Always test RPC with EIP-7702 delegation first. Free RPCs vary wildly in EIP-7702 support.

### 2. Web Interface Delegation Detection Lag

**Symptom**: Web UI shows `DELEGATED: FALSE` even after on-chain confirmation

**Root Cause**: Web interface uses different RPC (`eth.merkle.io`) which had connection errors:
```
HTTP request failed. URL: https://eth.merkle.io/
Details: Load failed
```

**Verification Method**:
```bash
# On-chain verification (always trust this)
cast code 0x6F44E29ab341aC030F68F6ac97Ec43Da2c2FBBD5 --rpc-url https://ethereum-rpc.publicnode.com
# Returns: 0xef01001d370cfced3c7f9101f5dca5ee626447276d20be
# Confirms delegation to 0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be
```

**Attempted Fixes** (all failed to update web UI):
- Hard refresh (Ctrl+Shift+R)
- Disconnect/reconnect wallet
- Send dummy transaction (0 ETH to self)
- Re-delegate with higher nonce

**Conclusion**: Web UI delegation status is **unreliable**. Always verify via `getCode()` and proceed with mint even if UI shows false negative.

### 3. Delegated EOA Transfer Restriction

**Issue**: After delegation, normal ETH transfers fail with:
```
TransactionExecutionError: Execution reverted with reason: gas required exceeds allowance (10500)
```

**Cause**: Delegated EOA executes via delegate contract, which doesn't support normal transfers.

**Solution**: Revoke delegation first:
```javascript
const authorization = await walletClient.signAuthorization({
  account,
  contractAddress: '0x0000000000000000000000000000000000000000'
});
const hash = await walletClient.sendTransaction({
  account,
  authorizationList: [authorization],
  to: account.address,
  data: '0x',
  value: 0n,
  gas: 100000n
});
```

**Implication**: Multi-wallet farming requires careful planning. Cannot redistribute ETH from delegated wallets without revoking first.

### 4. MCP Server Response Format

**Endpoint**: `https://www.brainrot.dog/api/mcp`

**Response Format**: Server-Sent Events (SSE), not JSON
```
event: message
data: {"result":{"content":[{"type":"text","text":"address: 0x6F4...BBD5\ndelegated: true\nETH balance: 0.0122 ETH\n$ROT balance: 0.0 ROT\nslots used: 0\nslots remaining: 10"}]},"jsonrpc":"2.0","id":1}
```

**Parsing Pattern**:
```javascript
const text = await response.text();
const lines = text.split('\n');
for (const line of lines) {
  if (line.startsWith('data: ')) {
    const data = JSON.parse(line.slice(6));
    const content = data.result?.content?.[0]?.text;
    // Process content
  }
}
```

**Headers Required**:
```javascript
{
  'Content-Type': 'application/json',
  'Accept': 'application/json, text/event-stream'
}
```

**MCP Parameter**: Use `address` not `wallet_address` in tool arguments.

### 5. MCP Server Timeout

**Symptom**: `check_wallet` tool works, but `mint` and `batch_mint` timeout after 30s+

**Test Results**:
```bash
# check_wallet - SUCCESS (returns wallet status)
curl -X POST https://www.brainrot.dog/api/mcp \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"method":"tools/call","params":{"name":"check_wallet","arguments":{"address":"0x6F4...BBD5"}}}'

# mint - TIMEOUT (no response after 30s)
curl -X POST https://www.brainrot.dog/api/mcp \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"method":"tools/call","params":{"name":"mint","arguments":{"address":"0x6F4...BBD5"}}}'
```

**Diagnosis**: Server-side relayer not configured or down. Error message from original README:
```
error: RELAYER_SERVER_URL not configured
```

**Conclusion**: MCP server operational for status checks but mint functionality unavailable. This is **outside user control** — requires project team to fix relayer configuration.

## Multi-Wallet Setup

User requested 500-wallet farming setup. Generated:
- 50 wallets with private keys
- Distribution script (0.0002 ETH per wallet)
- Auto delegate + mint script with threading

**Key Learning**: User corrected workflow multiple times:
> "proses dulu mint di wallet pertama, jangan send dulu ke yg lain"

**Correct Workflow**:
1. Generate wallets
2. Fund wallet #1 only
3. Delegate wallet #1
4. Test mint on wallet #1
5. **ONLY AFTER SUCCESS** → distribute to remaining wallets
6. Batch delegate + mint

**Rationale**: Prevents wasting gas distributing to 49 wallets if delegation/mint flow is broken.

## Scripts Created

### Delegation (with revoke support)
```javascript
// delegate-simple.mjs - Basic delegation
// delegate-force.mjs - Force re-delegate with explicit nonce
// delegate-nowait.mjs - Send tx without waiting for receipt (RPC timeout workaround)
```

### Distribution
```javascript
// distribute-simple.mjs - Send ETH to N wallets with retry
// send-all.mjs - Check all 50 wallets, send any balance to target address
```

### Farming
```javascript
// farm-all.mjs - Auto delegate + mint for all wallets
// Includes: retry logic, logging, concurrent processing
```

### Utilities
```javascript
// check-balances.mjs - Check ETH balance for all wallets
// test-mcp-simple.mjs - Test MCP endpoint connectivity
```

## Wallet Management

**Generated**: 50 wallets
**Format**: JSON with index, address, privateKey
**Backup**: `tar -czf rot-minter-backup-$(date +%Y%m%d).tar.gz wallets.json`

**First Wallet** (used for testing):
- Address: `0x6F44E29ab341aC030F68F6ac97Ec43Da2c2FBBD5`
- Private Key: `0x0ee9cb3cd297614f1d436a72349ccf41097fbc87fc906a2ebe3bc3abafae24b6`
- Status: Delegated successfully, but MCP mint unavailable

## Outcome

- ✅ Delegation working (on-chain verified)
- ✅ Multi-wallet infrastructure ready
- ❌ MCP mint endpoint non-responsive (server-side issue)
- ❌ Web interface delegation detection broken (RPC error)

**Recommendation**: Wait for project team to fix MCP relayer, or use alternative minting method if available.

## Key Takeaways

1. **Test first wallet completely** before scaling to multiple wallets
2. **Trust on-chain verification** over web UI status
3. **RPC selection matters** for EIP-7702 (publicnode.com > drpc.live)
4. **MCP server availability** is outside user control
5. **Delegated wallets cannot send normal transfers** without revoking first
6. **SSE parsing required** for MCP responses
7. **User workflow preferences** should be followed (test before distribute)
