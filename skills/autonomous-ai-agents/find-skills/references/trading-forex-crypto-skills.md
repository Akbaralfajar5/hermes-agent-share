# Trading / Forex / Crypto Skills Landscape

Surveyed 2025-07, updated 2026-05. Install counts are weekly at time of survey.

## Top Recommendations (by coverage & quality)

### 1. trading-signals — `scientiacapital/skills` (336 installs)
**Most comprehensive multi-asset skill.** Built on ThetaRoom (50K+ lines).
- 7-state Markov regime model (identify regime first, then route)
- Asset routing: Forex → `forex.md`, Crypto → `elliott-wave.md` + `markov-regime.md`, Options → `options-trading.md`, etc.
- Confluence scoring: 0.7-1.0 high conviction, 0.4-0.7 moderate, <0.4 no trade
- Risk management: max 2% per trade, 15% portfolio, 8% drawdown halt
- Includes: sentiment signals, backtesting patterns, daily trading workflow
- 18 reference files: forex.md, risk-management.md, elliott-wave.md, fibonacci.md, markov-regime.md, wyckoff.md, pattern-recognition.md, sentiment-signals.md, vix-volatility.md, commodities.md, equities.md, options-trading.md, options-strategies.md, turtle-trading.md, backtesting-patterns.md, daily-trading-workflow.md, swarm-consensus.md, chinese-llm-stack.md

### 2. trading-strategist — `kukapay/crypto-skills` (586 installs)
**Crypto-focused, data-driven strategies via Binance API.**
- Real-time price/volume from Binance (`/api/v3/ticker/price`, `/api/v3/klines`)
- TA indicators: SMA, RSI, MACD, Bollinger Bands, Stochastic
- Sentiment aggregation from crypto RSS feeds
- Risk management: stop-loss, position sizing (1-5% of capital), volatility warnings
- Scripts: `calculate_ta.py`

### 3. custom-indicators — `agiprolabs/claude-trading-skills` (37 installs)
**Custom crypto-native indicators beyond standard TA.**
- References: `indicator_formulas.md`, `signal_interpretation.md`
- Scripts: `compute_crypto_indicators.py`, `holder_momentum.py`
- Note: Triggers CAUTION on security scan due to `pip install` command — safe to `--force`

---

## News & Macro Skills (Essential for Traders)

### 4. market-news-analyst — `tradermonty/claude-trading-skills` (867 installs)
**Automated analysis of market-moving news from past 10 days.**
- 6 categories: monetary policy, inflation, earnings, geopolitical, commodities, corporate
- Impact scoring: price movement magnitude × breadth × forward significance
- Multi-asset reaction analysis (equities, bonds, commodities, currencies)
- Generates structured Markdown reports
- Requires: WebSearch and WebFetch tools

### 5. market-environment-analysis — `tradermonty/claude-trading-skills` (691 installs)
**Comprehensive market conditions assessment.**
- Market regime: Risk-On/Risk-Off, VIX level, sector rotation
- Multi-market overview: US, Asia, Europe
- Forex & commodities trends
- Script: `market_utils.py` (report header, session times, VIX categorization)

### 6. economic-calendar-fetcher — `tradermonty/claude-trading-skills` (247 installs)
**Upcoming economic events from FMP API.**
- Central bank decisions, employment, inflation, GDP, trade, housing
- Covers: US, EU, UK, Japan, China, Canada, Australia
- Script: `get_economic_calendar.py` (Python stdlib only)
- Requires: FMP API key (free at financialmodelingprep.com, 250 req/day)

---

## Chart & Price Skills

### 7. indicator-chart (local skill)
**Interactive Plotly candlestick charts with TA indicators.**
- Supports: EMA, RSI, MACD, BB, Supertrend, Ichimoku, Stochastic, ADX, OBV
- Uses Binance API for OHLC data (no key needed)
- Exports: HTML (interactive) or PNG (via kaleido + Chrome)
- Pitfall: Kaleido v1+ needs Chrome — run `kaleido.get_chrome_sync()` first

### 8. crypto-tracker — `sundial-org/awesome-openclaw-skills` (93 installs)
**Real-time crypto prices + alerts via CoinGecko (no API key).**
- Price check, search coins, set alerts (above/below/change/drop/rise)
- Script: `crypto.py` (uses `uv run`)
- CoinGecko free tier: ~10-30 req/min

### 9. generate-asset-price-chart — `besoeasy/open-skills` (13 installs)
**Render candlestick PNG from OHLC data (no API calls).**
- Node.js (canvas) or Python (matplotlib) options
- Dark background, green/red candles, grid

---

## Binance Execution Skills (Trade Execution)

### 10. binance-trading — `binance/binance-skills-hub` (official)
**Official Binance skill for executing trades via `binance-cli`.**
- Covers: Spot, USDS-M Futures, COIN-M Futures, Options, Algo, Margin, Wallet
- Requires: `binance-cli` (npm: `@binance/binance-cli`) + Node.js 22+
- Auth: `BINANCE_API_KEY` + `BINANCE_SECRET_KEY` env vars, or profile system
- Key references: `auth.md`, `futures-usds.md`, `spot.md`, `algo.md`, `wallet.md`
- Install method: Clone repo + manual copy (rate limits often block URL install)
  ```bash
  cd /tmp && git clone --depth 1 https://github.com/binance/binance-skills-hub.git
  SKILL_DIR="$HOME/.hermes/skills/trading/binance-trading"
  mkdir -p "$SKILL_DIR/references"
  cp /tmp/binance-skills-hub/skills/binance/binance/references/{auth,futures-usds,spot,algo,wallet,margin-trading,convert,derivatives-options,futures-coin}.md "$SKILL_DIR/references/"
  ```
- binance-cli install: `npm install -g @binance/binance-cli` (requires Node 22+)
- Key futures commands:
  ```bash
  binance-cli futures-usds change-initial-leverage --symbol INJUSDT --leverage 5
  binance-cli futures-usds new-order --symbol INJUSDT --side BUY --type LIMIT --quantity 100 --price 3.55 --time-in-force GTC
  binance-cli futures-usds new-order --symbol INJUSDT --side SELL --type STOP_MARKET --stop-price 3.18 --close-position true
  ```

### Other Exchange Skills
| Skill | Source | Installs | Exchange |
|-------|--------|----------|----------|
| binance-futures-signal-bot | aradotso/trending-skills | 314 | Binance |
| gate-exchange-futures | gate/gate-skills | 120 | Gate.io |
| futures-trading | kucoin/kucoin-skills-hub | 45 | KuCoin |
| bybit-futures | alsk1992/cloddsbot | 25 | Bybit |
| mexc-futures | alsk1992/cloddsbot | 15 | MEXC |

---

## Recommended Install Bundle (Complete Trading Toolkit)

For a full forex+crypto analysis AND execution setup, install in this order:

```bash
# 1. Analysis & TA
trading-signals, trading-strategist, custom-indicators

# 2. News & Macro
market-news-analyst, market-environment-analysis, economic-calendar-fetcher

# 3. Charts & Prices
indicator-chart (local), crypto-tracker, generate-asset-price-chart

# 4. Execution
binance-trading (manual clone install)
```

Total: 10 skills covering the full pipeline from news → analysis → chart → execution.

---

## Quality Notes for This Domain
- Install counts are much lower than web-dev skills (max ~900 vs 100K+)
- Most repos have <100 GitHub stars — normal for this niche
- `scientiacapital/skills` is the most professionally structured (multi-reference architecture)
- `tradermonty/claude-trading-skills` is the best for news/macro (3 complementary skills)
- `binance/binance-skills-hub` is the only official exchange skill hub
- Always review security audits on skills.sh before installing trading skills
- Trading skills often require external API keys (Binance, FMP, Octagon MCP)
- `binance-cli` requires Node.js 22+ (Node 18 fails with `styleText` import error)
