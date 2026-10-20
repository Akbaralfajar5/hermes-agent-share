# rpow2 Mining Post-Mortem (May 2026)

## Project Summary
- **Duration:** April-May 2026
- **Outcome:** Discontinued (not profitable)
- **Reason:** API instability + reward nerf (99.84% reduction)

## Technical Setup
- **Miners tested:**
  - rizkypujir/miner (Rust) - best performance
  - Custom Python miner - easy deployment
  - stablemarkk/rpow_cli_miner (Node.js) - final attempt
- **Deployment:** VPS Hermes (2 cores), zo.computer instances (3 cores each)
- **Automation:** Hermes cronjob watchdog (5-min checks, auto-restart)

## Performance Data
- **Pre-nerf:** Unknown (user joined post-nerf)
- **Post-nerf:** 0.000015 rpow2 per block (~0.13-0.22 rpow2/day per 2-core VPS)
- **Speed:** 0.5-3s per block (CPU-dependent)
- **API reliability:** Poor (frequent 503, 401, 404 errors)

## Economics
- **Reward nerf:** 0.009689 → 0.000015 rpow2/block (643x reduction)
- **Break-even:** $7.51/rpow2 at $101/month VPS cost
- **Market price:** Unknown (not listed yet)
- **Verdict:** Not profitable unless token lists at $7.51+

## Lessons Learned
1. **API stability critical:** rpow2 API had frequent downtime (503 errors), making mining unreliable
2. **Cookie authentication fragile:** Session tokens expired frequently, requiring manual refresh
3. **Reward nerfs kill profitability:** Post-nerf mining became speculative (accumulate and hope for listing)
4. **Multi-VPS strategy:** Using same cookie across multiple VPS worked (no device limits detected)
5. **Cronjob watchdog issues:** Hermes cronjob deletion had race conditions, required nuclear cleanup

## Why User Stopped
- API down for extended periods (May 9-10, 2026)
- Reward too low to justify VPS costs
- Moved to Pearl Network mining research (higher reward: $980/block)

## Code Artifacts
- **Rust miner:** https://github.com/rizkypujir/miner
- **Node.js miner:** https://github.com/stablemarkk/rpow_cli_miner

## Cookie Format
```
rpow_session=eyJlbWFpbCI6ImFrYmFyYWxwYWphcjVAZ21haWwuY29tIiwiZXhwIjoxNzgwODQzNjU4fQ.GShkyCeG_9TMhkFL5uLua5iPDmWm_xlWNhTpup3trtU
```
(Account: you@example.com, Balance: 171 rpow2 at shutdown)
