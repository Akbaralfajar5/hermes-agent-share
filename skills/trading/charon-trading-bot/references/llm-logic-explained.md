# Charon LLM Logic Explained

## Overview

Charon uses LLM (configurable, default MiniMax M2.7) to analyze up to 10 candidate tokens and decide BUY/WATCH/PASS.

## System Prompt

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

```javascript
{
  candidate_id,
  mint,
  route,           // signal source
  signals,         // signal data
  token: { name, symbol, gmgnUrl, twitter, website, telegram },
  metrics: { marketCapUsd, priceUsd, liquidityUsd, holderCount, gmgnTotalFeesSol },
  feeClaim,        // fee claim data
  trending: { bundler_rate, rug_ratio, is_wash_trading, volume, swaps },
  graduation,      // pump.fun graduation data
  holders: {
    count,
    top20Percent,      // total % held by top 20
    maxHolderPercent,  // largest single holder %
    top20: [{ address, rank, amount, percent, tags }]
  },
  chart: {
    currentNative,
    rangeHighNative,
    distanceFromAthPercent,
    topBlastRisk,
    athContext24h: { current, high, low, distanceFromHighPercent, aboveLowPercent }
  },
  savedWalletExposure,
  twitterNarrative,  // Twitter sentiment
  filters            // filter results
}
```

## LLM Output Schema

```json
{
  "verdict": "BUY|WATCH|PASS",
  "selected_candidate_id": 42,
  "selected_mint": "...",
  "confidence": 78,
  "reason": "Strong holder distribution, dev sold early, organic Twitter buzz",
  "risks": ["low liquidity", "new token"],
  "suggested_tp_percent": 80,
  "suggested_sl_percent": -25
}
```

## TP/SL Priority

Charon uses this priority for TP/SL:
1. **LLM suggestion** (if provided) — used first
2. **Strategy setting** (if LLM doesn't suggest)
3. **Default global** (fallback)

This means LLM can adjust TP/SL per token based on analysis:
- Volatile token → tighter SL
- Strong momentum → higher TP
- Risky token → lower TP (take profit quickly)

## Learning System

LLM receives `recent_lessons` — lessons from previous trades injected into prompt so it learns from experience.

```javascript
const user = {
  task: 'Pick the best dry-run buy candidate...',
  recent_lessons: activeLessonsForPrompt(),  // up to 6 lessons
  output_schema: {...},
  candidates: [...]
};
```

## Confidence Threshold

LLM verdict BUY only executes if confidence >= strategy's `llm_min_confidence`:
- Sniper: 50%
- Dip Buy: 60%
- Smart Money: 70%
- Degen: 0% (LLM disabled)

## Configuration

```env
ENABLE_LLM=true
LLM_BASE_URL=http://localhost:1430/v1  # or https://api.minimax.io/v1
LLM_API_KEY=your-key
LLM_MODEL=claude-opus-4.5  # or MiniMax-M2.7
LLM_TIMEOUT_MS=60000
LLM_CANDIDATE_PICK_COUNT=10
LLM_CANDIDATE_MAX_AGE_MS=600000
```

## Key Files

- `src/pipeline/llm.js` — LLM integration, prompt construction
- `src/pipeline/candidateBuilder.js` — builds candidate data
- `src/db/positions.js` — uses LLM suggested TP/SL
