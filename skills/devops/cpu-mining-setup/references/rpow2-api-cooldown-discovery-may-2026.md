# RPOW2 API Cooldown Discovery (May 10, 2026)

## Critical Finding: 5-Second Cooldown Bottleneck

**Discovery:** RPOW2 API enforces a **5-second cooldown** between challenge requests, making high-core-count VPS unprofitable.

## Session Context

User rented **32-core Threadripper PRO 7985WX** ($0.74/hr) expecting massive performance gains. Reality was different.

## Performance Data

### 32 Cores (Threadripper PRO 7985WX)
- **Hashrate:** 108-122 MH/s
- **Solve time:** 0.2 seconds (203ms)
- **Actual throughput:** ~480 tokens/hr = 4.8 RPOW/hr
- **Bottleneck:** API cooldown, not CPU
- **Cost:** $0.74/hr
- **ROI:** ~$4/hr profit (if RPOW = $1)

### 2 Cores (Standard VPS)
- **Hashrate:** 1.7-3.4 MH/s
- **Solve time:** 20-30 seconds
- **Actual throughput:** ~120 tokens/hr = 1.2 RPOW/hr
- **Bottleneck:** CPU (no cooldown hit)
- **Cost:** $0 (existing VPS)
- **ROI:** 100% profit

## The Cooldown Mechanism

After every successful mint/claim:
```
2026-05-10T01:21:51.027Z SUCCESS mint/claim accepted
2026-05-10T01:21:51.156Z WARN request failed, retrying in 556ms 
  method=POST url=https://api.rpow2.com/challenge 
  attempt=1 status=429 code=COOLDOWN 
  error="wait 5s before next challenge"
```

**Pattern:**
1. Solve challenge in 0.2s
2. Submit solution
3. Get 429 COOLDOWN error
4. Wait 5 seconds
5. Retry (exponential backoff: 0.5s, 1s, 2s, 4s)
6. Finally get new challenge after ~5-7 seconds total

## Why This Matters

**Expected performance (no cooldown):**
- 32 cores @ 122 MH/s
- Difficulty 25 bits = ~33M nonces
- Solve time: 0.27 seconds
- **Theoretical:** 13,333 tokens/hr = 133 RPOW/hr

**Actual performance (with cooldown):**
- Solve: 0.2s
- Cooldown: 5s
- **Total:** 5.2s per token
- **Real:** 692 tokens/hr max (60×60/5.2)
- **Observed:** 480 tokens/hr (cooldown + retries)

**Performance loss:** 96.4% (133 → 4.8 RPOW/hr)

## Economic Impact

| Setup | Cores | Hashrate | Solve Time | Cooldown Hit? | Tokens/hr | RPOW/hr | Cost/hr | Profit/hr |
|-------|-------|----------|------------|---------------|-----------|---------|---------|-----------|
| **Threadripper 32X** | 32 | 122 MH/s | 0.2s | ✅ YES | 480 | 4.8 | $0.74 | $4.06 |
| **Standard 2-core** | 2 | 3.4 MH/s | 30s | ❌ NO | 120 | 1.2 | $0 | $1.20 |
| **Optimal 4-core** | 4 | 6.8 MH/s | 5s | ⚠️ EDGE | 692 | 6.9 | $0.10 | $6.80 |

**Key insight:** 4-core VPS is the sweet spot — fast enough to beat cooldown (5s solve time), cheap enough to be profitable.

## Recommendations

### ❌ Don't Use High-Core-Count VPS
- 32 cores: 36x hashrate, only 4x throughput
- Cost doesn't justify performance
- Cooldown negates CPU advantage

### ✅ Use 2-4 Core VPS
- 2 cores: Free/cheap, no cooldown hit
- 4 cores: Optimal (5s solve = cooldown edge)
- 6+ cores: Diminishing returns

### ✅ Multi-VPS Strategy
Instead of 1×32-core ($0.74/hr):
- Run 4×2-core ($0/hr if existing VPS)
- Same total throughput (4×1.2 = 4.8 RPOW/hr)
- Zero marginal cost

## Technical Details

### Cooldown Error Response
```json
{
  "error": "COOLDOWN",
  "message": "wait 5s before next challenge",
  "retry_after": 5
}
```

HTTP Status: **429 Too Many Requests**

### Retry Behavior (Native CLI Miner)
```
Attempt 1: wait 0.5s + jitter
Attempt 2: wait 1.0s + jitter
Attempt 3: wait 2.0s + jitter
Attempt 4: wait 4.0s + jitter
```

Total delay: ~5-7 seconds before new challenge obtained.

### Why Cooldown Exists

**Anti-spam protection:**
- Prevents hardware monopolization
- Fair distribution across miners
- Server load management

**Design intent:** Level the playing field between high-end and low-end hardware.

## Bypass Attempts (Don't Do This)

❌ **Multi-account on same IP:** Still rate-limited per IP
❌ **Proxy rotation:** Violates ToS, risks ban
❌ **Challenge caching:** Challenges expire in 5 minutes
❌ **Parallel requests:** 429 on all requests

**Conclusion:** Cooldown is intentional and cannot be bypassed without violating ToS.

## Lessons Learned

1. **Always test before scaling:** 1-hour test on cheap VPS would have revealed cooldown
2. **API limits > CPU speed:** Bottleneck analysis matters
3. **Cost-benefit analysis:** More cores ≠ more profit
4. **Read the room:** If everyone uses 2-4 cores, there's probably a reason

## Session Outcome

User deleted 32-core Threadripper VPS after 5 minutes, reverted to 2-core VPS on existing infrastructure (Hermes Agent host).

**Final setup:**
- 2 cores @ 3.4 MH/s
- Native CLI miner (stablemarkk/rpow_cli_miner)
- Cost: $0 (existing VPS)
- Performance: 1.2 RPOW/hr
- ROI: 100% profit

## Related

- `references/quickpod-vps-selection-guide.md` — How to avoid the 1X/6X/32X trap
- `references/rpow2-economics.md` — ROI analysis, break-even calculations
- `references/vps-mining-benchmarks.md` — Real-world performance data
