# Micin Scan — Python filter + score pattern
# Used with: gmgn-cli market trending --chain sol --interval 5m --order-by volume --limit 50 --filter not_wash_trading --raw
# Pipe output to this script or use in execute_code

# Micin Scan Filter Criteria:
# - vol5m > $500 (volume-first)
# - gain1h > 20% (Signal1 threshold)
# - SM holders > 0 (smart money present)
# - bundler < 40% (not bot-dominated)
# - rug_ratio < 0.3 (not a rug)
# - is_wash_trading = false
# - bot_degen_rate < 50% (not pure bot activity)

# Scoring Formula:
# - SM count (capped at 50) × 2
# - Volume (capped at $100K) / 1000
# - (1 - rug_ratio) × 30
# - gain1h × 0.05 (capped at 30)
# - creator_close: +20
# - cto_flag: +10
# - entrap < 0.05: +15, < 0.10: +8
# - bundler < 0.10: +10, < 0.20: +5
# - dev_hold == 0: +5

# Grade Scale:
# A: SM >= 10, rug < 0.10, bundler < 10% → Strong buy
# B: SM >= 5, rug < 0.15, bundler < 20% → Worth entering
# C: SM >= 1, rug < 0.25 → High risk, small size
# D: Below C → Skip

# Output fields per token:
# symbol, name, address (FULL), exchange, vol5m, mcap, liq, gain1h, gain5m,
# sm, kols, holders, rug, bundler, entrap, top10, bot_rate, dev_hold,
# buy_ratio, swaps, cto, creator_close, twitter, telegram, website

# Deduplication: maintain a `seen` set of previously shown symbols
# On "cari lagi": filter out tokens already in `seen` set

SKIP_SYMBOLS = {
    # Add previously presented tokens here to dedup across scans
    # e.g. 'MUSHU', 'RTM', 'BILLBOARD', 'DOOOOOOOOG', 'OSCAR'
}
