# MC Death Zone Analysis — June 16, 2026

## Data Summary

11 trades analyzed. Entry MC correlated with PnL outcome:

### Entry MC < $5K (DEATH ZONE)
| Token | Entry MC | PnL | Status | Notes |
|-------|----------|-----|--------|-------|
| Athlos | $5,879 | -97.6% | STUCK | 18 holders, no liquidity to exit |
| bagcat | $4,911 | -90.2% | STUCK | 108 holders, MC doubled but still -90% |
| TrenchCity | $5,484 | -90.8% | STUCK | 53 holders, no exit liquidity |
| USAGIRL | $3,656 | -17.4% | SOLD | Lucky exit via SL |

**Pattern:** SL -35% is USELESS in this range. Price dumps >50% in a single candle, slippage is massive, and there may be no buyers. The SL triggers but the order can't execute at the target price.

### Entry MC $5K-$10K (HIGH RISK)
| Token | Entry MC | PnL | Status | Notes |
|-------|----------|-----|--------|-------|
| Coco | $2,728 | +50.5% | SOLD | Exception, not the rule |
| Watermelon | $3,966 | +39.7% | SOLD | |
| bully | $6,433 | +20.2% | SOLD | |

**Avg PnL:** +23.3% — but 1 of 3 had massive drawdown before exit.

### Entry MC ≥ $10K (SAFER)
| Token | Entry MC | PnL | Status | Notes |
|-------|----------|-----|--------|-------|
| cursor | $10,288 | +2.7% | SOLD | Breakeven |
| DOPAMINE | $85,096 | +80.2% | SOLD | Best trade |

**Avg PnL:** +41.5% — 2/2 wins, no losses.

## Lessons Learned

1. **MC < $5K = death zone.** SL -35% can't protect against 50%+ instant dumps.
2. **MC $10K+ = safer.** More liquidity, more organic holders, SL actually works.
3. **Holders < 50 = red flag.** All stuck positions had < 150 holders at entry.
4. **Sweet spot: MC $10K-$50K, holders ≥ 100.**

## Filter Changes Applied
- MC minimum: $2,700 → $10,000
- Holders minimum: 0 → 50 (hard stop)
- MC scoring: ≥$50K +10, ≥$20K +5, <$8K -5
- Holders scoring: ≥200 +5, <80 -3
