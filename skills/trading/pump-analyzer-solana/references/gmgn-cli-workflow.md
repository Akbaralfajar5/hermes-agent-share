# gmgn-cli Workflow — Preferred Token Scanner

gmgn-cli replaces the manual DexScreener + RugCheck pipeline with curated on-chain data including smart money tracking, bundle detection, and sniper analysis.

## Setup

```bash
npm install -g gmgn-cli
export GMGN_API_KEY="your-key-from-gmgn.ai/ai"
```

## Core Commands

### 1. Fresh Token Scan (replaces DexScreener)

```bash
# Safe preset — filters out obvious scams
gmgn-cli market trenches \
  --chain sol --type new_creation \
  --filter-preset safe \
  --min-marketcap 5000 --max-marketcap 50000 \
  --max-rug-ratio 0.3

# Smart money preset — only tokens smart money entered
gmgn-cli market trenches \
  --chain sol --type new_creation \
  --filter-preset smart-money \
  --min-marketcap 5000 --max-marketcap 100000

# Strict preset — only highest quality
gmgn-cli market trenches \
  --chain sol --type new_creation \
  --filter-preset strict
```

### 2. Advanced Custom Filters

```bash
# Tokens with smart money + KOL buys, low bundle activity
gmgn-cli market trenches \
  --chain sol --type new_creation \
  --min-smart-degen-count 3 \
  --min-renowned-count 1 \
  --max-bundler-rate 0.2 \
  --max-rug-ratio 0.3 \
  --min-marketcap 5000 \
  --sort-by smart_degen_count --direction desc
```

### 3. Token Deep Analysis

```bash
# Security check (replaces RugCheck)
gmgn-cli token security --chain sol --address <CA>

# Holder analysis (with smart money/KOL labels)
gmgn-cli token holders --chain sol --address <CA>

# Basic info
gmgn-cli token info --chain sol --address <CA>

# Pool info
gmgn-cli token pool --chain sol --address <CA>
```

### 4. Trending & Signals

```bash
# 5-min trending on SOL
gmgn-cli market trending --chain sol --interval 5m --limit 20

# Pump.fun only trending
gmgn-cli market trending --chain sol --interval 1h --platform Pump.fun --limit 30

# Price surge signals
gmgn-cli market signal --chain sol --type price-surge --limit 20

# Smart money buy signals
gmgn-cli market signal --chain sol --type smart-money-buy --limit 20
```

## Key Filters (DexScreener Doesn't Have These)

| Filter | Flag | What It Means |
|--------|------|---------------|
| Smart money | `--min-smart-degen-count` | Wallets with proven win rate holding |
| KOL buyers | `--min-renowned-count` | Known influencer wallets bought in |
| Bundle detection | `--max-bundler-rate` | Coordinated wallet groups (dump risk) |
| Sniper hold | `--max-top70-sniper-hold-rate` | % held by sniper bots |
| Rug risk | `--max-rug-ratio` | GMGN's rug pull probability score |
| Insider ratio | `--max-insider-ratio` | Insider trading activity |
| Dev track record | `--min-creator-created-open-ratio` | Dev's graduation rate |

## Filter Presets

| Preset | What It Does |
|--------|-------------|
| `safe` | Excludes rugs, honeypots, wash trading, and known scams |
| `smart-money` | Only tokens with smart money wallet activity |
| `strict` | Combines safe + smart-money + additional quality checks |

## 51 AI Skills Available

Full catalog at `https://gmgn.ai/static/opstatic/skills.json` (cached at `~/.hermes/data/gmgn_skills.json`).

Categories:
- **DATA-ANALYTICS (24):** Trending, new tokens, security, holders, traders, dev analysis, wallet tracking
- **TRADING (12):** Market buy/sell, limit orders, TP/SL, trailing stops, multi-wallet
- **MONITOR (9):** KOL trades, smart money signals, price surge, pump claims, exit signals
- **COOKING (4):** Token launching on Pump.fun, FourMeme, Clanker, etc.
- **MEDIA (2):** Twitter monitoring, crypto news aggregation

## Vs DexScreener + RugCheck

| Feature | gmgn-cli | DexScreener |
|---------|----------|-------------|
| Speed | Near real-time | 30min-6h delay |
| Smart money filter | ✅ | ❌ |
| Bundle detection | ✅ | ❌ |
| Sniper analysis | ✅ | ❌ |
| KOL tracking | ✅ | ❌ |
| Dev history | ✅ | ❌ |
| Rug risk score | ✅ (built-in) | ❌ (needs RugCheck API) |
| Free tier | Limited API calls | Fully free |
| API key required | ✅ | ❌ |
