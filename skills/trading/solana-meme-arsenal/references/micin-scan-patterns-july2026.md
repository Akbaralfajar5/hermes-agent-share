# Micin Scan Patterns — July 2026


Repeated pattern: user asks "cari token micin", "cari lagi", "yg aman masuk"
Goal: find meme tokens that are safe to enter RIGHT NOW with active volume.

## Scan Types by User Intent

### 1. "Cari token micin" / "Cari lagi" — Fresh Micin Discovery
- Use: `market trending --interval 5m --order-by volume --filter not_wash_trading`
- Filter: SM ≥ 1, Rug < 0.30, Bundler < 40%, Vol5m > $500
- Score: SM weight ×2, Volume weight, Safety bonus, CTO/Dev bonus
- Deduplicate by symbol across scans
- Show FULL addresses (never truncate!)

### 2. "Yang aman masuk" — Safe Entry (Graduated Tokens)
- Use: `market trending --interval 1h --order-by volume --filter not_wash_trading`
- Filter: open_timestamp > 0 (graduated), SM ≥ 2, Rug < 0.20, Bundler < 0.25
- Score: SM×3, Volume×0.1, Safety, CTO, Entrap, Bundler, Dev, Holders, Top10
- These are REAL market tokens with MCap $15K-$10M+
- Much safer than bonding curve tokens

### 3. "New pair age" — Fresh Bonding Curve
- Use: `market trenches --chain sol --type new_creation --max-created 30m`
- Filter: strict preset, min-smart-degen 1, min-volume 1000
- These are EXTREME RISK — bonding curve, MCap < $5K
- Only for degens, always warn about risk

### 4. Combined Best-of-All
- Run trending (5m for fresh, 1h for graduated) + smart money signals
- Merge results, dedup, score, present top 5-8

## Scoring Formula (Simplified)

```
score = 0
score += min(sm, 30) × 3      # Smart money weight
score += min(vol/500, 50)       # Volume weight  
score += (1-rug) × 25           # Safety bonus
score += min(gain1h × 0.03, 15) # Momentum bonus
if cto: score += 10
if entrap < 0.05: score += 15
elif entrap < 0.10: score += 8
if bundler < 0.05: score += 12
elif bundler < 0.15: score += 5
if holders > 500: score += 8
if top10 < 0.15: score += 8
if liq > 30000: score += 6
if dev_hold == 0: score += 4
```

## Grading

- 🟢🟢 (Grade A): SM ≥ 10, Rug < 0.10, Bundler < 10%, Entrap < 5%, Top10 < 20%
- 🟢 (Grade B): SM ≥ 5, Rug < 0.12, Bundler < 12%, Entrap < 10%
- 🟡 (Grade C): SM ≥ 3, Rug < 0.18, Bundler < 20%
- 🟠 (Grade D): Everything else that passes basic filters

## Output Format

```
🟢 #1 SYMBOL (Name)
`FULL-CONTRACT-ADDRESS-HERE`
Age: X min | Exchange: pump_amm
Vol: $X | MCap: $X | Liq: $X
1h: +X% | 5m: +X%
SM: X | KOL: X | Holders: X
Rug: X.XXX | Bundler: X.X% | Entrap: X.X%
CTO: Y/N | Dev Close: Y/N
🔗 GMGN: https://gmgn.ai/sol/token/FULL_ADDRESS
💡 One-line verdict
```

## Key Lessons

1. **NEVER truncate addresses** — user lost trust when we fabricated `EwD4QKUL...` endings
2. **Graduated vs Bonding Curve** — "aman masuk" = graduated (real market), "new pair" = bonding curve (degen)
3. **Re-scan = fresh data** — "cari lagi" means new scan, skip previously shown tokens
4. **Score transparency** — show grading criteria so user understands why a token is recommended
5. **Volume is king** — tokens with vol5m > $5K have real interest; below $1K is noise
6. **SM count matters most** — SM ≥ 3 = someone smart is watching; SM 0 = skip
7. **Entrap > 20% = whale trap** — even if other metrics look good
