# MCP Retry Loop Patterns

Session: May 10, 2026 — brainrot.dog $ROT minter infinite retry fix

## Problem

User reported: "bantu spam mint lewat mcp lagi retry terus" (MCP minting script keeps retrying endlessly)

**Symptoms**:
- Script logs show same error repeating every 15-20 seconds
- `error: relayer /relay/mint 500: Internal server error`
- No progress, just infinite retry loop
- `MAX_RETRIES=0` in config (unlimited retries)

**Root cause**: MCP relayer servers return 500/502/503 during high load. Fixed 15s retry delay hammers the failing endpoint without giving it time to recover.

## Solution: Exponential Backoff + Bounded Retries

### 1. Config Changes (.env)

```bash
# Before (infinite retry)
RETRY_DELAY_MS=15000
MAX_RETRIES=0

# After (bounded with backoff)
RETRY_DELAY_MS=20000
MAX_RETRIES=5
```

### 2. Script Changes (mint-rot.mjs)

**Exponential backoff in retry function**:

```javascript
async function callToolWithRetry(name, args, retryDelayMs, maxRetries) {
  let attempt = 0;

  while (true) {
    try {
      return unwrapToolResult(
        await callMcp('tools/call', {
          name,
          arguments: args,
        }),
      );
    } catch (error) {
      if (!shouldRetry(error)) {
        throw error;
      }

      if (maxRetries !== 0 && attempt >= maxRetries) {
        throw error;
      }

      attempt += 1;
      // Exponential backoff: 20s, 40s, 80s, 160s, 320s
      const backoffDelay = retryDelayMs * Math.pow(2, attempt - 1);
      
      if (error instanceof Error && error.message.includes(FETCH_FAILED_ERROR)) {
        console.error('error fetch failed, retrying now');
      } else {
        console.error(
          `${error.message}. Retrying in ${Math.floor(backoffDelay / 1000)}s (attempt ${attempt}${maxRetries === 0 ? '' : `/${maxRetries}`})...`,
        );
      }
      await sleep(backoffDelay);
    }
  }
}
```

**Key change**: `const backoffDelay = retryDelayMs * Math.pow(2, attempt - 1);`

Retry schedule with `RETRY_DELAY_MS=20000`:
- Attempt 1: 20s
- Attempt 2: 40s
- Attempt 3: 80s
- Attempt 4: 160s
- Attempt 5: 320s (5.3 minutes)

### 3. Shell Script Changes (auto-mine.sh)

**Smart cooldown after success**:

```bash
if echo "$output" | grep -q "minted 25,500"; then
    minted_count=$((minted_count + 1))
    tx=$(echo "$output" | grep "tx:" | awk '{print $2}')
    echo "[$timestamp] ✅ SUCCESS! Minted slot #$minted_count | TX: $tx" | tee -a $LOG_FILE
    
    # Extract balance
    balance=$(echo "$output" | grep "ROT balance:" | awk '{print $3}')
    echo "[$timestamp] 💰 Total Balance: $balance ROT" | tee -a $LOG_FILE
    
    # Cooldown 8-12 detik random untuk avoid rate limit
    cooldown=$((8 + RANDOM % 5))
    echo "[$timestamp] ⏸️  Cooldown ${cooldown}s..." | tee -a $LOG_FILE
    sleep $cooldown
```

**Server-error-specific handling**:

```bash
else
    error=$(echo "$output" | grep "error:" | head -1)
    echo "[$timestamp] ❌ Failed: $error" | tee -a $LOG_FILE
    
    # Jika error 500/502/503, tunggu lebih lama
    if echo "$error" | grep -qE "(500|502|503)"; then
        echo "[$timestamp] ⏳ Server error, waiting 30s..." | tee -a $LOG_FILE
        sleep 30
    else
        echo "[$timestamp] ⏳ Retrying in 20s..." | tee -a $LOG_FILE
        sleep 20
    fi
fi
```

## Why This Works

1. **Exponential backoff**: Gives overloaded MCP server time to recover. 5-minute max delay allows server to clear queue.

2. **Bounded retries**: Prevents infinite loops. After 5 attempts (total ~10 minutes), script moves on instead of hammering forever.

3. **Random jitter** (8-12s): Prevents thundering herd when multiple scripts restart simultaneously. Spreads load.

4. **Server-error detection**: 500/502/503 errors get 30s wait (server overload), other errors get 20s (may be transient).

5. **Rate limiting between mints**: Even successful mints wait 8-12s before next attempt. Prevents overwhelming relayer with burst requests.

## Results

After applying fixes:
- Script successfully minted 2 slots in first 5 minutes
- No more infinite retry loops
- Cooldown periods visible in logs: "⏸️ Cooldown 10s..."
- Server errors handled gracefully with longer waits

## When to Use

Apply this pattern when:
- User reports "retry terus" (keeps retrying)
- Logs show same error repeating at fixed intervals
- MCP endpoint returns 500/502/503 errors
- Script has `MAX_RETRIES=0` or very high value
- No exponential backoff in retry logic

## Related Patterns

- See `references/brainrot-dog-rot-minter.md` for full session context
- Gas monitoring + retry: combine with `scripts/gas-monitor.sh` to only retry when gas is low
- Multi-wallet farming: apply same retry logic to batch delegation scripts
