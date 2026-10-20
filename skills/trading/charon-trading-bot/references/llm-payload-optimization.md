# LLM Payload Optimization

## Problem
When batching 10 candidates for LLM screening, each candidate JSON is ~28KB (full enrichment data). Total request payload: 280KB+. LLM server rejects with HTTP 500.

## Root Cause
- Full candidate object includes all enrichment fields (GMGN stats, chart history, wallet tags, etc.)
- Axios sends entire JSON to LLM endpoint
- Server has payload size limits or processing constraints
- No clear error message — just "500 Internal Server Error"

## Solution: Compact Candidate Data

**File:** `src/pipeline/llm.js`, function `compactCandidateForLlm(row)`

### Before (28KB per candidate)
```javascript
export function compactCandidateForLlm(row) {
  const c = row.candidate;
  const gmgnStats = c.gmgn?.stat || {};
  const gmgnWalletTags = c.gmgn?.wallet_tags_stat || {};
  
  return {
    id: row.id,
    symbol: c.token?.symbol || '',  // Full symbol, can be long
    mint: c.token?.mint?.slice(0, 12) || '',  // 12 chars
    marketCapUsd: Math.round(c.metrics?.marketCapUsd || 0),
    liquidityUsd: Math.round(c.metrics?.liquidityUsd || 0),
    holderCount: c.metrics?.holderCount || 0,
    top20Percent: Math.round((c.holders?.top20Percent || 0) * 10) / 10,
    maxHolderPercent: Math.round((c.holders?.maxHolderPercent || 0) * 10) / 10,
    distanceFromAthPct: Math.round((c.chart?.distanceFromAthPercent || 0) * 10) / 10,
    freshWalletRate: Math.round((Number(gmgnStats.fresh_wallet_rate) || 0) * 100),
    top10HolderRate: Math.round((Number(gmgnStats.top_10_holder_rate) || 0) * 100),
    bundlerPct: Math.round((Number(gmgnStats.top_bundler_trader_percentage) || 0) * 100),
    botDegenRate: Math.round((Number(gmgnStats.bot_degen_rate) || 0) * 100),
    creatorHoldRate: Math.round((Number(gmgnStats.creator_hold_rate) || 0) * 100),  // REMOVE
    smartWallets: Number(gmgnWalletTags.smart_wallets) || 0,
    migrationMC: Math.round(Number(c.gmgn?.migration_market_cap) || 0),  // REMOVE
  };
}
```

### After (Ultra-minimal, ~2KB per candidate)
```javascript
export function compactCandidateForLlm(row) {
  const c = row.candidate;
  const gmgnStats = c.gmgn?.stat || {};
  const gmgnWalletTags = c.gmgn?.wallet_tags_stat || {};
  
  // Ultra-minimal data for LLM screening - avoid 500 errors from large payloads
  return {
    id: row.id,
    symbol: (c.token?.symbol || '').slice(0, 20),  // Truncate to 20 chars
    mint: c.token?.mint?.slice(0, 8) || '',  // Truncate to 8 chars
    // Core metrics only
    marketCapUsd: Math.round(c.metrics?.marketCapUsd || 0),
    liquidityUsd: Math.round(c.metrics?.liquidityUsd || 0),
    holderCount: c.metrics?.holderCount || 0,
    // Holder distribution
    top20Percent: Math.round((c.holders?.top20Percent || 0) * 10) / 10,
    maxHolderPercent: Math.round((c.holders?.maxHolderPercent || 0) * 10) / 10,
    // Chart context
    distanceFromAthPct: Math.round((c.chart?.distanceFromAthPercent || 0) * 10) / 10,
    // GMGN flags (simplified)
    freshWalletRate: Math.round((Number(gmgnStats.fresh_wallet_rate) || 0) * 100),
    top10HolderRate: Math.round((Number(gmgnStats.top_10_holder_rate) || 0) * 100),
    bundlerPct: Math.round((Number(gmgnStats.top_bundler_trader_percentage) || 0) * 100),
    botDegenRate: Math.round((Number(gmgnStats.bot_degen_rate) || 0) * 100),
    smartWallets: Number(gmgnWalletTags.smart_wallets) || 0,
    // Removed: creatorHoldRate, migrationMC (not essential for screening)
  };
}
```

## Impact
- **Before:** 10 candidates × 28KB = 280KB payload → 500 error
- **After:** 10 candidates × 2KB = 20KB payload → Success

## Verification
```bash
cd ~/charon && node -e "
const { compactCandidateForLlm } = require('./src/pipeline/llm.js');
const mockRow = {
  id: 1,
  candidate: {
    token: { symbol: 'VERYLONGTOKENNAME', mint: 'ABC123DEF456GHI789' },
    metrics: { marketCapUsd: 50000, liquidityUsd: 10000, holderCount: 500 },
    holders: { top20Percent: 45, maxHolderPercent: 15 },
    chart: { distanceFromAthPercent: -50 },
    gmgn: { stat: { fresh_wallet_rate: 0.2, top_10_holder_rate: 0.6 }, wallet_tags_stat: { smart_wallets: 10 } }
  }
};
const compact = compactCandidateForLlm(mockRow);
console.log(JSON.stringify(compact).length, 'bytes');
"
```

Expected: ~200-300 bytes per candidate (vs 28KB before).
