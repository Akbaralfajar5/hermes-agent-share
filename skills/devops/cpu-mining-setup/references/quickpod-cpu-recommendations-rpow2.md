# Quickpod CPU Recommendations for RPOW2 Mining (May 2026)

**Context:** RPOW2 is CPU mining (SHA-256 proof-of-work), not GPU mining. Optimal hardware is high-core-count CPUs.

## Top Picks from Quickpod

### 1. AMD Ryzen Threadripper PRO 7985WX (64-Core) — BEST
- **32 threads** @ **$0.74/hr**
- 96 GB RAM
- Location: Sofia-Capital, Bulgaria
- 96.67% reliability
- **ROI:** ~43 threads per dollar/hr

**Estimated performance:**
- Hashrate: ~28M H/s (32 cores × ~875K H/s per core)
- Solve time: ~1.2 seconds (difficulty 25 bits, 33M nonce search space)
- Solves per hour: ~3000
- RPOW earned: ~30 RPOW/hr (0.01 RPOW per solve)
- **Profit:** ~$29/hr (if RPOW = $1)

### 2. AMD Ryzen Threadripper PRO 5995WX (64-Core) — GOOD
- **32 threads** @ **$0.72/hr**
- 96 GB RAM
- Location: Sofia-Capital, Bulgaria
- 93-96% reliability
- Slightly cheaper, similar performance to 7985WX

**Estimated performance:**
- Hashrate: ~26M H/s (slightly slower than 7985WX)
- Solve time: ~1.3 seconds
- RPOW earned: ~28 RPOW/hr
- **Profit:** ~$27/hr (if RPOW = $1)

### 3. AMD Ryzen Threadripper PRO 5995WX (20 threads) — BUDGET
- **20 threads** @ **$0.45/hr**
- 40 GB RAM
- Location: Sofia-Capital, Bulgaria
- 96.67% reliability
- **Best value:** 44 threads per dollar/hr

**Estimated performance:**
- Hashrate: ~17.5M H/s
- Solve time: ~1.9 seconds
- RPOW earned: ~18 RPOW/hr
- **Profit:** ~$17.5/hr (if RPOW = $1)

## Performance Comparison

| Hardware | Cores | Hashrate | Solve Time | RPOW/hr | Cost/hr | Profit/hr |
|----------|-------|----------|------------|---------|---------|-----------|
| VPS (2 cores) | 2 | 1.8M H/s | 30s | 1.2 | ~$0.01 | ~$1.19 |
| PC (12 cores) | 12 | 5-10M H/s | 5-10s | 7.2 | $0 | ~$7.20 |
| Threadripper 20c | 20 | 17.5M H/s | 1.9s | 18 | $0.45 | ~$17.55 |
| Threadripper 32c | 32 | 28M H/s | 1.2s | 30 | $0.72 | ~$29.28 |

**Assumptions:**
- Difficulty: 25 bits (current as of May 2026)
- Search space: ~33M nonces
- RPOW value: $1 (adjust based on actual market price)
- No API rate limits or cooldowns

## ROI Analysis

**Break-even scenarios:**

| RPOW Price | Threadripper 32c Profit/hr | Threadripper 20c Profit/hr |
|------------|---------------------------|---------------------------|
| $0.10 | $3.00 - $0.72 = **$2.28** | $1.80 - $0.45 = **$1.35** |
| $0.50 | $15.00 - $0.72 = **$14.28** | $9.00 - $0.45 = **$8.55** |
| $1.00 | $30.00 - $0.72 = **$29.28** | $18.00 - $0.45 = **$17.55** |
| $2.00 | $60.00 - $0.72 = **$59.28** | $36.00 - $0.45 = **$35.55** |

**Minimum RPOW price for profitability:**
- Threadripper 32c: $0.024 per RPOW (break-even at $0.72/hr ÷ 30 RPOW/hr)
- Threadripper 20c: $0.025 per RPOW (break-even at $0.45/hr ÷ 18 RPOW/hr)

**Conclusion:** Extremely profitable if RPOW has any market value. Even at $0.10 per RPOW, ROI is 300-400%.

## Deployment Strategy

**Recommended approach:**

1. **Start with 20-thread instance** ($0.45/hr) to test:
   - Verify mining works on Quickpod
   - Confirm actual hashrate matches estimates
   - Check for API rate limits or cooldowns
   - Run for 1-2 hours to measure real RPOW/hr

2. **Scale up if profitable:**
   - Deploy multiple 32-thread instances if no rate limits
   - Or use 32-thread instance for single-account mining

3. **Monitor daily quota:**
   - RPOW has daily mint cap: 1000 RPOW per account
   - At 30 RPOW/hr, cap reached in ~33 hours
   - May need multiple accounts or rotate instances

## Pitfalls

- **API rate limits:** RPOW2 API may throttle high-frequency requests. Monitor for 429 errors.
- **Daily mint cap:** 1000 RPOW per account per day. Exceeding this wastes compute.
- **Cookie expiration:** JWT tokens expire ~30 days. Update before expiration.
- **Difficulty changes:** If difficulty increases, solve time increases proportionally.
- **RPOW market value:** Profitability depends on actual RPOW price. Verify before scaling.
- **Quickpod reliability:** 93-96% uptime means ~1-2 hours downtime per day. Factor into ROI.

## Alternative: GPU Mining

**Note:** RPOW2 is CPU mining (SHA-256), not GPU mining. GPUs are not suitable for this workload.

If looking for GPU mining opportunities, RPOW2 is not the right project. Consider:
- Ethereum (ETH) — GPU mining via ethash
- Ravencoin (RVN) — GPU mining via kawpow
- Ergo (ERG) — GPU mining via autolykos

For RPOW2, stick with high-core-count CPUs (Threadripper, EPYC, Xeon).

## See Also

- `references/rpow2-python-miner-v2-may-2026.md` — Python miner deployment guide
- `references/rpow2-economics.md` — Reward analysis and ROI calculations
- `references/vps-comparison-may-2026.md` — VPS provider comparison for CPU mining
