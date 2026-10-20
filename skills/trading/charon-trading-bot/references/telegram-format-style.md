# Telegram Format Style Guide

User preference: clean, structured, scannable reports with visual hierarchy.

## Design Principles
- Box-drawing characters (`┌─`, `│`, `└─`) for grouped sections
- `━━━━━━━━━━━━━━━━━━━━━━` full-width separators for headers
- Emoji for instant visual status recognition
- Sections grouped logically: Entry, Performance, Rules
- PnL shown as both % and SOL amount
- Glanceable — user wants to know status in 2 seconds

## Emoji Conventions
- PnL: 🚀 (>+50%), 🟢 (profit), 🟡 (small loss <-10%), 🔴 (big loss)
- Exit: 💰 (TP/PROFIT_LOCK), 🛑 (SL), ⏱ (MAX_HOLD/timeout)
- Mode: 🧪 DRY, 🔴 LIVE
- Entry: 🟢 BUY EXECUTED (live), 🧪 DRY RUN — BUY
- LLM verdict: ✅ BUY, 👀 WATCH, ❌ PASS

## Position Format (formatPosition)
```
━━━━━━━━━━━━━━━━━━━━━━
🟢 FKE  ·  #80
━━━━━━━━━━━━━━━━━━━━━━

🔗 AzeNfR...9gTk

┌─ Entry
│  Mcap: $12.5K
│  Size: 0.0500 SOL
│  TX: 3eVzh7...rGnD
└─

┌─ Performance
│  PnL: +96.0% (+0.0480 SOL)
│  High: $24.5K
│  Status: OPEN
└─

┌─ Rules
│  TP: unlimited  ·  SL: -18%
│  Profit Lock: 20%→+5, 40%→+15, 80%→+40, 150%→+90
│  Mode: 🧪 DRY
└─

✅ Exit: TP at $24.5K
   TX: 5hYe7...LrdH
```

## Candidate Summary (candidateSummary)
```
━━━━━━━━━━━━━━━━━━━━━━
🛶 Genomusagent ($GENOMUS)
━━━━━━━━━━━━━━━━━━━━━━

🔗 Dx7smZ...pump
<code>Dx7smZsHqzRqRnNM3VMvuFxpWzcoczqCEhQjQcWZpump</code>
📡 Signal: trending

┌─ Metrics
│  Mcap: $14.3K  ·  Liq: $5.2K
│  Fees: 0.0000 SOL  ·  Grad vol: $0
└─

┌─ Holders
│  Count: 45  ·  Top20: 62.3%
│  Max: 8.5%  ·  Saved: 0/0
└─

┌─ Trending
│  Rank: #12/5m  ·  Vol: $3.2K
│  Swaps: 15  ·  Hot: 2  ·  Smart: 1
└─

┌─ Chart
│  ATH dist: -25.0%  ·  Above low: 45.0%
│  Top risk: ✅ NO
└─

✅ LLM: BUY 72.0%
   Token ini punya momentum kuat dan holder terdistribusi baik.
```

## Batch Screening (batchRevealSummary)
```
━━━━━━━━━━━━━━━━━━━━━━
🧭 SCREENING BATCH #374
━━━━━━━━━━━━━━━━━━━━━━

📊 Screened: 9 tokens
❌ Decision: PASS 25.0%

⚡ Trigger: NETHERLAND · iabWvp...pump · trending · mcap $23.1K · liq $0
🎯 Pick: none

💬 Batch dominated by World Cup country coins...
```

## PnL Summary (/pnl command)
```
━━━━━━━━━━━━━━━━━━━━━━
📊 DRY RUN PnL
━━━━━━━━━━━━━━━━━━━━━━

🟢 Total: +0.0914 SOL

┌─ Stats
│  Trades: 80 closed, 5 open
│  Wins: 45 · Losses: 35
│  Win rate: 56%
│  Avg PnL: 2.4%
│  Best: +96% · Worst: -36.8%
└─

┌─ By Exit Type
│  ✅ PROFIT_LOCK: 5x · avg +8% · +0.02 SOL
│  ❌ SL: 21x · avg -29% · -0.31 SOL
│  ⏱ MAX_HOLD: 29x · avg +12% · +0.17 SOL
└─

┌─ Recent Wins
│  🟢 FKE +96.0% (TP)
│  🟢 Shithouse +34.7% (MAX_HOLD)
└─
```

## Strategy Menu (/strategy)
```
🎯 Strategy

Active: Profit Lock
Size: 0.0500 SOL
Max positions: 10
SL: -18.0%
TP: unlimited

Profit Lock Tiers:
  +20% → SL locks at +5%
  +40% → SL locks at +15%
  +80% → SL locks at +40%
  +150% → SL locks at +90%
  After top tier: trail -40% from high
  Confirm: 45s

Mcap: $8.0K — $100.0K
Min holders: 25
LLM: no (rule-based)

○ Degen
○ Dip Buy
▶ Profit Lock
○ Smart Money
```

## Position Exit Notification
```
💰 DRY CLOSE — PROFIT_LOCK  ·  +15.2%

━━━━━━━━━━━━━━━━━━━━━━
🟢 FRANCE  ·  #83
━━━━━━━━━━━━━━━━━━━━━━
[full position format]
✅ Exit: PROFIT_LOCK at $73.2K
```

## Key Implementation Notes
- All HTML uses `parse_mode: 'HTML'` — escape with `escapeHtml()` for user-provided text
- Links: `<a href="url">text</a>` — always set `disable_web_page_preview: true`
- Monospace for mint addresses: `<code>full_address</code>`
- Short addresses: `short(address)` = first 6 + last 4 chars
- GMGN link: `https://gmgn.ai/sol/token/{mint}`
- Solscan TX: `https://solscan.io/tx/{signature}`
