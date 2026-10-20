# zo.computer Web Terminal Setup Notes

Session: May 9, 2026 — Setup rpow2 mining on zo.computer cloud workspace via web terminal.

## Platform Details

**zo.computer** is a cloud workspace platform with:
- Web-based terminal (no direct SSH)
- Debian 12 (Bookworm) base
- Dynamic resource allocation (specs change based on workload)
- Promo code: `CLAWCONMIA` for $100 free credit


- **CPU:** 5 cores total, 3 cores online (0-2), x86_64, model name "unknown"
- **RAM:** 4.0 GB (2.9 GB free)
- **OS:** Debian GNU/Linux 12 (Bookworm)
- **Swap:** 0 GB (no swap configured)
- **Uptime:** Fresh instance (2 minutes at check time)

**Performance estimate:** ~0.5-2.5s per block (vs 0.06-3.31s on 2-core VPS Hermes)

## Web Terminal Workflow

User must paste commands into web terminal one-by-one. Cannot use SSH automation.

### Critical Differences from SSH Setup

1. **No remote script upload** — must create scripts inline with `cat > file << 'EOF'`
2. **No scp/rsync** — credentials must be pasted directly into terminal
3. **Screen session behavior** — web terminal disconnect doesn't kill screen, but reconnect may show stale state
4. **Sudo may prompt** — first `sudo` command may ask for password (web terminal shows prompt)

### Setup Sequence

See main skill for full command sequence. Key points:

- **Step 6-9:** Each `cat > script.sh << 'EOF' ... EOF` block must be pasted as single unit
- **Step 10:** Cookie must be added BEFORE starting mining (no way to hot-reload)
- **Step 11:** `./start.sh` creates detached screen session — user won't see mining output immediately

### Common Failure: Stuck on "Attaching to start.sh"

**Symptom:** After running `./start.sh`, terminal shows:
```
Starting rpow2 mining in background...
Attaching to start.sh
```
And hangs indefinitely.

**Root cause:** Screen session created but didn't properly detach. Terminal is trying to attach to the session instead of returning to prompt.

**Fix:**
```bash
# Press Ctrl+C to cancel stuck attach
screen -S rpow2 -X quit  # Kill the stuck session
pkill -f rpow2-miner     # Kill any orphaned miner processes
./start.sh               # Restart (should work now)
```

**Prevention:** Ensure `start.sh` uses `screen -dmS` (detached mode) not `screen -S` (attached mode).

### Verification After Setup

```bash
# Check screen session exists
screen -list | grep rpow2

# Check miner process running
ps aux | grep rpow2-miner

# Check logs for mining activity
tail -20 mining.log | grep -E "Found nonce|Minted"

# Check CPU usage (should be ~100% per thread)
top -bn1 | grep rpow2-miner
```

Expected output:
- Screen session: `650205.rpow2 (Detached)`
- Process: `rpow2-miner --threads 3`
- Logs: Regular "Found nonce: X in Y.YYs" and "Minted! Session: N" messages
- CPU: ~300% (3 threads × 100%)

## Performance Expectations

**zo.computer 3-core instance:**
- Mining speed: 0.5-2.5s per block (average ~1.5s)
- Blocks per minute: ~8-12 blocks
- Earnings per day: ~0.17-0.26 rpow2 (at post-nerf reward rate of 0.000015258 rpow2/block)
- Earnings per month: ~5-8 rpow2

**Comparison to VPS Hermes (2-core AMD EPYC):**
- zo.computer is ~20-30% faster due to extra core
- Both are "free" (zo.computer uses promo credit, VPS Hermes is existing infrastructure)

## Promo Code Setup

To get $100 free credit:

1. Sign up at https://zo.computer with temp email
2. Navigate to Billing section
3. Enter promo code: `CLAWCONMIA`
4. Credit applied immediately

**Note:** Browser automation (Browserbase) blocked by Cloudflare on temp mail sites. User must sign up manually.

## Multi-Account Strategy

User has 2 rpow2 accounts:
- **Account 1:** you@example.com (171 rpow2 balance)
- **Account 2:** f7qds81lfc@wshu.net (33 rpow2 balance)

**Decision:** Mine Account 1 on zo.computer (higher balance, main account).

**Alternative:** Could run both accounts on separate zo.computer instances (each with CLAWCONMIA promo) for 2x earnings, but requires 2 signups.

## Troubleshooting

### Mining won't start after cookie added

**Symptom:** Added `accounts.txt` but miner still fails with "Cannot read accounts.txt"

**Cause:** Miner was already running when cookie was added. Miner reads `accounts.txt` at startup only.

**Fix:**
```bash
./stop.sh
./start.sh  # Miner will now read the cookie
```

### Screen session shows "Attaching" instead of "Detached"

**Symptom:** `screen -list` shows session in "Attaching" state

**Cause:** Previous terminal tried to attach but disconnected mid-attach

**Fix:**
```bash
screen -d rpow2  # Force detach
screen -list     # Should now show "Detached"
```

### Web terminal disconnected, mining status unknown

**Symptom:** Browser closed or network interrupted

**Recovery:**
1. Reopen zo.computer web terminal
2. Run: `cd ~/rpow2-mining && ./status.sh`
3. If mining still running, logs will show recent activity
4. If stopped, restart: `./start.sh`

**Note:** Screen sessions persist across web terminal disconnects. Mining continues in background.

## Cost Analysis

**zo.computer with CLAWCONMIA promo:**
- $100 free credit
- Instance cost: ~$0.10-0.20/hour (estimate based on 3-core allocation)
- Runtime: 500-1000 hours (~20-40 days)
- Earnings in 30 days: ~6 rpow2
- **Effective cost:** $0 (using promo credit)

**Break-even:** If rpow2 lists at $16.67/token, 6 tokens = $100 (break-even with promo credit used).

**Comparison to QuickPod Threadripper PRO 7985WX:**
- QuickPod: $101/month, 13.44 rpow2/month, break-even at $7.51/token
- zo.computer: $0/month (promo), 6 rpow2/month, pure profit if token has any value

**Recommendation:** Use zo.computer promo credit for mining. Zero marginal cost, accumulate tokens while waiting for listing.
