# Charon LLM Decision System

## Overview

Charon uses LLM (e.g., Claude Opus 4.5 via enowX) to analyze token candidates and decide BUY/WATCH/PASS.

## System Prompt (Built-in)

```
You are Charon, a Solana meme coin trench analyst.
Return strict JSON only.
You will receive up to 10 recently matched candidates.
Pick at most one candidate to buy through the configured execution mode.
Use verdict BUY only for the single best unusually strong asymmetric opportunity.
Use WATCH if candidates are interesting but none deserves a buy.
Use PASS if the set is weak or unsafe.
Chart data is ATH/range context. Do not penalize or reward a token only because 24h change is huge; new Pump tokens often do that.
Use distance from ATH/range high and top-blast risk to decide whether entry is late.
Confidence is your conviction from 0 to 100, not probability.
```

## Data Sent to LLM

Each candidate includes:
- `mint` — token address
- `route` — signal source
- `signals` — signal data
- `token` — token info
- `metrics` — market cap, volume, liquidity
- `feeClaim` — fee claim data
- `trending` — trending stats (volume, swaps, rug ratio, bundler rate)
- `holders` — holder distribution
- `chart` — ATH context, distance from high, top-blast risk
- `twitterNarrative` — Twitter sentiment
- `filters` — filter results
- `recent_lessons` — learnings from previous trades

## LLM Output Schema

```json
{
  "verdict": "BUY|WATCH|PASS",
  "selected_candidate_id": 123,
  "selected_mint": "...",
  "confidence": 0-100,
  "reason": "short explanation",
  "risks": ["risk1", "risk2"],
  "suggested_tp_percent": 80,
  "suggested_sl_percent": -25
}
```

## TP/SL Priority System (IMPORTANT)

LLM can suggest TP/SL per token. Charon uses this priority:

```javascript
// From src/db/positions.js lines 34-35
const tp = Number(decision.suggested_tp_percent || strat.tp_percent || numSetting('default_tp_percent', 50));
const sl = Number(decision.suggested_sl_percent || strat.sl_percent || numSetting('default_sl_percent', -25));
```

**Priority order:**
1. **LLM suggestion** (if provided) ← used first
2. **Strategy setting** (if LLM doesn't suggest)
3. **Default global** (fallback)

This means if LLM suggests `suggested_tp_percent: 80`, the position uses 80% TP even if strategy says 100%.

**Rationale:** Adaptive TP/SL based on token-specific conditions:
- Volatile token → tighter SL
- Strong momentum → higher TP
- Risky token → lower TP (take profit quickly)

**To disable:** Edit `src/db/positions.js` to always use `strat.tp_percent` instead of checking `decision.suggested_tp_percent` first.

## Confidence Threshold

LLM verdict BUY only executes if `confidence >= strategy.llm_min_confidence`:
- Sniper: 50%
- Dip Buy: 60%
- Smart Money: 70%
- Degen: LLM disabled (0%)

## Learning System

Charon has a learning loop:
1. `learning_lessons` table stores lessons from past trades
2. Active lessons are injected into LLM prompt via `recent_lessons`
3. LLM learns patterns: what worked, what failed

Query active lessons:
```sql
SELECT lesson FROM learning_lessons WHERE status = 'active' ORDER BY id DESC LIMIT 6;
```

## LLM Configuration (.env)

```bash
ENABLE_LLM=true
LLM_BASE_URL=http://localhost:1430/v1  # enowX local
LLM_API_KEY=enx-...
LLM_MODEL=claude-opus-4.5
LLM_TIMEOUT_MS=60000
LLM_CANDIDATE_PICK_COUNT=10
LLM_CANDIDATE_MAX_AGE_MS=600000
```

## Troubleshooting

**LLM not making decisions:**
- Check `ENABLE_LLM=true` in .env
- Verify `LLM_API_KEY` is valid
- Check `use_llm: true` in strategy config
- Ensure confidence meets minimum threshold

**LLM always returns WATCH:**
- Lower `llm_min_confidence` in strategy
- Check if candidates pass filters first (LLM only sees filtered candidates)
- Review `recent_lessons` — bad lessons can make LLM too conservative
