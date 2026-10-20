---
name: eip7702-mcp-minting
description: "EIP-7702 delegation + MCP-gated token minting workflows (dogeshit.meme pattern)"
version: 1.0.0
author: hermes
tags: [eip-7702, mcp, minting, ethereum, delegation, web3]
---

# EIP-7702 MCP-Gated Minting

Handle projects that use EIP-7702 wallet delegation + MCP (Model Context Protocol) servers to gate minting through AI assistants (Claude.ai, etc).

## When to Use

- User shares a mint link that mentions EIP-7702, MCP, or "mint through Claude"
- Project requires wallet delegation before minting
- Minting is gated behind an MCP server that only specific AI platforms can call

## User Workflow Preferences

### Stop Immediately When Asked
- **Signal**: User says "stop dulu" (stop first) or "STOP" repeatedly
- **Action**: Immediately kill all running processes, don't continue with pending operations
- **Context**: When debugging or troubleshooting, user may want to pause automation to assess state
- **Pattern**:
  ```bash
  pkill -9 -f "mint-rot"
  pkill -9 -f "auto-mine"
  rm -f /tmp/rot-miner.lock
  ```
- **Don't**: Continue with "let me just finish this one thing" — stop means stop NOW

## Architecture Pattern

```
User Wallet (EOA) --[EIP-7702 delegate]--> MintDelegate Contract
                                                |
Claude.ai --[MCP call]--> Project MCP Server --[Relayer TX]--> User's Delegated Wallet
                                                |
                                          Token Contract mints to msg.sender
```

Key contracts (typical):
- **Token**: ERC20 token contract (holds balanceOf, totalMints, mintsOf)
- **MintDelegate**: Stateless contract that wallets delegate to (has mint(), batchMint(uint256))
- **Relayer**: EOA that sends mint txs (tx.origin check enforced on-chain)

## Step-by-Step Workflow

### 1. Reconnaissance
```bash
# Get project config
curl -s "https://<project>/api/config" | python3 -m json.tool

# Identify contracts from page source
# Look for 0x addresses in HTML/JS
```

### 2. EIP-7702 Delegation (using Foundry cast)

```bash
# Install foundry if needed
export PATH="$HOME/.foundry/bin:$PATH"

# Delegate wallet to MintDelegate
cast send $WALLET \
  --private-key $PK \
  --rpc-url $RPC \
  --auth $MINT_DELEGATE_ADDRESS \
  --value 0 \
  --gas-limit 100000

# Verify delegation
cast code $WALLET --rpc-url $RPC
# Should show: 0xef0100<mintdelegate_address>
```

### 3. Trigger Mint via Claude.ai

User must:
1. Go to Claude.ai Settings → Connectors → "Tambah konektor kustom"
2. Add MCP URL (e.g., `https://project.com/mcp`)
3. Complete OAuth/SIWE flow (connect wallet in browser)
4. Chat: "mint me X slots"

### 4. Monitor Status

```bash
# Check mint status
cast call $TOKEN "mintsOf(address)(uint256)" $WALLET --rpc-url $RPC
cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC
cast call $TOKEN "totalMints()(uint256)" --rpc-url $RPC

# Monitor gas (relayers have gas caps)
cast base-fee --rpc-url $RPC
```

## Post-Mint Trading

Once supply is exhausted, tokens typically list on Uniswap (ETH L1). Key observations from dogeshit.meme:

- **Liquidity is thin** (~$50-60K) — slippage brutal for >$500 trades
- **Pump pattern**: +700%+ in first 24h after supply cap hit (FOMO from latecomers)
- **Re-entry after selling**: Wait for retrace. Use Fibonacci levels from 24h low→high:
  - Aggressive: -10% from current (Fib 0.236)
  - Moderate: -20% (Fib 0.382)
  - Conservative: -30% (Fib 0.5)
- **Stop loss**: Below Fib 0.618 (-15% from entry)
- **FDV context**: 420B supply × $0.0000035 = ~$740K FDV. Free mint → many holders will dump
- **Multiple Uniswap pools**: Liquidity fragments across pools — check DexScreener for main pool (highest liquidity)
- **DexScreener search**: `curl -s "https://api.dexscreener.com/latest/dex/search?q=<token_name>"` — filter by chainId and liquidity

## Pitfalls

### Test First Wallet Before Batch Distribution (CRITICAL)
- **Always delegate + mint on wallet #1 FIRST** before distributing ETH to other wallets
- Verify the full flow works (delegation confirms, MCP responds, mint succeeds) on one wallet
- Only after successful test mint should you distribute ETH and scale to remaining wallets
- Prevents wasting gas distributing to 50+ wallets if delegation/mint flow is broken
- User frustration signal: "proses dulu mint di wallet pertama, jangan send dulu ke yg lain"
- **Workflow**: Generate wallets → Fund wallet #1 → Delegate #1 → Test mint #1 → THEN distribute to others
- If user says "STOP" or "jangan distribusi dulu", immediately halt distribution and focus on testing wallet #1

### Web Interface Delegation Status Unreliable
- Web UI may show `DELEGATED: FALSE` even when on-chain delegation is confirmed
- Root cause: Web uses different RPC (e.g., `eth.merkle.io`) which may be down, cached, or out of sync
- **Always verify delegation via script** with `publicClient.getCode({ address })` — ignore web UI
- Delegated wallet returns code starting with `0xef0100<delegate_address>`
- Refreshing page, clearing cache, reconnecting wallet, or sending dummy tx may not fix stale UI
- If web UI shows RPC error but script confirms delegation, **delegation is valid** — proceed with mint

### Free RPC EIP-7702 Limitations
- Free RPC tiers (drpc.live, llamarpc) **timeout on `waitForTransactionReceipt`** for EIP-7702 txs
- Delegation tx sends successfully but RPC times out waiting for receipt (120s+)
- **Confirmed working RPC**: `https://ethereum-rpc.publicnode.com` (fast, no timeout, May 2026)
- **Failed RPCs**: `https://lb.drpc.live/ethereum/...` (timeout), `https://eth.llamarpc.com` (rate limit)
- **Solution**: Use `publicnode.com` RPC or skip wait and poll manually with sleep
- Pattern: send tx → log hash → sleep 30s → check delegation with `cast code`
- Explicit gas limit required: `gas: 100000n` (intrinsic gas too low without it)
- If switching RPCs mid-session, update `.env` and reload: `export $(grep -v '^#' .env | xargs)`

### Delegated EOA Transfer Restriction
- **Once delegated, EOA cannot send normal ETH transfers** — execution reverts with "gas required exceeds allowance"
- Root cause: Delegated EOA executes via delegate contract, which may not have fallback for normal transfers
- **Must revoke delegation first** to send ETH: sign authorization to `0x0000000000000000000000000000000000000000`
- Revoke pattern:
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
- After revoke, normal transfers work again
- **Implication for multi-wallet farming**: Cannot redistribute ETH from delegated wallets without revoking first

### brainrot.dog MCP API Changed (May 2026)
- **Old tools (deprecated)**: `balance`, `mint` (with different schema)
- **New tools (current)**: `check_wallet`, `get_supply`, `mint`, `batch_mint`, `check_mint_status`
- `check_wallet` replaces `balance` — returns delegation status, ETH balance, ROT balance, slots used/remaining
- `batch_mint` is new — mint multiple slots in one call (more gas-efficient)
- `check_mint_status` is new — poll job status when relayer is busy (returns `job_id` instead of tx hash)
- **Always call `tools/list` first** to discover current tool names before scripting
- Old scripts using `npm run mint` (which called old MCP tools) will fail with "Tool balance not found"
- **Working curl pattern for new API**:
  ```bash
  curl -s -X POST https://www.brainrot.dog/api/mcp \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_wallet","arguments":{"address":"0x..."}},"id":1}' \
    | grep '^data:' | sed 's/^data: //'
  ```

### MCP Server Response Format
- MCP endpoints return **Server-Sent Events (SSE)**, not plain JSON
- Response format: `event: message\\ndata: {json}\\n\\n`
- Must parse SSE: split by `\\n`, find lines starting with `data: `, parse JSON
- Fetch headers must include: `'Accept': 'application/json, text/event-stream'`
- **MCP parameter is `address` not `wallet_address`** (check MCP schema first)
- Mint endpoints may timeout (30s+) if relayer is down or not configured
- **Parsing pattern**:
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
- Use `AbortController` with 30s timeout to prevent hanging on unresponsive MCP servers
- **MCP server availability is outside user control** — if mint endpoint times out, check project Telegram/Discord for status
- `check_wallet` tool may work while `mint`/`batch_mint` timeout — indicates server-side relayer issue, not delegation problem

### EIP-7702 Browser Requirement (CRITICAL)
- Even if delegation is done via `cast`, the **OAuth/SIWE flow for Claude.ai MCP** requires the user to sign in-browser at the project's `/connect` page
- Claude.ai will say "wallet hasn't been authorized yet" if EIP-7702 wasn't signed through the web UI
- The browser flow does BOTH: EIP-7702 delegation + OAuth token generation for MCP
- **Cannot be fully automated from VPS** — user must interact with browser wallet extension

### Delegation Target Confusion
- `/api/config` response labels may be counterintuitive
- `"token"` in config = ERC20 contract (NOT what you delegate to)
- `"mintDelegate"` in config = what wallet delegates to
- Always verify with `cast code` after delegation

### EIP-7702 TX Status
- Type-4 tx may show `status: 0 (failed)` but delegation STILL gets applied
- Always check `cast code $WALLET` after tx regardless of status
- The "failure" is often the self-tx execution reverting, not the authorization

### MCP IP Restriction
- Most MCP endpoints are IP-restricted to Claude.ai's server ranges
- Cannot be bypassed with headers (X-Forwarded-For, Origin spoofing)
- Cloudflare enforces at network level
- **Cannot call MCP from VPS/local machine** — must go through Claude.ai

### Claude.ai Access
- MCP connectors work on **Free tier** (confirmed May 2026)
- Settings path: Settings → Konektor → "Tambah konektor kustom" → paste MCP URL
- Or direct URL: `https://claude.ai/settings/connectors?add_custom_connector=<MCP_URL>`
- Cloudflare blocks headless browsers and curl from accessing claude.ai
- HttpOnly cookies (sessionKey=sk-ant-sid02-...) can't be extracted via document.cookie
- Even with full cookies, VPS requests get CF challenge (403 cf-mitigated: challenge)
- User must interact with Claude.ai directly — no automation possible from server side
- Claude may respond generically ("What are you looking to create?") if connector not properly linked — user should verify connector appears in Settings first

### Claude.ai Retry Strategy
- When gas/queue blocks mint, tell Claude: "Keep retrying until conditions improve"
- Claude will auto-retry but Free tier has message limits — may stop after N retries
- For continuous retry: "Keep retrying continuously without stopping until the mint succeeds"
- If Claude stops, open new chat and re-issue mint command
- Claude shows "Searched available tools >" when MCP is properly connected

### MCP Relayer TX Success ≠ On-Chain Confirmation (CRITICAL)
- **Problem**: MCP relayer returns TX hash and "SUCCESS" message even when transaction reverts on-chain
- **Symptoms**: Script logs show "✅ SUCCESS! Minted slot #X | TX: 0x..." but balance doesn't increase, slots_used stays same
- **Root cause**: Relayer submits TX and returns hash immediately, but TX can revert later (nonce conflict, gas issues, contract revert)
- **Impact**: Automated miners think they succeeded and move to next slot, but actual on-chain state unchanged
- **Solution**: Always verify on-chain state after "success"
  ```bash
  # After mint attempt
  if echo "$output" | grep -q "minted 25,500"; then
      # Don't trust the output alone - verify on-chain
      balance=$(cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC)
      slots=$(cast call $TOKEN "mintsOf(address)(uint256)" $WALLET --rpc-url $RPC)
      
      # Compare with expected state
      expected_balance=$((previous_balance + 25500))
      if [ "$balance" -eq "$expected_balance" ]; then
          echo "✅ CONFIRMED on-chain"
      else
          echo "❌ TX reverted - balance unchanged"
          # Retry this slot
      fi
  fi
  ```
- **Best practice**: Query `mintsOf(address)` or `balanceOf(address)` after each "success" before incrementing counter
- **User frustration signal**: "baru 4 yang masuk" when script claims 10 succeeded = verification gap

### MCP Script Retry Loop (Automated Minting)
- **Problem**: Scripts with `MAX_RETRIES=0` (unlimited) + fixed delay retry infinitely on 500/502/503 errors
- **Symptoms**: User says "retry terus" (keeps retrying), logs show same error repeating every 15-20s
- **Root cause**: MCP relayer servers return 500 Internal Server Error during high load, fixed retry delay hammers failing endpoint
- **Solution**: Implement exponential backoff + bounded retries + smart cooldown
  ```javascript
  // In callToolWithRetry function:
  const backoffDelay = retryDelayMs * Math.pow(2, attempt - 1);
  // 20s → 40s → 80s → 160s → 320s
  ```
- **Config changes**:
  - Set `MAX_RETRIES=5` (not 0) to prevent infinite loops
  - Increase base `RETRY_DELAY_MS=20000` (20s minimum)
  - Add random jitter between successful mints: `sleep $((8 + RANDOM % 5))` (8-12s)
  - Detect server errors and wait longer: if 500/502/503 → sleep 30s, else sleep 20s
- **Shell script pattern** (auto-mine loop):
  ```bash
  if echo "$error" | grep -qE "(500|502|503)"; then
      echo "Server error, waiting 30s..."
      sleep 30
  else
      echo "Retrying in 20s..."
      sleep 20
  fi
  ```
- **Why exponential backoff**: Gives overloaded MCP server time to recover, reduces spam
- **Why random jitter**: Prevents thundering herd when multiple scripts restart simultaneously
- **User frustration signal**: "retry terus" = immediate action needed, not just "wait it out"

### Duplicate Process Prevention (CRITICAL)
- **Problem**: Multiple instances of auto-mine script running simultaneously, causing race conditions and incorrect slot counting
- **Symptoms**: Logs show duplicate "🚀 ROT Auto Miner Started" headers, multiple "Attempting mint #X" at same timestamp, balance stuck despite "success" messages
- **Root cause**: Background process spawning without lock file allows multiple script instances to run in parallel
- **Impact**: Scripts compete for same slots, some TXs revert due to nonce conflicts, slot counter gets out of sync with reality
- **Solution**: Implement lock file pattern
  ```bash
  #!/bin/bash
  LOCK_FILE="/tmp/rot-miner.lock"
  
  # Check if already running
  if [ -f "$LOCK_FILE" ]; then
      PID=$(cat "$LOCK_FILE")
      if ps -p "$PID" > /dev/null 2>&1; then
          echo "Miner already running (PID: $PID)"
          exit 1
      else
          echo "Stale lock file found, removing..."
          rm -f "$LOCK_FILE"
      fi
  fi
  
  # Create lock file
  echo $$ > "$LOCK_FILE"
  
  # Cleanup on exit
  trap "rm -f $LOCK_FILE" EXIT
  
  # Run miner logic...
  ```
- **Best practice**: Always use lock file for long-running automated miners
- **Verification**: `ps aux | grep -E "(auto-mine|mint-rot)" | grep -v grep` should show only 1 bash + 1 node process
- **User frustration signal**: "ada duplicate runs yang overlap" = immediate lock file needed

### Batch Minting (Parallel Slots)
- **When to use**: User wants faster completion ("batch mint 3 sekaligus biar cepet")
- **Pattern**: Launch N parallel mint processes, wait for all to complete before next batch
- **Shell implementation**:
  ```bash
  BATCH_SIZE=3
  SLOTS_LEFT=$(cast call $TOKEN "mintsOf(address)(uint256)" $WALLET --rpc-url $RPC)
  SLOTS_LEFT=$((10 - SLOTS_LEFT))
  
  for ((i=0; i<SLOTS_LEFT; i+=BATCH_SIZE)); do
    echo "Batch mint #$((i/BATCH_SIZE + 1)): starting $BATCH_SIZE parallel mints"
    for ((j=0; j<BATCH_SIZE && i+j<SLOTS_LEFT; j++)); do
      node mint.js &  # Background process
    done
    wait  # Wait for all parallel mints to finish
    sleep 5
  done
  ```
- **Tradeoffs**:
  - ✅ Faster completion when MCP server is responsive
  - ❌ All N processes fail together if MCP is down (wastes N × retry time)
  - ❌ Higher MCP server load (may trigger rate limits)
- **Best for**: Final push when most slots already minted (e.g., 7/10 → batch 3 remaining)
- **Avoid when**: MCP server already showing timeouts (sequential is more resilient)

### MCP v2 Success Detection Bug (CRITICAL)
- **Problem**: Script checks `grep -q '"tx:'` or `grep -q "tx:"` on raw SSE result — this NEVER matches
- **Root cause**: MCP v2 success response is inside JSON `result.content[0].text`, not at top level
- **Actual success text format**: `"minted 25,500 $ROT to 0x...\ntx: 0x...\nslots used: N\n..."`
- **Symptom**: Mint actually succeeds (on-chain balance increases) but script logs `❌` and keeps retrying
- **Fix**: Parse `text` content first, THEN grep for `"minted 25,500"` OR `"tx:"`:
  ```bash
  text=$(echo "$result" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['result']['content'][0]['text'])" 2>/dev/null)
  if echo "$text" | grep -q "minted 25,500\|tx:"; then
      # SUCCESS
  fi
  ```
- **Wrong pattern** (don't use): `if echo "$result" | grep -q '"tx:'; then`
- **Wrong pattern** (don't use): `if echo "$result" | grep -q "tx:"; then`
- See `templates/mine-v2.sh` for corrected implementation

### Don't Change RPC Mid-Session (CRITICAL)
- **User correction**: "kalo belum kayaknya gara2 anda rubah deh, soalnya akun 1 sebelum diubah bisa delegated dan mint"
- **Problem**: Switching RPC while miner is running can break working setup
- **Why it breaks**:
  - Miner script caches RPC connection at startup
  - Changing `.env` doesn't reload running process
  - New RPC may have different rate limits, endpoints, or state sync
  - Working delegation on old RPC may not be visible on new RPC immediately
- **Correct workflow**:
  1. If miner is working (successfully minting), **leave RPC alone**
  2. Only change RPC if miner is failing AND you've confirmed RPC is the root cause
  3. After changing RPC, **always restart miner process** (kill + relaunch)
  4. Test with one wallet first before applying RPC change to all miners
- **When RPC change is justified**:
  - Delegation tx times out on current RPC (try publicnode.com)
  - Current RPC returns 429 rate limit errors
  - Current RPC is down (DNS error, connection refused)
- **When to leave RPC alone**:
  - Miner successfully minted at least 1 slot on current RPC
  - Only MCP server is timing out (not RPC issue)
  - User says "sebelum diubah bisa" (it worked before you changed it)

### Local Slot Counter Drift (CRITICAL)
- **Problem**: Script tracks `current_slots` as a local variable, incrementing by 1 on each "success"
- **Symptoms**: Script says "Slots: 4/10" but on-chain shows 5/10 — counter drifted because some mints succeeded silently (e.g., before script started, or during a restart)
- **Root cause**: Local counter starts from a hardcoded value or 0, not from on-chain state; also, success detection bug (see above) can cause counter to NOT increment even when mint succeeded
- **Fix**: After each successful mint, re-query on-chain slot count instead of incrementing locally:
  ```bash
  # After success, re-query on-chain
  new_slots=$(get_slots)  # calls check_wallet MCP tool
  [ -n "$new_slots" ] && current_slots=$new_slots || current_slots=$((current_slots + 1))
  ```
- **Also**: Initialize `current_slots` from on-chain at script start, never hardcode:
  ```bash
  current_slots=$(get_slots)
  [ -z "$current_slots" ] && current_slots=0  # fallback only if MCP unreachable
  ```
- **User signal**: "akun 2 yang masuk baru 127500 rot" when script claims more = counter drift

### Per-Wallet Slot Cap Lockout (CRITICAL)
- **Problem**: Wallet reaches slot cap in MCP server's accounting even when on-chain slots are fewer
- **Symptoms**: Error `0x... has 0 slot(s) remaining in per-wallet cap, asked for 1` but on-chain shows fewer slots used
- **Root cause**: MCP relayer counts submitted TXs toward cap, even if TXs revert on-chain
- **Impact**: Wallet becomes "locked" - can't mint more slots even though on-chain slots < 10
- **Example**: Wallet shows `slots used: 9` on-chain, but MCP says `0 slot(s) remaining` → wallet is soft-locked
- **Solution**: Generate new wallet → delegate → mint remaining slots
- **Prevention**: After each mint, verify on-chain state matches MCP's slot count before continuing
- **Recovery workflow**:
  1. Check on-chain slots: `cast call $TOKEN "mintsOf(address)(uint256)" $WALLET`
  2. If on-chain slots < 10 but MCP says 0 remaining → wallet is locked
  3. Generate new wallet: `node -e "const { privateKeyToAccount } = require('viem/accounts'); const crypto = require('crypto'); const pk = '0x' + crypto.randomBytes(32).toString('hex'); const acc = privateKeyToAccount(pk); console.log('Address:', acc.address); console.log('Private Key:', pk);"`
  4. Fund new wallet with 0.0025 ETH
  5. Delegate new wallet
  6. Mint remaining slots on new wallet
- **User signal**: "error: 0x... has 0 slot(s) remaining in per-wallet cap" when balance shows fewer slots on-chain

### Relayer Limitations
- Relayers have **gas price caps** (e.g., 4.21 gwei) — won't send if base fee exceeds cap
- Relayers have **queue limits** (e.g., 50 in-flight txs) — retry when full
- Gas cap is a **hard server-side limit** — cannot be overridden by user or Claude
- Claude's MCP tool (`Ca:token_mint`) returns error when gas exceeds cap
- "raise RELAYER_MAX_FEE_GWEI" error = server config, not user-configurable
- Queue "50/50" may be application-level (no pending txs on-chain) — backend rate limit
- Gas is cheapest UTC 00:00-06:00 (WIB 07:00-13:00) and weekends
- Best strategy: set cronjob gas monitor + have Claude auto-retry continuously
- During peak (CT China rush), both queue AND gas spike simultaneously

### Twitter Due Diligence Tool
- `twitter` CLI (pip, cookie-based with TWITTER_AUTH_TOKEN + TWITTER_CT0) works when `xurl` has no auth configured
- Use `twitter search "<domain>" --json` to check who's sharing the project
- Check follower counts with `twitter user "<handle>" --json` → `.data.followers`
- Mid-tier KOLs (3K-16K followers) sharing with "DYOR" = typical for legit experimental mints

### Node.js Top-Level Await in `node -e` (CRITICAL)
- **Problem**: `node -e "const x = await fetch(...)"` throws `SyntaxError: await is only valid in async functions`
- **Root cause**: `node -e` runs in CommonJS mode by default, which doesn't support top-level await
- **Solution A**: Use `--input-type=module` flag:
  ```bash
  echo "const r = await fetch('...');" | node --input-type=module
  ```
- **Solution B**: Write to a `.mjs` file and run it from the correct directory (where `node_modules` exists):
  ```bash
  cat > /tmp/check.mjs << 'EOF'
  const r = await fetch('...');
  EOF
  cd ~/rot-minter-new && node /tmp/check.mjs
  ```
- **Solution C**: Wrap in async IIFE for `node -e`:
  ```bash
  node -e "(async () => { const r = await fetch('...'); console.log(await r.text()); })()"
  ```
- **For viem imports**: Must run from directory with `node_modules/viem` installed:
  ```bash
  cd ~/rot-minter-new && node -e "const { privateKeyToAccount } = require('viem/accounts'); ..."
  ```
- **Wallet generation** (confirmed working pattern):
  ```bash
  cd ~/rot-minter-new && node -e "const { privateKeyToAccount } = require('viem/accounts'); const crypto = require('crypto'); const pk = '0x' + crypto.randomBytes(32).toString('hex'); const acc = privateKeyToAccount(pk); console.log('Address:', acc.address); console.log('Private Key:', pk);"
  ```

### NEVER Generate Fake Wallet Addresses (CRITICAL — ETH LOSS RISK)
- **NEVER write a random hex string and claim it's a wallet address**
- **NEVER provide a made-up private key** — it will not correspond to the address
- This caused real ETH loss (0.011 ETH) when user sent funds to a fake address with no valid PK
- **ALWAYS generate wallets with proper cryptographic tools**:
  ```bash
  # Option 1: Python eth_account (most reliable on this VPS)
  python3 -c "from eth_account import Account; a = Account.create(); print('Address:', a.address); print('PK:', a.key.hex())"
  
  # Option 2: Node.js viem (from rot-minter-new directory)
  cd ~/rot-minter-new && node -e "const { privateKeyToAccount } = require('viem/accounts'); const crypto = require('crypto'); const pk = '0x' + crypto.randomBytes(32).toString('hex'); const acc = privateKeyToAccount(pk); console.log('Address:', acc.address); console.log('PK:', pk);"
  
  # Option 3: cast wallet new (if foundry available)
  cast wallet new
  ```
- **Verify**: After generating, derive address from PK and confirm they match before sharing
- **`cast` is NOT available on this VPS** (May 2026) — use python3 or node instead
- If you're unsure whether a tool is available, test it first before claiming success

### Stopping One Miner Kills All (CRITICAL)
- **Problem**: `pkill -f "rot-minter-new"` or `pkill -f "mine-v2.sh"` kills ALL miner processes, not just one account
- **Symptoms**: User asks to stop account 1 only, but accounts 2 and 3 also die
- **Root cause**: `pkill -f` matches any process with that string in command line — all miners share the same script name
- **Fix**: Use process session IDs (from `proc_xxx` handles) to kill specific miners:
  ```bash
  # WRONG — kills all miners
  pkill -f "mine-v2.sh"
  pkill -f "rot-minter-new"
  
  # RIGHT — kill specific process by session ID
  # Use process tool: action=kill, session_id=proc_xxxxx
  # Or by PID if known:
  kill <specific_pid>
  ```
- **Best practice**: Track each miner's session_id separately. When user says "stop akun 1", kill only that session_id
- **Recovery**: If all miners accidentally killed, restart accounts 2 and 3 immediately

### ETH Top-Up Requires Miner Restart
- **Problem**: Miner running in background doesn't detect new ETH after top-up
- **Symptoms**: Error keeps showing old balance (e.g., `has 0.000335 ETH, needs 0.001 ETH`) even after user sends more ETH
- **Root cause**: Script reads ETH balance at each attempt via MCP `check_wallet`, but the relayer caches or the script process has stale state
- **Fix**: Kill miner process and restart after top-up is confirmed on-chain
  ```bash
  # Kill old miner
  pkill -f "mine-v2.sh"
  # Verify ETH arrived
  curl -s -X POST https://www.brainrot.dog/api/mcp \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_wallet","arguments":{"address":"0x..."}},"id":1}' \
    | grep '^data:' | sed 's/^data: //'
  # Restart miner
  cd ~/rot-minter-account2 && bash mine-v2.sh &
  ```
- **User signal**: "sudah saya isi" (already topped up) but miner still shows old balance error

### Importing User-Provided Private Key
- **When user provides a PK directly**, always derive the address first before doing anything
- **Never assume** the address — derive it cryptographically:
  ```bash
  python3 -c "
  from eth_account import Account
  pk = '0x<user_provided_pk>'
  acct = Account.from_key(pk)
  print('Address:', acct.address)
  "
  ```
- Then check wallet status on-chain before proceeding with delegation/mining
- This prevents working on wrong address or duplicate work if wallet already delegated

### Setup New Account from User-Provided PK (Full Workflow)
- **Pattern**: User sends PK → derive address → check_wallet → delegate if needed → setup folder → start miner
  ```bash
  # 1. Derive address
  python3 -c "from eth_account import Account; a = Account.from_key('0x<PK>'); print(a.address)"
  
  # 2. Check wallet status (delegation, ETH, slots)
  curl -s -X POST https://www.brainrot.dog/api/mcp \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_wallet","arguments":{"address":"0x..."}},"id":1}' \
    | grep '^data:' | sed 's/^data: //'
  
  # 3. Setup folder (copy from existing account)
  mkdir -p ~/rot-minter-accountN
  cp ~/rot-minter-account2/mine-v2.sh ~/rot-minter-accountN/
  cp ~/rot-minter-account2/delegate-votes.mjs ~/rot-minter-accountN/
  cp -r ~/rot-minter-new/node_modules ~/rot-minter-accountN/
  cp ~/rot-minter-new/package.json ~/rot-minter-accountN/
  
  # 4. Create .env
  cat > ~/rot-minter-accountN/.env << EOF
  PRIVATE_KEY=0x<PK>
  MINT_ADDRESS=0x<ADDRESS>
  RPC_URL=https://ethereum-rpc.publicnode.com
  MCP_URL=https://www.brainrot.dog/api/mcp
  EOF
  
  # 5. Update ADDRESS in mine-v2.sh
  sed -i 's/ADDRESS="0x.*/ADDRESS="0x<ADDRESS>"/' ~/rot-minter-accountN/mine-v2.sh
  
  # 6. Delegate if not already delegated
  cd ~/rot-minter-accountN && node delegate-votes.mjs
  
  # 7. Start miner
  cd ~/rot-minter-accountN && bash mine-v2.sh &
  ```
- **Key check**: If `delegated: true` already, skip step 6
- **ETH requirement**: ~0.001 ETH per slot × 10 slots = ~0.01 ETH minimum

### Free RPC Rate Limits
- `https://eth.llamarpc.com` — rate limits quickly
- `https://ethereum-rpc.publicnode.com` — more reliable for reads
- `https://1rpc.io/eth` — backup

### RPC Selection for MCP Minting (CRITICAL)
- **RPC publik (ethereum-rpc.publicnode.com) PALING CEPAT untuk mint** melalui MCP
- **Ankr premium LAMBAT/STUCK untuk MCP calls** — bagus untuk delegation tapi jelek untuk mint
- **User correction (May 2026)**: "RPC publik paling cepat" vs "Ankr stuck untuk MCP"
- **Pola**: Delegation bisa pakai RPC mana saja (Ankr premium OK), tapi mint via MCP lebih cepat dengan RPC publik
- **Alasan**: MCP server mungkin punya rate limit atau preferensi untuk request dari RPC tertentu
- **Workflow**:
  1. Delegation: Bisa pakai RPC mana saja (Ankr premium OK)
  2. Mint via MCP: Pakai RPC publik (publicnode.com)
  3. Jika mint stuck setelah ganti RPC → kembalikan ke RPC yang sebelumnya berhasil

## Gas Monitoring Script

```bash
#!/bin/bash
export PATH="$HOME/.foundry/bin:$PATH"
RPC="https://ethereum-rpc.publicnode.com"
TARGET_GWEI=4.21

while true; do
  BASE_FEE=$(cast base-fee --rpc-url $RPC 2>/dev/null)
  GWEI=$(python3 -c "print(f'{int(${BASE_FEE:-0}) / 1e9:.2f}')")
  if python3 -c "exit(0 if float('$GWEI') < $TARGET_GWEI else 1)"; then
    echo "GAS LOW: ${GWEI} gwei < ${TARGET_GWEI} — MINT NOW!"
    # Send notification
    break
  fi
  echo "$(date): ${GWEI} gwei (waiting for < ${TARGET_GWEI})"
  sleep 60
done
```

## Twitter/X Due Diligence

Before minting, check project legitimacy:
```bash
twitter search "<project_domain>" --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
for t in data.get('data', []):
    a = t.get('author', {})
    print(f'@{a.get(\"screenName\")} ({a.get(\"followers\",\"?\")} followers): {t.get(\"text\",\"\")[:100]}')
"
```

Look for: mid-tier KOLs sharing (not just bots), verified accounts, "DYOR" disclaimers (normal for new projects).

## Multi-Wallet Farming

To maximize mints across multiple wallets:

### 0. Use Single-Instance Miner Template
- See `templates/mine-single.sh` for production-ready miner with lock file + on-chain verification
- See `templates/mine-single-simple.sh` for simplified version (lock file + smart cooldown, no on-chain verification)
- Prevents duplicate processes and catches reverted TXs
- Adjust `MAX_SLOTS`, token address, and balance calculation for your project

### 1. Generate wallets in batch
```python
from eth_account import Account
wallets = [Account.create() for _ in range(10)]
for i, w in enumerate(wallets, 1):
    print(f"#{i} {w.address} PK:{w.key.hex()}")
```

### 2. Fund each wallet
- **0.013 ETH per wallet** (0.00111 × 10 mints + ~0.002 for delegation gas)
- Delegation tx costs ~36K gas (~$1.20 at 5 gwei)

### 3. Delegate all wallets
```bash
for PK in $PK1 $PK2 ... $PK10; do
  WALLET=$(cast wallet address --private-key $PK)
  cast send $WALLET --private-key $PK --rpc-url $RPC --auth $MINT_DELEGATE --value 0 --gas-limit 100000
  sleep 2
done
```

### 4. User mints manually on Claude.ai
- Same Claude account works for all wallets (connector is account-level, not wallet-level)
- Each wallet needs separate OAuth/SIWE flow (switch wallet in MetaMask/browser extension)
- Mint command: "mint me 9 slots" (leave 1 slot margin for ETH dust)
- 9 slots × 0.00111 = 0.00999 ETH, leaves ~0.001 ETH dust

### Budget Example (10 wallets × 10 slots)
- Total ETH needed: ~0.13 ETH (~$298 at $2289/ETH)
- Total $SHIT minted: 1,000,000,000 (1B)
- Actual yield per wallet: 9 slots (90M $SHIT) due to ETH dust

## References

- See `references/dogeshit-meme.md` for the first documented instance of this pattern
- See `references/brainrot-dog-rot-minter.md` for brainrot.dog $ROT minting session (May 2026): complete troubleshooting path including RPC selection (publicnode.com vs drpc.live), web UI delegation false negatives, MCP SSE parsing, delegated EOA transfer restrictions, MCP server timeout diagnosis, and multi-wallet farming workflow with user-corrected "test first wallet" approach
- See `references/mcp-retry-patterns.md` for exponential backoff + bounded retry implementation (fixes infinite retry loops on 500/502/503 errors)
- See `references/duplicate-process-prevention.md` for lock file pattern + on-chain verification after "success" (prevents duplicate script instances and catches reverted TXs that relayer reports as successful)
- See `references/rot-minter-account1-completion.md` for production debugging session (May 10, 2026): fixing infinite retry loops, duplicate process spawning, and TX revert detection — complete path from "retry terus" to 10/10 slots with exponential backoff + lock files
- See `references/rot-wallet-cap-lockout.md` for wallet cap lockout issue (May 10, 2026): MCP counts reverted TXs toward slot cap, locking wallet even when on-chain slots < 10 — includes complete debugging path and new wallet generation workflow
- See `references/brainrot-dog-api-v2.md` for brainrot.dog MCP API v2 tool list, response formats, and working curl patterns (May 2026 — tools renamed, batch_mint and check_mint_status added)
- See `templates/mine-v2.sh` for bash miner using new MCP API v2 (no npm/ethers dependency, pure curl + python3 JSON parsing)
- See `references/rot-multi-account-may10-2026.md` for 4-account mining session (May 10, 2026): fake wallet ETH loss incident, process management pitfalls (pkill kills all miners), ETH top-up restart requirement, RPC performance comparison (publicnode fastest for MCP), and complete multi-account folder setup workflow
