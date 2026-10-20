# Spot Swing Scan — Report Format (the user)

This is the proven output format for spot swing token recommendations. Follow this structure exactly.

## Section 1: Market Context (always first)

```
## 🔍 Market Context
- BTC: $XX,XXX | Fear & Greed: XX (Label)
- Total MCap: $X.XXT (+X.X% 24h)
- BTC Dom: XX.X% — [one-line interpretation: altseason status]
```

## Section 2: Ranked Picks (one block per token)

Each pick block:
```
**#N SYMBOL** — $price | MCap $XXXM
*Category / Narrative*

**Teknikal:**
- Daily score: X/6 ✅ | RSI 1D: XX | RSI 4H: XX
- EMA bull 4H ✅/❌ | MACD bull ✅/❌ | Volume naik ✅/❌
- Jarak dari EMA21 4H: +X.X% — entry quality GOOD/OK/EXTENDED

**Fundamental:**
- [2-3 bullet points: what the project does, why it matters, ATH distance]

**Entry:** $X.XX | **SL:** $X.XX | **TP1:** $X.XX (RR X.Xx) | **TP2:** $X.XX (RR X.Xx)
```

## Section 3: Summary Table

```
## 📊 Ranking Summary
| Token | Daily | RSI 4H | Entry Quality | Risk |
|-------|-------|--------|---------------|------|
| CRV   | 6/6   | 61     | ⭐ BEST       | Medium |
...
```

## Section 4: Notes

- Spot vs futures clarification
- Which tokens are ready to enter NOW vs need pullback
- BTC context (if BTC breaks key level, what happens to alts)
- Position sizing reminder (2-5% per token)

## Key Rules for the user

- **Indonesian language** for explanations
- **No tables for individual token blocks** — use bullet points
- Summary table at the end is OK (it's a comparison, not a data dump)
- Entry quality labels: GOOD (dist EMA21 4H < 5%), OK (5-12%), EXTENDED (>12%)
- Always show RR ratio next to TP levels
- Flag tokens where 4H RSI > 72 as "tunggu pullback" — don't recommend immediate entry
- AAVE/blue chips: lower risk label, higher entry quality bar
- Meme/narrative tokens: flag as high risk explicitly
