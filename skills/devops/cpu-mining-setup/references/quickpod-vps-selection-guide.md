# Quickpod VPS Selection Guide for CPU Mining

**TL;DR:** Always choose **32X Threadripper**, never 1X or 6X.

## The 1X/6X Trap

Quickpod lists VPS by thread count: 1X, 2X, 4X, 6X, 8X+, 20X, 32X.

**Common mistake:** Choosing 1X or 6X because they're cheaper.

**Why it's wrong:** CPU mining is embarrassingly parallel — performance scales linearly with threads, but cost doesn't.

## Performance vs Cost

| Spec | Threads | Hashrate | Solve Time | RPOW/hr | Cost/hr | RPOW per $ |
|------|---------|----------|------------|---------|---------|------------|
| **1X Threadripper** | 1 | 0.9M H/s | 37s | ~97 | $0.026 | 3,730 |
| **6X Threadripper** | 6 | 10M H/s | 3s | ~1,200 | $0.14 | 8,571 |
| **20X Threadripper** | 20 | 34M H/s | 1s | ~3,000 | $0.45 | 6,667 |
| **32X Threadripper** | 32 | 55M H/s | <1s | ~3,600 | $0.74 | 4,864 |

### Why 6X Looks Better (But Isn't)

**Naive calculation:** 6X has best RPOW per dollar (8,571 vs 4,864).

**Reality:** This ignores:

1. **API cooldown** — rpow2 enforces 2-5s between challenges
   - 32X: <1s solve + 3s cooldown = 4s cycle → 900 tokens/hr
   - 6X: 3s solve + 3s cooldown = 6s cycle → 600 tokens/hr
   - 1X: 37s solve + 3s cooldown = 40s cycle → 90 tokens/hr

2. **Challenge expiry** — 5 min timeout
   - 32X: Solves 300+ challenges before expiry
   - 6X: Solves 100 challenges before expiry
   - 1X: Solves 8 challenges before expiry (high waste)

3. **Opportunity cost** — Time is money
   - 32X mines 3x more in same rental period
   - 6X takes 3x longer to reach same earnings
   - 1X takes 37x longer

### Real-World Adjusted ROI

**With cooldown:**

| Spec | Effective Rate | Cost/hr | Revenue/hr (RPOW=$1) | Profit/hr | ROI |
|------|---------------|---------|---------------------|-----------|-----|
| 1X | 90 tokens/hr | $0.026 | $0.90 | $0.87 | 3,346% |
| 6X | 600 tokens/hr | $0.14 | $6.00 | $5.86 | 4,186% |
| 32X | 900 tokens/hr | $0.74 | $9.00 | $8.26 | 1,116% |

**Wait, 6X still wins?**

No! This assumes:
- Unlimited time (you don't care how long it takes)
- No challenge expiry (all challenges solved)
- No opportunity cost (your time is free)

**In practice:**
- You want to mine **as much as possible in limited time**
- Challenge expiry wastes more cycles on slow miners
- Faster mining = faster compounding = higher total earnings

**Example:** 24-hour rental

| Spec | Tokens Mined | Cost | Revenue (RPOW=$1) | Profit | Effective $/hr |
|------|-------------|------|------------------|--------|----------------|
| 1X | 2,160 | $0.62 | $21.60 | $20.98 | $0.87/hr |
| 6X | 14,400 | $3.36 | $144.00 | $140.64 | $5.86/hr |
| 32X | 21,600 | $17.76 | $216.00 | $198.24 | **$8.26/hr** |

**Conclusion:** 32X earns 1.5x more profit per hour than 6X, despite lower ROI percentage.

## Decision Framework

### Choose 32X Threadripper When:
- ✅ You want maximum earnings per hour
- ✅ You're mining for limited time (hours/days)
- ✅ RPOW has market value (>$0.10)
- ✅ You want to minimize challenge expiry waste
- ✅ You value speed over efficiency

### Choose 20X Threadripper When:
- ✅ Budget constrained but still want good performance
- ✅ 32X not available
- ✅ Testing before committing to 32X

### Choose 6X Threadripper When:
- ⚠️ Extremely budget constrained
- ⚠️ Mining for weeks/months (long-term efficiency matters)
- ⚠️ RPOW value uncertain (<$0.10)

### Never Choose 1X:
- ❌ Too slow (37s per solve)
- ❌ High challenge expiry risk
- ❌ Poor absolute earnings ($0.87/hr)
- ❌ Only makes sense if RPOW = $0.01 (unlikely)

## How to Find 32X on Quickpod

1. Go to https://quickpod.io/pricing
2. Click **"CPU"** tab (not GPU)
3. Look for listings with **"32X"** prefix:
   - **32X AMD Ryzen Threadripper PRO 7985WX 64-Cores**
   - **32X AMD Ryzen Threadripper PRO 5995WX 64-Cores**
4. Check specs:
   - Threads: **32**
   - RAM: **96 GB**
   - Price: **~$0.72-0.74/hr**
5. Click **"Create"**

### Visual Identification

**WRONG (1X):**
```
1X AMD Ryzen Threadripper PRO 7985WX 64-Cores
Threads: 1 | RAM: 3 GB
$0.0260/hr
```

**WRONG (6X):**
```
6X AMD Ryzen Threadripper PRO 7985WX 64-Cores
Threads: 6 | RAM: 18 GB
$0.1410/hr
```

**RIGHT (32X):**
```
32X AMD Ryzen Threadripper PRO 7985WX 64-Cores
Threads: 32 | RAM: 96 GB
$0.7390/hr
```

**Key indicator:** Look for **"Threads: 32"** in the specs, not just the title.

## Common Mistakes

### Mistake 1: Choosing by Price
**Wrong:** "1X is $0.026/hr, 32X is $0.74/hr → 1X is 28x cheaper!"

**Right:** "1X earns $0.87/hr, 32X earns $8.26/hr → 32X is 9.5x more profitable!"

### Mistake 2: Choosing by ROI Percentage
**Wrong:** "6X has 4,186% ROI, 32X has 1,116% ROI → 6X is better!"

**Right:** "6X earns $5.86/hr, 32X earns $8.26/hr → 32X is 41% more profitable!"

### Mistake 3: Ignoring Cooldown
**Wrong:** "6X solves in 3s, 32X solves in 1s → 6X is 'good enough'"

**Right:** "With 3s cooldown, 6X cycle is 6s, 32X cycle is 4s → 32X is 50% faster in practice"

### Mistake 4: Focusing on Efficiency Over Earnings
**Wrong:** "I want the best RPOW per dollar → choose 6X"

**Right:** "I want the most profit per hour → choose 32X"

## Special Cases

### Case 1: Testing/Prototyping
**Use:** 6X or 20X for 1-2 hours to verify setup works

**Why:** Lower risk if something goes wrong

**Then:** Switch to 32X for production mining

### Case 2: Long-Term Mining (Weeks)
**Use:** 6X might make sense if mining for 30+ days

**Why:** Efficiency compounds over time

**But:** Only if RPOW value is stable and you're not in a rush

### Case 3: Multiple Accounts
**Use:** Multiple 32X instances (one per account)

**Why:** Parallel mining across accounts

**Don't:** Split one 32X into multiple accounts (wastes threads)

## Quick Reference

| Goal | Choose | Why |
|------|--------|-----|
| **Max profit/hr** | 32X | Fastest mining |
| **Budget <$1/hr** | 20X | Good balance |
| **Testing** | 6X | Lower risk |
| **Long-term (30+ days)** | 6X or 20X | Efficiency matters |
| **Quick test** | 6X (1-2 hrs) | Cheap validation |

**Default recommendation:** 32X Threadripper PRO 7985WX or 5995WX

## See Also

- `references/quickpod-setup-session-may-2026.md` — Real deployment session with 32X
- `references/vps-mining-benchmarks.md` — Performance data
- `references/rpow2-economics.md` — ROI calculations
