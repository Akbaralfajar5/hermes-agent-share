# Ponyin Instant Scalping - 4 Filter Protocol

Source: Ponyin Trading Intel Vol. 2 — A7

## Overview

Instant Scalping is a method for trading new pairs on Solana with 4 strict filters. According to Ponyin data, 70% of followers successfully avoided rugs after applying this method.

**Golden Rule:** "JANGAN GANTI ATURAN DI TENGAH JALAN" — Don't change rules mid-trade. FOMO = skip filter = rug.

## The 4 Filters

### Filter 1: Global Gas Fee (NOT available in GMGN)
Check Solana network conditions before entry.

| Condition | Interpretation | Action |
|-----------|----------------|--------|
| Normal/Low | Traffic quiet, smooth execution | PROCEED |
| High | Traffic busy, tight competition | CAUTION |
| Very High | Bot war, retail loses | SKIP or wait |

**Note:** Charon doesn't fetch gas fee data. Would need Solana RPC integration.

### Filter 2: Wallet Age (Fresh Wallet Rate)
Check age of funded wallets holding the token.

**Red Flag:** Many holders with wallets funded < 24 hours before launch = wallets prepared for manipulation.

**GMGN Data Available:**
- `stat.fresh_wallet_rate` — % of fresh/new wallets
- `wallet_tags_stat.fresh_wallets` — count of fresh wallets

**Threshold:** `freshWalletRate > 0.3` (30%) = RED FLAG

### Filter 3: Top Holder Balance/Concentration
Check SOL balance and concentration of top holders.

**Red Flag:** Top holders with balance < 0.2 SOL = not serious players, likely dummy wallets.

**GMGN Data Available:**
- `stat.top_10_holder_rate` — % held by top 10
- `stat.top_bundler_trader_percentage` — bundler activity
- `stat.bot_degen_rate` — bot/degen activity
- `stat.top70_sniper_hold_rate` — sniper holdings

**Thresholds:**
- `top10HolderRate > 0.5` (50%) = RED FLAG
- `maxHolderPercent > 20%` = RED FLAG
- `bundlerTraderPct > 0.1` (10%) = RED FLAG
- `botDegenRate > 0.3` (30%) = RED FLAG
- `sniperHoldRate > 0.2` (20%) = RED FLAG

**Note:** GMGN provides % token holdings, not SOL balance of holders.

### Filter 4: Entry Market Cap vs Deploy MC
Check if token already pumped from deploy.

**Red Flag:** Token launched at < 3K MC and already pumped significantly = you're late, becoming exit liquidity.

**GMGN Data Available:**
- `migration_market_cap` — MC when migrated from Pump.fun
- `creation_timestamp` — token creation time
- `open_timestamp` — trading open time

**Threshold:** `currentMC > (migrationMarketCap * 10)` = RED FLAG (10x from deploy = late)

## Decision Matrix

| Flag Count | Decision | Notes |
|------------|----------|-------|
| 0 flags | GAS IT ✅ | All filters clear, good scalp potential |
| 1 flag | GAS IT (careful) ⚠️ | 60-70% potential on fresh launch |
| 2+ flags | SKIP ❌ | Don't think twice, find another token |

## Additional Red Flags from GMGN

| Field | Threshold | Meaning |
|-------|-----------|---------|
| `creatorHoldRate` | > 5% | Dev still holding, dump risk |
| `ratTraderPct` | > 5% | Insider trading detected |
| `entrapmentPct` | > 10% | Honeypot risk |

## Positive Signals

| Field | Threshold | Meaning |
|-------|-----------|---------|
| `smartWallets` | > 50 | Smart money interest |
| `creatorTokenStatus` | "creator_close" | Dev sold/closed position |

## LLM Prompt Implementation

The Ponyin 4-Filter Protocol was added to Charon's LLM system prompt in `src/pipeline/llm.js`:

1. **Data enrichment** — `compactCandidateForLlm()` now includes `gmgnAnalysis` object with all GMGN stats
2. **System prompt** — Instructs LLM to count flags and apply decision rules
3. **Reason field** — LLM mentions flag count and which flags triggered

### gmgnAnalysis Object Structure

```javascript
gmgnAnalysis: {
  // Filter 2: Wallet Age
  freshWalletRate: Number,
  freshWalletCount: Number,
  
  // Filter 4: Deploy MC
  migrationMarketCap: Number,
  creationTimestamp: Number,
  openTimestamp: Number,
  
  // Manipulation detection
  botDegenRate: Number,
  bundlerTraderPct: Number,
  ratTraderPct: Number,
  entrapmentPct: Number,
  sniperHoldRate: Number,
  
  // Holder analysis
  top10HolderRate: Number,
  creatorHoldRate: Number,
  devTeamHoldRate: Number,
  
  // Wallet categories
  smartWallets: Number,
  whaleWallets: Number,
  bundlerWallets: Number,
  sniperWallets: Number,
  
  // Dev info
  creatorTokenStatus: String,
  creatorCreatedCount: Number,
}
```

## GMGN API Data Reference

Full token info endpoint: `GET /v1/token/info?chain=sol&address={mint}`

Key fields for Ponyin filters:
- `stat.fresh_wallet_rate`
- `stat.bot_degen_rate`
- `stat.top_bundler_trader_percentage`
- `stat.top_rat_trader_percentage`
- `stat.top_entrapment_trader_percentage`
- `stat.top70_sniper_hold_rate`
- `stat.top_10_holder_rate`
- `stat.creator_hold_rate`
- `stat.dev_team_hold_rate`
- `wallet_tags_stat.smart_wallets`
- `wallet_tags_stat.fresh_wallets`
- `wallet_tags_stat.bundler_wallets`
- `wallet_tags_stat.sniper_wallets`
- `wallet_tags_stat.whale_wallets`
- `migration_market_cap`
- `creation_timestamp`
- `open_timestamp`
- `dev.creator_token_status`
