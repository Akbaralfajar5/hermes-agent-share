---
name: crypto-spot-signal-generator
description: Generate manual crypto spot trading signals using SNR + Price Action + Volume + RSI analysis on 4H timeframe with chart visualization and news validation
version: 1.0.0
dependencies:
  - pandas
  - numpy
  - matplotlib
  - requests
tags:
  - trading
  - crypto
  - spot
  - technical-analysis
  - SNR
  - signals
---

# Crypto Spot Signal Generator

Generate high-quality manual trading signals for cryptocurrency spot markets using Support & Resistance (SNR) analysis combined with Price Action, Volume, and RSI indicators on 4-hour timeframe.

## When to Use

- User requests: "Cari sinyal spot", "Ada setup bagus?", "Scan market dong"
- User wants altcoin hunting: "Cari altcoin mcap rendah", "Cari coin yang belum naik tinggi"
- Manual on-demand signal generation (NOT automated/cron)
- Spot trading only (no leverage, LONG positions only)

## Methodology

**Analysis Framework: SNR + Price Action + Volume + RSI**

### 1. Support & Resistance (SNR)
- Identify pivot points using rolling window (15-20 periods)
- Cluster nearby levels within 1.5-2% threshold
- Find nearest support below and resistance above current price

### 2. Price Action Patterns
- **Bullish Engulfing**: Previous red candle fully engulfed by current green candle
- **Hammer/Pin Bar**: Long lower wick (>60% of range), small upper wick (<10%)
- **Rejection Wicks**: Strong bounce from support level

### 3. Volume Confirmation
- Compare current volume to 20-period moving average
- Look for 1.5x+ volume spike on bounce/breakout
- Higher volume = stronger signal

### 4. RSI (14-period)
- **Oversold (<40)**: Strong buy signal at support
- **Neutral (40-60)**: Room to move up
- **Overbought (>70)**: Avoid entry or wait for pullback

## Scoring System (0-100)

| Criteria | Points | Condition |
|----------|--------|-----------|
| Near support | 25 | Price within 2% of support level |
| At support | 10 | Price within 1% (bouncing) |
| RSI oversold | 20 | RSI < 40 |
| RSI neutral-low | 10 | RSI 40-50 |
| High volume | 20 | Volume > 1.5x average |
| Above avg volume | 10 | Volume > 1.0x average |
| Bullish engulfing | 25 | Pattern confirmed |
| Hammer/pin bar | 20 | Pattern confirmed |

**Minimum Score for Signal: 60/100**

## Entry & Exit Strategy

### Entry
- **Entry Price**: At support level (use LIMIT order)
- Wait for price to touch support before entering
- Confirm with volume spike and bullish candle close

### Take Profit (TP)
- **TP1**: Entry + 1.5% → Close **30%** of position
- **TP2**: Entry + 3.0% → Close **40%** of position
- **TP3**: Nearest resistance or Entry + 5% → Close **20%** of position
- **Trailing**: Remaining 10% with 2% trailing stop from peak

### Stop Loss (SL)
- **SL**: Support level - 1.5%
- Exit immediately if price breaks below SL

### Risk:Reward
- Target minimum 1:2 RR ratio
- Calculate: (TP3 - Entry) / (Entry - SL)

## News & Fundamental Validation

**CRITICAL — DO THIS FIRST**: When user asks about a specific token's situation (delisting warning, ST tag, price crash, etc.), research the project fundamentals BEFORE giving any trading advice. Don't jump to "cut loss" or "hold" without knowing if the project is alive.

### Fundamental Health Check (BEFORE any advice)

**Run this checklist for any token the user holds or asks about:**

1. **CoinGecko/CoinMarketCap listing** — If not listed on either, major red flag
2. **Official website** — Try {token}.io, {token}.network, {token}.ai, {token}.xyz
3. **Social media** — Twitter/X activity, Telegram group, Discord
4. **GitHub** — Active development? Recent commits?
5. **Exchange coverage** — Listed on how many exchanges? Only 1 CEX = extreme risk
6. **DEX liquidity** — Check Uniswap/Raydium/etc for liquidity pools

**Dead project indicators (any 2+ = likely dead/scam):**
- ❌ Not on CoinGecko or CoinMarketCap
- ❌ No working website
- ❌ No GitHub activity
- ❌ No social media presence
- ❌ Only listed on 1 exchange
- ❌ No DEX liquidity
- ❌ No news coverage anywhere

**If project appears dead → tell user immediately, recommend exit. Don't sugarcoat.**

### Global Market News
- Check Fear & Greed Index (CoinMarketCap)
- Major crypto news (CoinDesk, CoinTelegraph)
- Regulatory developments
- Market sentiment (bullish/neutral/bearish)

### Token-Specific News
- Recent announcements
- Partnerships or integrations
- Exploits or security issues
- Exchange listings/delistings
- Major holder movements

**Red Flags** (DO NOT signal):
- Recent exploit or hack
- Negative regulatory news
- Major FUD campaign
- Suspicious price pump (possible dump incoming)
- ST/delisting warning from exchange
- Project has no verifiable online presence

## Implementation Steps

### Step 1: Scan Market
```python
# DUAL-EXCHANGE SCAN (proven workflow May 2026):
# 1. Scan MEXC first (2400+ pairs, most small-cap coverage)
# 2. Scan Binance in parallel (600 pairs, most liquid)
# 3. Cross-reference: tokens on BOTH = safer picks
# 4. MEXC-only tokens need extra fundamental verification

# MEXC scan
url = "https://api.mexc.com/api/v3/ticker/24hr"
# Filter: USDT pairs, vol > $200K, range_pos < 0.35, change -15% to +15%

# Binance scan  
url = "https://api.binance.com/api/v3/ticker/24hr"
# Filter: USDT pairs, vol > $1M, range_pos < 0.30, change -10% to +10%

# Then run 4H RSI + scoring on all candidates from both
```

### Step 2: Technical Analysis
```python
# For each coin:
# 1. Get 4H klines (200 candles)
# 2. Calculate RSI(14)
# 3. Find SNR levels (window=15, threshold=0.015)
# 4. Check price action patterns
# 5. Calculate volume ratio
# 6. Score the setup (0-100)
```

### Step 3: Filter Good Setups
- Score >= 60
- Clear support/resistance levels
- Positive price action
- No conflicting signals

### Step 4: News Check
- Check global crypto news
- Search token-specific news
- Validate no negative developments
- Confirm safe to enter

### Step 5: Generate Chart
```python
# Create 3-panel chart:
# - Panel 1: Candlesticks with SNR levels, entry, TP1/2/3, SL
# - Panel 2: Volume bars (green/red)
# - Panel 3: RSI with 30/70 levels
# Dark theme (#0e1117 background)
# Save as PNG
```

### Step 6: Format Signal
```
🎯 SINYAL SPOT - {SYMBOL}

📊 Setup: SNR + Price Action + Volume + RSI (4H)
⭐ Score: {score}/100

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🪙 Pair: {symbol}
💵 Current Price: ${current_price}

🎯 ENTRY: ${entry_price}
_(Wait for price to touch support level)_

💰 TAKE PROFIT:
• TP1: ${tp1} (+1.5%) → Close 30%
• TP2: ${tp2} (+3.0%) → Close 40%
• TP3: ${tp3} (+X.X%) → Close 20%
• Trailing: 10% remaining with 2% trailing stop

🛑 STOP LOSS: ${sl_price} (-1.5%)

📈 Risk:Reward: 1:{rr_ratio}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 Analisa Teknikal:
✅ {reason_1}
✅ {reason_2}
✅ {reason_3}
...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📰 News Check:

Global Market:
• Fear & Greed Index: {value} ({status})
• {key_news_1}
• {key_news_2}

{Symbol} Specific:
• {token_news_1}
• {token_news_2}

Overall: ✅ SAFE TO ENTER / ⚠️ CAUTION / ❌ AVOID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ Trading Notes:
1. Entry Strategy: Use LIMIT order at ${entry}
2. Wait for confirmation: Price must touch support
3. Monitor volume: Ensure volume stays high
4. Strict SL: Exit immediately if breaks ${sl}
5. TP Management: Follow the plan, don't be greedy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MEDIA:/path/to/chart.png
```

## Pitfalls

### Workflow Order (CRITICAL)
- **NEVER give "cut loss" or "hold" advice before researching the project**: When user asks about a token's situation (delisting, crash, ST warning), FIRST check if the project is alive (website, CoinGecko, socials, exchange coverage, DEX liquidity). THEN give advice based on findings.
- **User correction (May 2026)**: "Kenapa anda tidak baca berita/news tokennya dulu bro" — Agent jumped to trading advice without fundamental research. The project turned out to be completely dead.

### Technical Analysis
- **Don't force signals**: If no setup scores >= 60, say "No good setup found"
- **Respect the score**: Don't override scoring system based on "feeling"
- **Volume matters**: Low volume signals are weak, even with good price action
- **Volume SPIKE is the strongest confirmer**: When vol_ratio > 3x average + RSI oversold + near bottom = highest conviction setup (e.g., LRC May 2026: 5.77x volume spike at 9% range position, RSI 26.5 → scored 9/11)
- **RSI context**: Overbought (>70) at support is NOT a good entry
- **Extreme oversold + low volume = trap**: RSI < 20 with declining volume often means no buyers, not a bounce opportunity. Require volume confirmation before recommending entry on extreme oversold tokens

### News Validation
- **Never skip news check**: Even perfect technical setup can fail on bad news
- **Check BOTH global + token**: Global bearish + token bullish = still risky
- **Recent news matters more**: 1-hour old exploit > 1-week old partnership

### Chart Generation
- **Mark ALL levels clearly**: Support, resistance, entry, TP1/2/3, SL
- **Use contrasting colors**: Easy to read on dark background
- **Current price marker**: Show where price is NOW vs entry level
- **Include RSI panel**: Visual confirmation of momentum

### Signal Delivery
- **Wait for setup**: Don't send mediocre signals just because user asked
- **Be honest**: "No good setup right now" is better than weak signal
- **Explain reasoning**: User needs to understand WHY it's a good setup
- **Risk warning**: Always remind about SL and risk management

## Example Session

**User**: "Cari sinyal spot"

**Agent**:
1. Scan top 15 coins by volume
2. Analyze each with SNR + PA + Vol + RSI
3. Score all setups
4. Find XRPUSDT scores 80/100 ✅
5. Check news: No negative news ✅
6. Generate chart with markings
7. Calculate entry/TP/SL
8. Format signal with full analysis
9. Send signal + chart to user

**If no good setup found**:
"Saya sudah scan 15 coins dengan volume tertinggi, tapi belum ada setup yang bagus (score < 60). Kebanyakan coins sedang:
- Jauh dari support level
- Volume rendah
- RSI overbought
- Atau ada berita negatif

Mau saya cek lagi nanti, atau ada coin spesifik yang mau dianalisa?"

## Tools & APIs

- **Binance API**: Market data (klines, 24h ticker) - reliable, works well
- **MEXC API**: Most small-cap coverage, 2400+ pairs (see `references/mexc-api.md`)
- **Gate.io API**: Low-cap altcoin discovery (see `references/gate-io-api.md` for workarounds)
- **DexScreener API**: DEX-only tokens (meme coins, bonding curves, new launches not on CEX)
  ```python
  # Search by name/symbol
  url = "https://api.dexscreener.com/latest/dex/search?q=tokenname"
  # Returns: pairs with priceUsd, priceChange.h24/h1, volume.h24, liquidity.usd, fdv
  # Use for: tokens only on Uniswap/bonding curves, not listed on any CEX
  # Pitfall: multiple pools per token — sort by liquidity, use highest
  ```
- **CoinGecko API**: Category scanning, trending, mcap data (rate limit: 10-30 req/min free tier)
- **CoinMarketCap**: Fear & Greed Index, top coins
- **CoinDesk/CoinTelegraph**: Crypto news
- **Python**: pandas, numpy, matplotlib for analysis & charts
- **Telegram**: Signal delivery with native image support

## Altcoin Hunting Mode

When user wants low market cap altcoins with momentum potential:

### User Criteria (typical)
- Market cap: $5M - $100M
- 24h change: 5-30% (not too high, avoid overbought)
- Volume: >$500k (ensure liquidity)
- Price position: <70% of 24h range (not near top)
- Target: 10-20% gain in 1-3 days

### Multi-Exchange Scanning

**MEXC** (best for low-cap gems & narrative tokens):
```python
# MEXC has 2400+ pairs — most small cap coverage
url = "https://api.mexc.com/api/v3/ticker/24hr"
resp = requests.get(url, timeout=15).json()
# Filter: symbol ends with 'USDT'
# Filter: quoteVolume > 200_000 (lower threshold OK for MEXC gems)
# Exclude leveraged tokens (3L, 3S, 2L, 2S, 4L, 4S, 5L, 5S)
# Calculate range_pos = (lastPrice - lowPrice) / (highPrice - lowPrice)
# Filter: range_pos < 0.3 (near 24h bottom = belum naik)

# MEXC klines for TA:
url = f"https://api.mexc.com/api/v3/klines?symbol={sym}&interval=4h&limit=60"
# Returns: [openTime, open, high, low, close, volume, closeTime, quoteVolume]
# Note: quoteVolume is at index 7 (not 5 like Binance)
```

**Gate.io** (good for low-cap altcoins):
```python
url = "https://api.gateio.ws/api/v4/spot/tickers"
# Filter: currency_pair ends with '_USDT'
# Filter: 5% <= change_percentage <= 30%
# Filter: quote_volume > 500_000
# Calculate price_position = (last - low_24h) / (high_24h - low_24h) * 100
# Filter: price_position < 70%
# Sort by volume descending
```

**Binance** (for established coins):
```python
url = "https://api.binance.com/api/v3/ticker/24hr"
# Same filters as Gate.io
# Cross-check: coins on both exchanges = safer
```

**Exchange priority by user request:**
- "cari di MEXC" → MEXC scan (most gems, lowest mcap)
- "cari di Binance" → Binance scan (safest, most liquid)
- "cari di Gate" → Gate.io scan
- No exchange specified → Scan CoinGecko first, then check availability on user's preferred exchanges (Binance + Gate.io + MEXC)

### Altcoin Scoring (0-100)

| Criteria | Points | Condition |
|----------|--------|-----------|
| Volume | 30 | >$10M excellent / >$5M good / >$2M decent |
| Price position | 30 | <30% very low / <50% low-mid / <70% mid-high |
| Momentum | 25 | 5-15% good / 15-25% strong / >25% risky |
| Room to grow | 15 | >20% good / >10% moderate |

**Minimum Score: 60/100 for recommendation**

### Altcoin Analysis Output

For each candidate, show:
```
{SYMBOL}/USDT
   💰 Price: ${price}
   📈 24h: +{change}%
   💧 Volume: ${volume}M
   📊 Volatility: {volatility}%
   📍 Position: {position}% {🟢 LOW / 🟡 MID / 🔴 HIGH}
```

Then rank by score and present top 5-10 with trade plans.

### Narrative/Catalyst-Driven Scanning

When user wants tokens with **high upside potential** (50%+), use narrative approach instead of pure technical:

**Step 1: Identify hot narratives**
```python
# Check CoinGecko trending
trending = requests.get("https://api.coingecko.com/api/v3/search/trending").json()

# Scan by category (rate limit: space requests 3-5s apart)
categories = {
    'artificial-intelligence': 'AI',
    'real-world-assets-rwa': 'RWA',
    'decentralized-physical-infrastructure-depin': 'DePIN',
    'gaming': 'Gaming',
    'layer-2': 'Layer 2',
    'meme-token': 'Meme',
}
url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&category={cat_id}&order=market_cap_desc&per_page=50&page=1"
```

**Step 2: Known narrative token lists (manually curated, updated May 2026)**
```python
narrative_tokens = {
    # AI Compute/Infra: IO, RENDER, TAO, AIOZ, RLC, AIX, CHIP, FIL, AR, ICP
    # AI Intelligence: ARKM, FET, NEAR, WLD, AGIX, OCEAN, PHB, NFP
    # AI Agents: ELIZAOS, SWARMS, ZEREBRO, VIRTUAL, COOKIE, GRIFFAIN, ARC, ACT
    # AI + Privacy: PSAI (double narrative play)
    # AI + Gaming: AI (Sleepless AI — combo narrative)
    # DePIN: IOTA, IOTX, MOBILE, HNT, WLD, GRASS
    # RWA: ONDO, RSR, POLYX, OM
    # Gaming: PIXEL, PORTAL, XAI, BEAM, ACE, HIGH, MOGU, PLAY, GALA, 9BIT
    # Privacy: ZANO, FIRO, ZEC, DASH, BDX, SCRT, ROSE (follows ZEC pumps)
    # Modular: TIA, ALT, DYM, MANTA, STRK
    # BTC-Fi: CORN, BSB
}
# MEXC-specific AI tokens (most small-cap coverage):
# PSAI, AIX, SWARMS, ELIZAOS, GRIFFAIN, CHIP, AI, ZEREBRO, VIRTUAL, COOKIE, ARC, ALCH
# These are often NOT on Binance — MEXC is the go-to for AI narrative gems
```
```

**Step 3: Score narrative candidates**
```python
score = 0
# RSI oversold (<35: +3, <45: +2, <55: +1)
# Near bottom of 20-bar range (<15%: +3, <30%: +2, <45%: +1)
# Upside to recent high (>50%: +3, >30%: +2, >15%: +1)
# Volume increasing (>1.5x: +2, >1.0x: +1)
# Max score: 11
```

**Step 4: Categorize recommendations**
- **Safe play:** Oversold + volume spike + on major exchange
- **Moonshot:** Micro cap + strong narrative + huge upside (376%+)
- **Narrative bet:** AI/DePIN/Gaming tokens that haven't caught up yet

**Key insight:** "Belum naik" can mean two things:
1. Technically oversold (good for bounce trade 10-20%)
2. Narrative hasn't hit yet (good for 50-200%+ if narrative catches)

Always be honest about probability — oversold ≠ guaranteed pump.

**Double/Triple narrative tokens** (highest conviction picks):
- Tokens that sit at intersection of 2+ hot narratives get more catalysts
- Example: PSAI = AI + Privacy → when EITHER narrative pumps, PSAI benefits
- Example: AI (Sleepless AI) = AI + Gaming → double exposure
- Prioritize these over single-narrative tokens when both narratives are active

**Narrative heat check method:**
```python
# Get Binance top 50 gainers, categorize by narrative
# Count how many tokens per narrative are pumping
# Narrative with most tokens pumping = hottest
# If a token matches 2+ hot narratives = highest priority pick
```

### Altcoin-Specific Risks

⚠️ **Always warn user**:
- Low cap = high risk (rug pull, low liquidity)
- Gate.io only = harder to exit than Binance
- Unknown projects = no fundamental backing
- **Single-exchange tokens** = extreme delisting risk (PSAI lesson: only on MEXC, got ST-tagged May 2026, no DEX liquidity, couldn't exit → total loss)
- **-80%+ decline from recent high** = likely dead project. Skip even if RSI is extreme oversold. Learned from ENM (-83% decline, unverified project — same pattern as PSAI)
- **Bonding curve tokens** (e.g., j3sse.org) = buy/sell ONLY through their contract, no open market listing ever, exit depends on curve reserve holding ETH. Not tradeable on any DEX/CEX. Liquidity = whatever ETH is in the hook contract.
- **Recommendation**: Max 2-5% of portfolio per coin
- **Mandatory**: Tight stop loss (10-15%)
- **Pre-entry check**: Token MUST be on at least 2 exchanges OR have DEX liquidity as exit route
- **Decline filter**: If token dropped >70% from 20-bar high on 4H, flag as potential dead project and require fundamental verification before recommending

### MEXC ST (Special Treatment) Warning System

MEXC applies "ST" tags to tokens at risk of delisting:
- ST tag applied → token may be **delisted 3 days later**
- After delisting: 30-day withdrawal window, then funds at risk
- Deposits disabled immediately after delist
- **Action when ST detected**: Check if token has other exchange listings or DEX liquidity. If not → immediate exit.
- **Monthly announcements**: MEXC publishes ST batches (check announcements page)
- **Pattern**: ST announcement → immediate 40-50% dump day 1 → continued bleed → delist

### MEXC Symbol Naming Pitfalls (CRITICAL)

**ALWAYS verify the exact symbol on MEXC before recommending entry prices!**

MEXC has many tokens with similar/confusing names:
- `AIUSDT` on MEXC ≠ Sleepless AI. Sleepless AI = `SLEEPLESSAIUSDT` on MEXC, `AIUSDT` on Binance
- `AIUSDT` on MEXC ($0.032) is a DIFFERENT token than Binance's `AIUSDT` ($0.023)
- Always cross-check: `https://api.mexc.com/api/v3/ticker/price?symbol={SYMBOL}USDT`

**Verification step (mandatory before giving entry price):**
```python
# Check MEXC for exact symbol
mexc_prices = requests.get("https://api.mexc.com/api/v3/ticker/price", timeout=10).json()
# Search for token name variations
for p in mexc_prices:
    if 'KEYWORD' in p['symbol']:
        print(f"{p['symbol']}: {p['price']}")
```

If user shows a screenshot with a different price than your data, STOP and re-verify the symbol. Don't assume your symbol mapping is correct.

### Head-to-Head Comparison Format

When user asks "mending A atau B?", use structured comparison:
1. Fetch real-time data for BOTH tokens
2. Compare: RSI, range position, volume trend, upside, liquidity, narrative strength
3. Present as table with clear "Winner" column per metric
4. Give final verdict with reasoning tied to user's risk profile and existing positions

### Gate.io API Limitations

**Known Issues**:
- Candlestick endpoint (`/spot/candlesticks`) has timestamp format issues
- Returns 8 columns but structure varies
- **Workaround**: Use ticker data only for altcoin scanning
- For detailed analysis, prefer Binance if coin is listed there

**Ticker-based analysis** (when klines fail):
```python
# Use 24h high/low as support/resistance proxy
support_proxy = low_24h * 1.02
resistance_proxy = high_24h * 0.98

# Calculate position in range
price_position = (current - low_24h) / (high_24h - low_24h) * 100

# Entry/TP/SL based on 24h range
entry = current * 0.99  # 1% below for limit order
sl = low_24h * 0.98     # 2% below 24h low
tp1 = entry * 1.10      # +10%
tp2 = entry * 1.15      # +15%
tp3 = min(entry * 1.20, high_24h * 0.99)  # +20% or near high
```

### User Preference: "Jangan yang naik sudah terlalu tinggi"

When user says this, tighten filters:
- 24h change: **3-15%** (instead of 5-30%)
- Price position: **<50%** (instead of <70%)
- Focus on "early movers" not "already pumped"

Show two lists:
1. **Moderate Momentum** (5-30% gain, safer entry)
2. **Early Movers** (3-15% gain, just starting)

User typically prefers Early Movers for lower risk.

## Position Monitoring & Rotation

### Position Lifecycle Management

When user closes a position (cut loss, TP, or rotation):
1. **Immediately remove/update the monitoring cronjob** — don't wait for user to ask
2. If partial close (e.g., "TP 50%"), keep monitor but update position size
3. If full close, remove the cronjob entirely
4. Ask if user wants a new monitor for the replacement position

**Common user phrases for position closure:**
- "sudah cut" = cut loss, position closed
- "sudah TP" / "baru TP 50%" = take profit (partial or full)
- "stop reminder X" = explicitly remove monitor for X
- "sudah masuk Y" = entered new position Y (may want new monitor)

### Setting Up Spot Monitor Cronjob

After user enters positions, create a cronjob to monitor SL/TP levels:

```
Schedule: every 2h (or every 1h for volatile tokens)
Deliver: origin (same chat)
Enabled toolsets: web, terminal
```

**Cronjob delivery note:** Cronjobs with `deliver: origin` sometimes don't visibly deliver to the chat even when `last_status: ok`. If user reports not receiving updates, manually run the check inline and offer to recreate the cronjob. Always have a fallback: user can ask "cek posisi" and you fetch prices manually.

**Monitor should check:**
1. Current price vs entry (PnL%)
2. Distance to SL and TP levels (alert if within 2%)
3. RSI status (is momentum changing?)
4. Narrative sentiment (is the sector still hot?)

**Alert conditions:**
- Price within 2% of SL → "⚠️ MENDEKATI SL"
- Price hit TP → "🎯 TP HIT — jual X%"
- Price below SL → "🚨 CUT LOSS"
- 24h change > +15% or < -10% → significant move

### Narrative Rotation Decision Framework

When user asks "should I close and rotate?":

1. **Check current narrative heat** — are the top gainers in the same sector?
2. **Check position's narrative** — is it still hot or cooling?
3. **Calculate opportunity cost** — small loss now vs waiting for catch-up

**Decision matrix:**
| Current Position | Narrative Status | Action |
|---|---|---|
| Profit + narrative hot | Still pumping | HOLD |
| Profit + narrative cooling | Momentum fading | Close partial, rotate |
| Small loss + narrative dead | Other sector pumping | Close, rotate |
| Small loss + narrative starting | Just beginning | HOLD, be patient |

**Key rule:** Don't close a token that's ALREADY in the hot narrative (e.g., closing an AI token to buy another AI token = pointless churn). Only rotate when switching TO a hotter narrative.

**Rotation pitfall:** Don't buy tokens that already pumped 15%+ today — you're buying the top. Find tokens in the same narrative that HAVEN'T moved yet.

## Reference Files

- `references/mexc-api.md` — MEXC API endpoints and quirks
- `references/gate-io-api.md` — Gate.io API workarounds
- `references/mexc-ai-tokens-may2026.md` — AI narrative token mapping, sub-narratives, rotation patterns

## Related Skills

- `crypto-futures-trading-system`: Futures trading (different methodology)
- `binance-futures-trading`: Binance Futures API operations
- `market-news-analyst`: News analysis and sentiment
- `indicator-chart`: Chart generation with technical indicators
- `crypto-altcoin-scanner`: Altcoin discovery — OVERLAPS with this skill's altcoin/narrative mode. That skill is futures-focused; this one is spot-focused. Use THIS skill for spot gem hunting.

## Notes

- **CoinGecko rate limiting**: Free tier hits 429 after 2-3 pages. Space requests or accept partial data.
- **MEXC volume inflation**: Some pairs show inflated volume from wash trading. Cross-check with order book depth if possible.
- **"Belum naik" scanning**: Two approaches — (1) pure technical oversold for bounce trades, (2) narrative-driven for moonshots. Always clarify which the user wants and be honest about probability.
