# Trading Toolkit Setup (from trading-toolkit-setup skill)

## Recommended Skill Stack

### Layer 1: Technical Analysis & Strategy
- `trading-signals` (scientiacapital/skills) — Markov 7-state regime, Elliott Wave, Fibonacci, Wyckoff
- `trading-strategist` (kukapay/crypto-skills) — Binance API data, TA indicators
- `custom-indicators` (agiprolabs/claude-trading-skills) — Custom formulas, signal interpretation

### Layer 2: News & Macro
- `market-news-analyst` (tradermonty/claude-trading-skills) — Market-moving news 10 days
- `market-environment-analysis` (tradermonty/claude-trading-skills) — Market regime, VIX, sector rotation
- `economic-calendar-fetcher` (tradermonty/claude-trading-skills) — Fed decisions, CPI/PPI, NFP (needs FMP API key)

### Layer 3: Execution
- `binance-trading` / `binance-futures-trading` — Binance CLI + API
- `indicator-chart` — Plotly candlestick charts
- `crypto-tracker` — CoinGecko price tracking

## Installation Pattern
```bash
curl -fsSL "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1" | grep -i "<skill-name>"

# Install

# Download supporting files
SKILL_DIR="$HOME/.hermes/skills/trading/<skill-name>"
mkdir -p "$SKILL_DIR/references" "$SKILL_DIR/scripts"
curl -fsSL "<raw-URL>/references/<file>" -o "$SKILL_DIR/references/<file>"
```

## Timeframe Selection Rules
| Mode | Analysis TFs | Entry TF | SL | Hold |
|------|-------------|----------|-----|------|
| Futures | 4H→1H→15M/5M | 5M–15M | 1–3% (ATR-based) | Minutes–hours |
| Spot swing | 1D→4H | 4H–1D | 10–20% | Days–weeks |

Never use Daily TF for futures entry — SL too wide for leveraged positions.
