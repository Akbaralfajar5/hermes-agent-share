# Scan Session: June 16, 2026 (Dead Market)

## Context
- Time: ~04:30 WIB (dead zone per skill)
- Signal Type 1 (gainer): 7 pump.fun tokens
- Signal Type 3 (volume spike): 24 pump.fun tokens
- After dedup: 30 unique
- After MC/holders filter: 20
- After social filter: 20 (all had website or X link — weak social but passing)
- After bundler/bot/serial-deployer hard stops: 8
- After RugCheck cross-verify: **0** (all failed Top1 > 50%)

## Key Observation
**100% whale trap rate** — every token that passed GMGN filters failed RugCheck.
This is consistent with dead market hours. Prime hours likely have better ratio.

## RugCheck Top1 Results (all failing)
| Token | GMGN T10 | RugCheck Top1 | RugCheck Top5 | Score |
|-------|----------|---------------|---------------|-------|
| Fatou | 0.8% | 99.1% | 118.9% | 1 |
| BELLE | 0.3% | 99.7% | 111.3% | 1 |
| GOBMINING | 7.6% | 91.3% | 103.8% | 1 |
| Delic | 2.8% | 96.0% | 133.6% | 1506 |
| ROI | 0.6% | 99.4% | 122.2% | 1 |
| prysmatic | 21.8% | 65.6% | 79.3% | 1 |
| Niger | 0.8% | 99.2% | 130.2% | 1 |
| QR | 6.6% | 91.9% | 119.0% | 1475 |

Note: RugCheck Top5 > 100% is possible because it includes LP pool + bonding curve holders.

## Hard Stop Stats (pre-RugCheck)
- Bundler > 25%: 3 tokens (LOOP 45.7%, Elgatito 37.0%, LOOP had bot 58.6% too)
- Bot > 50% w/o SM: 7 tokens (Cuben, LOOP, Elgatito, Solana, dudegeorgeson, TENNIS, One)
- Serial deployer: 5 tokens (Sprouts, Cuben, Memes, TRILLIONAIRE, STARTPUP)

## Lesson
In dead market, RugCheck is the PRIMARY bottleneck. Consider:
1. Run RugCheck on first 2-3 candidates
2. If all fail with Top1 > 90%, abort scan early
3. Save GMGN API quota for prime hours
