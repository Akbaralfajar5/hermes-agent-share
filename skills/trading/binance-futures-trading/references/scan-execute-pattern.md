# Scan & Execute Pattern

One-shot script that scans all liquid pairs, scores them with FibStruct, and batch-executes the top N entries.

## Usage
```bash
cd /home/ubuntu && source .hermes/.env && python3 /tmp/scan_execute.py
```

## Key Design Decisions

1. **Reads API keys from env vars** (`os.environ.get('BINANCE_API_KEY')`) — never hardcode
2. **Filters existing positions** — won't double-enter symbols already open
3. **Sorts by score then R:R** — best setups first
4. **Executes immediately** — no confirmation, no delay
5. **Updates state file** after each entry for daemon pickup
6. **Tries API SL/TP first** — falls back to daemon monitoring on -4120 error

## Config (adjust at top of script)

| Param | Default | Notes |
|-------|---------|-------|
| MIN_VOLUME | 10_000_000 | $10M minimum 24h volume |
| MIN_SCORE | 4 | Minimum confluence score (out of 5) |
| MARGIN_PCT | 0.05 | 5% of balance per trade |
| MAX_ENTRIES | 3 | How many positions to open per run |
| LEVERAGE | Dynamic | Based on SL distance: <0.5%=50x, <1%=30x, <2%=20x, else 10x |

## Flow
```
1. Fetch 183 pairs (sorted by volume, >$10M)
2. Get existing positions (skip already-open symbols)
3. Scan all pairs with FibStruct scoring
4. Filter: score >= 4/5
5. Sort: score DESC, R:R DESC
6. Execute top 3 (excluding existing)
7. Update fibstruct_state.json for daemon monitoring
```

## Pitfalls

- **Env vars must be sourced** — script reads `os.environ.get()` which requires `source .hermes/.env` before execution
- **Qty precision varies** — each pair has different `quantityPrecision`, must query exchangeInfo
- **SL/TP API may fail** — commodity/index pairs (XAUUSDT, SKHYNIXUSDT) return -4120, daemon picks up monitoring
- **Balance changes between entries** — re-query balance before each entry, not just once at start
