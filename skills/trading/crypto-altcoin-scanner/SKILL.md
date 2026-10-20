---
name: crypto-altcoin-scanner
description: "Scan and screen altcoins for trading opportunities using CoinGecko API + Binance OHLC data. Combines fundamental screening (market cap, volume, momentum) with technical analysis (EMA, RSI, MACD) to find long and short setups. Trigger on: find tokens, scan altcoins, best entry, what to trade, screen crypto, momentum scan."
tags: [trading, crypto, screening, altcoin, scanner, coingecko, technical-analysis]
---

# Crypto Altcoin Scanner

Systematic workflow for finding tradeable altcoin setups combining market screening with technical analysis.

## When to Use
- User asks to find tokens to trade (long or short)
- User wants altcoin recommendations with entry points
- Scanning for momentum plays or reversal setups

## Prerequisites
- CoinGecko API (free, no key needed, 10-30 req/min)
- Binance public API for OHLC data (no key needed)
- Python with numpy for TA calculations
- Plotly + kaleido for chart generation (see indicator-chart skill)

## Workflow

### Step 1: Global Context (ALWAYS DO FIRST)
Before any token analysis, check:
1. Market news (market-news-analyst skill)
2. BTC trend and dominance
3. Fear & Greed index
4. Overall market conditions (risk-on/risk-off)

### Step 2: Screen Candidates

**Option A: Binance Futures Top Volume (PREFERRED for futures trading)**

Faster and directly shows tradeable pairs with liquidity:
```python
import requests
resp = requests.get("https://fapi.binance.com/fapi/v1/ticker/24hr")
data = resp.json()
# Filter USDT pairs, sort by volume, exclude BTC/ETH and already-open positions
exclude = ['BTCUSDT', 'ETHUSDT', 'INJUSDT']  # add any open positions
usdt_pairs = [d for d in data if d['symbol'].endswith('USDT') and float(d['volume']) > 0 and d['symbol'] not in exclude]
usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
# Skip pump coins (>30% daily change) — too volatile, likely to reverse
# Also skip brand-new/low-mcap coins with extreme moves
candidates = [p for p in usdt_pairs if abs(float(p['priceChangePercent'])) < 30][:20]
```

**Candidate selection priority:**
- Prefer established coins (SOL, DOGE, XRP, BNB, HYPE, PEPE) over new/unknown tokens
- Skip coins with >30% daily pump (BR, UB, ORCA-type moves) — high reversal risk
- Minimum $150M+ daily quote volume for reliable fills
- Check if available on testnet before full analysis (not all pairs exist there)

**Option B: CoinGecko Markets API (for broader discovery)**

```bash
# Page 1 (top 100 by mcap)
curl -sf "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=24h,7d"

# Page 2 (rank 101-200)
curl -sf "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=2&sparkline=false&price_change_percentage=24h,7d"

# Trending coins
curl -sf "https://api.coingecko.com/api/v3/search/trending"
```

### Step 3: Filter Candidates

**Market cap tiers (ask user preference first):**
- **Low cap:** $5M - $50M (high risk, high reward, lower liquidity)
- **Mid cap:** $50M - $500M (balanced risk-reward)
- **Large cap:** $500M - $10B (safer, established projects)

**User preference (the user):** When asked for "low cap" or "low mcap", use $5M-$50M range. When no market cap specified, default to mid cap ($50M-$500M) for better liquidity.

**LONG filters:**
- 24h change: +2% to +18% (momentum but not overextended)
- 7d change: > 0% (uptrend)
- Skip stablecoins: USDT, USDC, DAI, BUSD, FDUSD, USD1

**SHORT filters:**
- 24h change: < -3% (bearish momentum)
- 7d change: < -5% (downtrend)

**Narrative filters (optional, user preference):**
- Some users prefer narrative-driven (AI/Privacy/DePIN themes)
- Others prefer pure technical + fundamental (project utility, adoption, team)
- **Default (the user):** "tidak harus narasi ai, yg penting teknikal bagus dan fundamental jalan" — prioritize technical score + fundamental quality (liquidity, volume, project utility) over narrative hype. Present narrative categorization as context AFTER technical filtering, not as primary filter.

### Step 4: Technical Analysis per Candidate

**IMPORTANT: Timeframe depends on trade type:**
- **Futures (intraday):** Analyze 4H → 1H → 15M → 5M (top-down)
- **Spot (swing):** Analyze 1D → 4H (daily trend + confirmation)

### Step 4a: Narrative Categorization (Optional)

After technical filtering, categorize candidates by narrative/sector for better context:

**Hot Narratives (2026):**
- **RWA (Real World Assets):** Tokenization of bonds, real estate, commodities (e.g., ONDO, POLYX)
- **DePIN (Decentralized Physical Infrastructure):** Storage, compute, wireless networks (e.g., FIL, HNT, RNDR, MOVR)
- **Layer-1 Alternatives:** Ethereum competitors with high speed (e.g., SUI, ICP, SEI, APTOS)
- **Privacy:** ZK tech, privacy-focused chains (e.g., ZEC, XMR)
- **AI:** Decentralized AI compute and models (e.g., TAO, FET, AGIX)
- **Web3 Infrastructure:** Account abstraction, wallet protocols (e.g., BICO, WCT)
- **Gaming/NFT:** Play-to-earn, NFT marketplaces (e.g., MAGIC, BIGTIME)
- **Meme:** Community-driven tokens (e.g., DOGE, SHIB, PEPE)

**Categorization logic:**
```python
narratives = {}
for coin in candidates:
    name = coin['name'].lower()
    symbol = coin['symbol'].lower()
    
    if any(x in name for x in ['real world', 'ondo', 'rwa']):
        narratives['RWA'] = narratives.get('RWA', []) + [symbol.upper()]
    elif any(x in name for x in ['depin', 'network', 'infrastructure', 'storage', 'moonriver']):
        narratives['DePIN'] = narratives.get('DePIN', []) + [symbol.upper()]
    elif any(x in name for x in ['layer', 'sui', 'aptos', 'sei', 'internet computer']):
        narratives['Layer-1 Alt'] = narratives.get('Layer-1 Alt', []) + [symbol.upper()]
    # ... continue for other narratives
```

Present narrative-categorized results when user asks for "narasi" or wants fundamental context beyond pure technicals.

User preference: "tidak harus narasi ai, yg penting teknikal bagus dan fundamental jalan" — prioritize technical + fundamental quality over narrative hype.

#### Multi-TF Intraday Scoring (for Futures)

Fetch candles from Binance Futures API:
```python
# Use fapi for futures data
url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit=100"
```

Score each timeframe (4H, 1H, 15M) — max 9 points:

| Timeframe | Weight | Criteria |
|-----------|--------|----------|
| 4H | 3 pts | EMA9 > EMA21 > EMA50 = BULL (+3) |
| 1H | 2 pts | EMA9 > EMA21 > EMA50 = BULL (+2) |
| 15M | 1 pt | EMA9 > EMA21 > EMA50 = BULL (+1) |
| 4H MACD | 1 pt | MACD line > Signal = BULL (+1) |
| 1H MACD | 1 pt | MACD line > Signal = BULL (+1) |
| 15M MACD | 1 pt | MACD line > Signal = BULL (+1) |

**Score interpretation:**
- 8-9/9: Perfect alignment — enter with confidence
- 6-7/9: Good setup — enter with tighter SL
- 4-5/9: Mixed — skip or wait for alignment
- 0-3/9: Counter-trend — look for SHORT instead

#### Simplified 4-TF Direction Scoring (Proven Method)

A faster alternative that works well for automated scanning (used in cronjob auto-entry):

```python
def analyze_tf(klines):
    """Score a single TF as LONG, SHORT, or NEUTRAL"""
    closes = [float(k[4]) for k in klines]
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    
    ema20 = calc_ema(closes, 20)
    ema50 = calc_ema(closes, 50)
    macd, _, _ = calc_macd(closes)
    current = closes[-1]
    
    bullish = bearish = 0
    
    # EMA alignment (2 pts)
    if current > ema20 > ema50: bullish += 2
    elif current < ema20 < ema50: bearish += 2
    
    # MACD direction (1 pt)
    if macd > 0: bullish += 1
    elif macd < 0: bearish += 1
    
    # Momentum last 5 candles (1 pt)
    if closes[-1] > closes[-5]: bullish += 1
    else: bearish += 1
    
    # Structure: HH/HL or LH/LL (1 pt)
    if highs[-1] > max(highs[-10:-5]) and lows[-1] > min(lows[-10:-5]): bullish += 1
    elif highs[-1] < min(highs[-10:-5]) and lows[-1] < max(lows[-10:-5]): bearish += 1
    
    if bullish > bearish: return "LONG"
    elif bearish > bullish: return "SHORT"
    return "NEUTRAL"

# Score across 4 TFs
directions = [analyze_tf(k4h), analyze_tf(k1h), analyze_tf(k15m), analyze_tf(k5m)]
long_count = directions.count("LONG")
short_count = directions.count("SHORT")

# Entry decision
if long_count >= 3: entry_side = "LONG"    # 3/4 or 4/4 aligned
elif short_count >= 3: entry_side = "SHORT"
else: entry_side = None  # SKIP — not enough alignment
```

**Scoring rules:**
- 4/4 aligned: High confidence entry, use normal leverage (15-20x)
- 3/4 aligned: Valid entry, slightly tighter SL
- 2/4 or less: SKIP — no entry

**ATR-based SL/TP for auto-entries:**
```python
atr_15m = calc_atr(k15m, period=14)
sl_distance = atr_15m * 1.2  # 1.2x ATR 15M

# For LONG:
sl = entry_price - sl_distance
tp1 = entry_price + sl_distance * 1.5  # RR 1:1.5
tp2 = entry_price + sl_distance * 2.5  # RR 1:2.5
tp3 = entry_price + sl_distance * 3.5  # RR 1:3.5

# For SHORT: reverse the math
```

**Pullback bonus (ideal entry):**
- LONG: 15M RSI between 35-55 (pulled back in uptrend)
- SHORT: 15M RSI between 45-65 (bounced in downtrend)

**RSI filter (avoid traps):**
- Skip LONG if 4H RSI > 75 (overbought)
- Skip SHORT if 4H RSI < 25 (oversold)

#### Daily TF Analysis (for Spot Swing)

Fetch 60 daily candles from Binance:
```bash
curl -sf "https://api.binance.com/api/v3/klines?symbol=INJUSDT&interval=1d&limit=60"
```

Calculate and score (0-6 bullish points):
1. Price > EMA7 (+1)
2. Price > EMA21 (+1)
3. EMA7 > EMA21 (+1)
4. EMA21 > EMA50 (+1)
5. MACD histogram > 0 (+1)
6. RSI > 50 (+1)

**Score interpretation:**
- 5-6: Strong LONG setup
- 3-4: Neutral
- 0-2: Strong SHORT setup

### Step 4b: Token-Specific News Check (MANDATORY for Futures)

**RULE: Teknikal bagus + fundamental jelek = NO ENTRY.**

After a candidate passes technical scoring (≥3/4), MUST check token news before execution:

```python
# Check token-specific news
news_url = f"https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories={token_name}"
resp = requests.get(news_url, timeout=10).json()
# Scan headlines for red flags
```

**Red flags → SKIP entry regardless of score:**
- 🔓 Token unlock >5% supply within 7 days
- 🔴 Hack/exploit/security breach
- ⚖️ SEC/regulatory action
- 📉 Exchange delisting
- 🐋 Whale dump (large on-chain transfers to exchanges)
- 💀 Project abandoned/team gone

**Rating:** ✅ CLEAR (full size) / ⚠️ RISKY (half size) / ❌ SKIP (no entry)

### Step 4c: Set Dynamic Leverage (Volatility-Based)

**DO NOT always use max leverage!** Leverage is scaled inversely with volatility. See `binance-futures-trading` skill for full formula.

```python
# 1. Calculate ATR% volatility
atr_15m = calc_atr(k15m, period=14)
atr_pct = (atr_15m / current_price) * 100

# 2. Query max leverage bracket
r = requests.get(f"{BASE_URL}/fapi/v1/leverageBracket", params=sign({...}), headers=headers)
max_lev = r.json()[0]['brackets'][0]['initialLeverage']

# 3. Calculate appropriate leverage
# ATR% > 2% (shitcoin/meme): 10-20x
# ATR% 1-2% (midcap): 20-50x
# ATR% < 1% (large cap): 50x-MAX
calculated_lev = int(min(max_lev, max(10, 2 / max(atr_pct, 0.01) * 10)))

# 4. Set it
requests.post(f"{BASE_URL}/fapi/v1/leverage", params=sign({"symbol": sym, "leverage": calculated_lev, ...}), headers=headers)
```

**LESSON (TAGUSDT):** Max leverage on volatile token = instant SL hit. Dynamic leverage gives SL room to breathe.

### Step 5: Verify Futures Availability

Check if symbol exists on Binance Futures (testnet or prod):
```bash
binance-cli futures-usds symbol-price-ticker --symbol INJUSDT
```

### Step 6: Determine Entry Type (Market vs Limit)

After identifying the setup, decide order type:

| Condition | Order Type | Example |
|-----------|-----------|---------|
| Price already at support/EMA21 pullback zone | **Market** | Price sitting on 15M EMA21 |
| Price above entry zone, expecting pullback | **Limit** at EMA21/support | Set GTC limit at 15M EMA21 |
| Strong momentum breakout, no pullback expected | **Market** | Breaking key resistance with volume |

**Limit order entry levels (for pullback):**
- Primary: 15M EMA21 (dynamic support in uptrend)
- Secondary: 15M EMA50 (deeper pullback)
- Tertiary: Recent swing low (last 5 candles)

### Step 7: Generate Charts & Execute

Use indicator-chart skill for visual confirmation, then binance-futures-trading skill for execution.

## Pitfalls

### Pandas/Numpy EMA Calculation Error
When calculating EMA, always wrap data in `pd.Series()` first:
```python
# WRONG - causes 'numpy.ndarray' object has no attribute 'ewm'
ema = np.array(closes).ewm(span=period, adjust=False).mean()

# CORRECT
ema = pd.Series(closes).ewm(span=period, adjust=False).mean().tolist()
```

### EMA Calculation with NumPy Arrays
If using `np.array(data).ewm()`, you'll get `'numpy.ndarray' object has no attribute 'ewm'`. Use pandas instead:
```python
import pandas as pd
def calc_ema(data, period):
    return pd.Series(data).ewm(span=period, adjust=False).mean().tolist()
```

### CoinGecko JSON Truncation
Large responses may get truncated in terminal output buffer. Save to file first:
```bash
curl -sf "URL" > /tmp/cg_data.json
python3 -c "import json; ..."  # read from file
```

### CoinGecko Rate Limiting
Free tier: 10-30 requests/minute. Space requests or you get empty responses.

**Mitigation strategy when hitting 429:**
- Wait at least 15 seconds before retry (not 2-5s — that's not enough)
- For individual coin detail calls (`/coins/{id}`), space 4+ seconds between each
- If still hitting 429 after 15s wait, the session quota is exhausted — use cached data from the markets bulk call instead of individual coin detail calls
- The `/coins/markets` bulk endpoint is more quota-efficient than N individual `/coins/{id}` calls — extract as much as possible from the bulk response before falling back to individual calls
- For fundamental data (ATH, categories, description), fall back to manual knowledge for well-known tokens (AAVE, CRV, FET, etc.) rather than burning quota on detail calls

### Testnet Symbol Availability
Not all coins available on testnet. Always verify with `symbol-price-ticker` before attempting to trade.

### Background Processes (&) Not Supported
Do NOT use `&` to background curl/python calls in terminal. The tool rejects it with:
`"Foreground command uses '&' backgrounding. Use terminal(background=true) for long-lived processes"`
Run API calls sequentially, not in parallel via shell backgrounding.

### Strict Filters May Return Zero Results
If initial scan with score ≥5 and RSI 40-70 returns nothing:
- Relax to score ≥4 and RSI 35-75
- Expand market cap range
- Check if market is in consolidation (low volatility = fewer setups)

### RSI Interpretation for Direction
- RSI > 70 + bullish trend = overbought, risky for new LONG entry
- RSI < 30 + bearish trend = can still SHORT (oversold doesn't mean reversal)
- Best LONG entries: RSI 40-65 with bullish EMA structure
- Best SHORT entries: RSI 25-45 with bearish EMA structure

## AITS: Advanced Institutional Trading System (DEPLOYED)

The basic EMA/RSI/MACD method has been **replaced** by AITS for the the user futures trading system. AITS is live at `/home/ubuntu/aits_engine.py` and integrated into the cronjob.

**Key components:**
- **Market Structure (BOS/CHoCH)** — Leading trend detection, replaces lagging EMA crossovers
- **Order Blocks (S/D Zones)** — Institutional entry zones, replaces generic support/resistance
- **Fibonacci OTE (0.618-0.786)** — Confluence with Order Blocks for precision entries
- **Volume Profile + VWAP** — Institutional activity confirmation
- **Liquidity Sweep Detection** — Entry after stop-hunt manipulation phase

**Scoring system (0-100 points):**
| Component | Max Points | What It Measures |
|---|---|---|
| 4H Bias (BOS/CHoCH) | 25 | Directional bias from structure |
| 1H Confirmation | 20 | Structure alignment with 4H |
| 15M Order Block quality | 20 | S/D zone strength (freshness, volume, departure speed) |
| VWAP alignment | 10 | Price vs institutional benchmark |
| Volume confirmation | 10 | Divergence/healthy trend |
| 5M Trigger | 10 | Entry timeframe confirmation |
| Liquidity sweep bonus | 5 | Post-manipulation entry |

**Entry rules:**
- Minimum score: **60/100** (75 if against BTC direction)
- Minimum R:R: **1:2** (vs old 1:1.5)
- SL placement: Below/above Order Block (tight, zone-based vs old ATR-based)
- TP targets: Opposing zone or Fibonacci extensions

**Usage in cronjob:**
```python
import sys
sys.path.insert(0, '/home/ubuntu')
from aits_engine import analyze_aits, score_setup, generate_entry, scan_and_execute

# Full scan
setups = scan_and_execute(btc_bias='bullish', risk_rating='safe', wallet_balance=5000, max_positions=5, current_positions=2)
```

**Observed improvement over basic method:**
- More selective (fewer but higher-quality entries)
- Tighter SL (zone-based vs ATR-based)
- Better R:R (1:2-1:5 vs 1:1.5)
- Target win rate: 80-90% (user benchmark for real account migration)

See `references/advanced-institutional-trading-system.md` for full design documentation.
See `/home/ubuntu/aits_engine.py` for the live implementation.

## Related Skills
- `indicator-chart` — Chart generation
- `binance-futures-trading` — Trade execution
- `trading-signals` — Advanced TA methodologies
- `market-news-analyst` — Global news context
- `crypto-tracker` — Real-time price tracking

## References

**references/quick-single-token-scan.md** - Lightweight 3-TF scan (15pt scoring) for "find me one token" requests. No auth needed, uses public Binance API. Includes entry plan output format preference.

**references/hot-narratives-2026-05.md** - Current hot crypto narratives (May 2026): RWA, DePIN, Layer-1 alts, Privacy, AI, Web3 Infrastructure, Gaming/NFT. Includes market context, strength rankings, key coins per narrative, and fundamental drivers. Update monthly or when narrative shifts occur.

**references/narrative-analysis-workflow.md** - Step-by-step workflow for identifying hot narratives from CoinGecko trending API and categorizing tokens by sector. Includes Python categorization logic, output format, and integration with technical scanner.

**references/spot-swing-report-format.md** - Proven output format for spot swing recommendations (market context → ranked picks → summary table). Follow this for the user scan reports.

**references/spot-position-monitoring-cronjob.md** - Pattern for monitoring spot positions via cronjob. Includes alert thresholds (SL/TP hits, approaching levels), Python monitoring script, and how to add new positions to existing cronjob. Covers both Binance and MEXC positions.

**references/aits-implementation-notes.md** - AITS (Advanced Institutional Trading System) implementation notes

**references/advanced-institutional-trading-system.md** - Full AITS design documentation

