# Brainrot $ROT Minting — RPC Strategy Session Notes

## Context
Multi-account mining of brainrot.dog $ROT tokens via EIP-7702 delegation + MCP-gated minting. Backend (MCP server at `brainrot.dog`) was severely degraded with frequent timeouts and 500/502 errors.

## RPC Progression & Results

### Timeline
1. **Initial setup**: Public RPC (`ethereum-rpc.publicnode.com`)
   - Account 1: Successfully minted slots 1-7 (178,500 ROT)
   - Account 2: Delegated successfully
   
2. **User provided premium RPC**: drpc.live (2 different keys for 2 accounts)
   - Switched both accounts
   - No improvement in mint success rate
   
3. **User provided Ankr premium**: `rpc.ankr.com/eth/[key]`
   - Switched both accounts
   - Delegation worked instantly
   - But minting still timed out (MCP issue, not RPC)
   
4. **Returned to public RPC**: User's decision after seeing no improvement
   - Account 1: Minted slot 8, then slot 9 (229,500 ROT total)
   - Account 2: Minted slot 1, then slot 2 (51,000 ROT total)
   - **Public RPC proved most reliable for this specific backend**

## Key Learning: Test-and-Hold Strategy

**User's approach (correct):**
- Try RPC A → observe results for 10+ minutes
- If mints succeed → keep using it
- Only switch when prolonged failure (30+ min no success)
- Manual switching based on observed results

**Agent's initial approach (wrong):**
- Proposed automatic RPC rotation every 10 minutes
- Would have introduced unnecessary variables
- User rejected: "yaudah kalo gitu mending pake rpc publik"

## Why Public RPC Won

The bottleneck was **MCP server `brainrot.dog`**, not RPC quality:
- All RPCs could handle delegation (fast operation)
- All RPCs could submit mint transactions
- The timeout happened at MCP fetch (30-45s hang)
- Premium RPCs didn't improve MCP response time

Public RPC worked best because:
1. Lower latency to MCP server (geographic routing?)
2. Less aggressive rate limiting on repeated failed calls
3. Or simply: timing coincidence (MCP recovered during public RPC period)

## Batch vs Sequential Decision

**User correction:** "satu satu aja deh jangan batch yg akun 1"

Agent tried batch parallel minting (3 slots simultaneously) to speed up completion. All 3 hung at MCP timeout. User immediately reverted to sequential.

**Reason:** When backend is degraded, parallel requests:
- Amplify server load
- All fail together
- No benefit over sequential

Sequential with aggressive retry (2s) gives each mint the best chance to slip through during brief windows of server availability.

## Retry Configuration

```javascript
// Aggressive retry that worked
const RETRY_DELAY = 2000; // 2 seconds between attempts
const COOLDOWN_AFTER = 10; // After 10 consecutive failures
const COOLDOWN_DURATION = 10000; // 10 second cooldown

// This kept trying until MCP server had brief availability windows
```

## Miner Architecture

```bash
~/rot-miner-new/          # Account 1
~/rot-miner-account2/     # Account 2

# Each folder:
.env                      # PRIVATE_KEY, MINT_ADDRESS, RPC_URL
aggressive-mine.sh        # Retry loop wrapper
mining.log               # Append-only log
```

## Commands Used

```bash
# Switch RPC (both accounts)
cd ~/rot-miner-new && sed -i 's|RPC_URL=.*|RPC_URL=NEW_RPC|' .env
cd ~/rot-miner-account2 && sed -i 's|RPC_URL=.*|RPC_URL=NEW_RPC|' .env

# Restart miners
pkill -f "aggressive-mine.sh"
cd ~/rot-miner-new && ./aggressive-mine.sh &
cd ~/rot-miner-account2 && ./aggressive-mine.sh &

# Check balance on-chain
cast call 0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be \
  "balanceOf(address)(uint256)" $ADDRESS \
  --rpc-url $RPC
```

## Final State

- **Account 1**: 9/10 slots (229,500 ROT) — 1 slot remaining
- **Account 2**: 2/10 slots (51,000 ROT) — 8 slots remaining
- **RPC**: Public `ethereum-rpc.publicnode.com` (fixed, no rotation)
- **Strategy**: Sequential minting with 2s aggressive retry

## Takeaway for Future Sessions

When dealing with unreliable mining backends:
1. **Don't assume premium RPC = better results** — test first
2. **Manual RPC switching > automatic rotation** — let user decide based on observed results
3. **Sequential > batch parallel** when backend is degraded
4. **Aggressive retry on same RPC** beats premature switching
5. **The bottleneck is often NOT the RPC** — could be MCP server, relayer, or on-chain congestion
