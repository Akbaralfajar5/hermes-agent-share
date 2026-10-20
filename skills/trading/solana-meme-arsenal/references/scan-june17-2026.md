# Scan Session — June 17, 2026 (03:00-09:00 WIB dead zone)

## Summary
- 84 unique tokens from GMGN signals (50 gainer + 50 volume spike, overlapping)
- 10 passed pre-filter (MC range, holders >20, social, bundler <25%, bot <50%, non-serial-deployer)
- **0 passed RugCheck** — 100% whale trap rate (all Top1 > 50%)
- 8/10 had Top1 > 90%, confirming systemic whale-trap pattern

## Pre-Filter Breakdown (84 → 10)
| Filter | Rejected | Count |
|--------|----------|-------|
| Not pump.fun suffix | Various | ~40 |
| Already analyzed | parsec, DJBOOM, CHAD, etc | 15 |
| No social | Epsilon, MOON | 2 |
| Bot >50% w/o SM | ELONBOT, SHHH, Cuben, etc | 9 |
| Serial deployer (>10) | Sprouts(48), Saviour(38), STARTPUP(84), MechaMusk(15) | 4 |
| Bundler >25% | WISH(26.9%), LOOP(44.3%), Elgatito(36.1%) | 3 |
| Holders <2 | X-Man, CUBICLE, MerlinTrump, Niger | 4 |
| MC out of range | DASH ($2575) | 1 |
| Rug ratio >0.10 | nobody (0.5) | 1 |

## RugCheck Results (10 → 0)
| Symbol | CA | MC | Top1 | Top5 | Score | Status |
|--------|----|----|------|------|-------|--------|
| EGO | HLAbDm2T...pump | $9.5K | 99.9% | 111.8% | 1 | 🚫 |
| Fatou | FMG8uGf9...pump | $11.3K | 99.1% | 118.9% | 1 | 🚫 |
| BELLE | DfkwfjYt...pump | $6.6K | 99.7% | 111.3% | 1 | 🚫 |
| GOBMINING | 2shdcDjj...pump | $7.3K | 91.3% | 103.8% | 1 | 🚫 |
| Memes | 3x2CW9So...pump | $6.3K | 90.0% | 104.0% | 1 | 🚫 |
| Delic | EosZb7rj...pump | $76K | 96.0% | 133.6% | 1506 | 🚫 |
| TRILLIONAIRE | ChmoXrX6...pump | $7.3K | 99.1% | 111.8% | 1 | 🚫 |
| FIH | CsTkBg12...pump | $9.5K | 64.6% | 78.6% | 1 | 🚫 |
| ROI | CNWddst4...pump | $3.8K | 99.4% | 122.2% | 1 | 🚫 |
| prysmatic | G282Uu6G...pump | $8.4K | 68.8% | 82.5% | 1 | 🚫 |

## Key Observations
1. **100% whale trap rate** during dead zone hours — matches June 16 scan perfectly
2. **RugCheck Top1 is the primary filter** — GMGN T10 is unreliable for fresh tokens (Fatou T10=0.8% but RugCheck Top1=99.1%)
3. **Top5 > 100%** on many tokens (111-133%) — indicates RugCheck includes bonding curve or LP in holder math, making Top5 less reliable as absolute number
4. **All scores = 1** except Delic (1506) — RugCheck gives minimal score to pure bonding curve tokens
5. **LP = 0** for all — all still on bonding curve, none graduated
6. **RugCheck-first saves API calls** — avoided 10 GMGN token info + security calls

## Recommendation
- Dead zone (03:00-09:00 WIB): scan 3 candidates max, abort early if Top1 >90% on all 3
- Prime hours (21:00-01:00 WIB): full scan, expect better signal-to-noise
