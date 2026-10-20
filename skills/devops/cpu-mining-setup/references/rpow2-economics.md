# rpow2 Mining Economics (May 2026)

## Reward Nerf History

### Pre-Nerf (Before May 2026)
- **Reward:** ~1 rpow2 per 5 minutes
- **Per hour:** 12 rpow2
- **Per day:** 288 rpow2
- **Per month:** 8,640 rpow2

### Post-Nerf (May 2026)
- **Reward per block:** 0.000015258 rpow2
- **Per 5 minutes:** ~0.001555 rpow2 (at 20 blocks/min)
- **Per hour:** 0.01866 rpow2
- **Per day:** 0.448 rpow2
- **Per month:** 13.44 rpow2

### Nerf Impact
- **Reduction:** 99.84% (643x decrease)
- **Reason:** Likely anti-farm mechanism, tokenomics rebalance, or supply inflation control

## Break-Even Analysis

### VPS Cost Scenarios

**QuickPod Threadripper PRO 7985WX:**
- Cost: $101/month
- Earnings: 13.44 rpow2/month
- **Break-even price:** $101 ÷ 13.44 = **$7.51 per rpow2**

**VPS Hermes (Free/Existing):**
- Cost: $0/month (already paying for VPS)
- Earnings: 5.3-6.6 rpow2/month
- **Break-even price:** $0 (pure profit)

**Zo.computer (with $100 promo):**
- Cost: $0 first month (promo credit)
- Earnings: 6-8 rpow2/month
- **Break-even price:** $0 first month, then ~$12-15/month

### ROI at Different Token Prices

| rpow2 Price | Monthly Revenue (13.44 rpow2) | Profit/Loss (vs $101 cost) | ROI |
|-------------|-------------------------------|----------------------------|-----|
| $1          | $13.44                        | -$87.56 ❌                 | -87% |
| $5          | $67.20                        | -$33.80 ❌                 | -33% |
| $7.51       | $101                          | $0 🟰                      | 0% (break-even) |
| $10         | $134.40                       | +$33.40 ✅                 | +33% |
| $20         | $268.80                       | +$167.80 ✅                | +166% |
| $50         | $672                          | +$571 ✅                   | +565% |

## Mining Speed Benchmarks

### By CPU Type (Post-Nerf)

| CPU | Cores | Mining Speed | Blocks/min | rpow2/day | Cost/month |
|-----|-------|--------------|------------|-----------|------------|
| AMD EPYC 7K62 | 2 | 0.06-3.31s | 6-10 | 0.13-0.22 | $0 (existing) |
| Threadripper 5995WX | 6 | 1-3s | 10-20 | 0.22-0.44 | $99 |
| Threadripper 7985WX | 6 | 0.06-0.47s | 20-30 | 0.44-0.66 | $101 |
| Zo.computer (3 cores) | 3 | 0.5-2.5s | 8-12 | 0.17-0.26 | $0-15 |

### Performance Factors

**Clock speed matters most:**
- Threadripper 7985WX (5.1 GHz boost) = 3x faster than Xeon E5-4669 v4 (2.9 GHz boost)
- Single-core performance > core count for rpow2 mining

**Thread allocation:**
- More threads = faster mining (up to CPU core count)
- Diminishing returns beyond physical cores

## Strategy Recommendations

### Scenario 1: Already Have VPS
**Action:** Mine on existing VPS (free)
- ✅ Zero additional cost
- ✅ Pure profit at any token price
- ✅ Accumulate tokens for future listing

### Scenario 2: Rent Dedicated Mining VPS
**Action:** Only if confident in token price > $7.51
- ⚠️ Need $7.51+ token price to break even
- ⚠️ No market price yet (not listed)
- ⚠️ High risk, high reward

### Scenario 3: Use Promo Credits
**Action:** Maximize free credits (zo.computer CLAWCONMIA)
- ✅ $100 free = 6-7 months free mining
- ✅ Zero risk
- ✅ Accumulate ~40-50 rpow2 before paying

### Scenario 4: Multi-VPS Same Account
**Action:** Run same account on 2-3 VPS
- ✅ 2-3x mining speed
- ✅ Consolidated balance
- ⚠️ Possible API rate limiting
- ⚠️ Ban risk if detected as multi-device

## Current Market Status (May 2026)

- **Listing:** Not yet listed on exchanges
- **Market price:** Unknown
- **Liquidity:** None (can't sell yet)
- **Solana wrap:** Not enabled for most accounts

**Implication:** Mining is speculative — accumulate now, sell later when listed.

## Historical Context

**Why the nerf?**
1. Too many miners → supply inflation
2. Prepare for mainnet/listing
3. Anti-farm mechanism
4. Tokenomics rebalance

**Similar patterns:**
- Many testnet tokens nerf rewards before mainnet
- Early miners accumulate more (pre-nerf advantage)
- Post-nerf mining = long-term accumulation play

## Conclusion

**Post-nerf mining is viable if:**
- ✅ Using existing/free VPS (no additional cost)
- ✅ Using promo credits (zo.computer, etc.)
- ✅ Confident token will list at $10+ (3-5x break-even)
- ✅ Long-term accumulation mindset

**Skip mining if:**
- ❌ Renting expensive VPS ($100+/month)
- ❌ Need immediate ROI
- ❌ Token price uncertainty too high
- ❌ Opportunity cost of capital matters
