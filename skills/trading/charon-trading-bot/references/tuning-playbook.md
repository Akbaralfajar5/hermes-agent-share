# Charon Tuning Playbook

Operational knowledge for tuning Charon's trading performance. Accumulated from live dry-run sessions.

## Sibling references in this skill

- `references/live-pnl-and-auto-learn.md` — **CRITICAL**: Live Jupiter price for PnL (not high_water_mcap), hourly auto-learn cron setup, route blacklist filter, user exit preferences (TP unlimited, trailing 35%, no max hold, LLM decides holder quality).
- `references/9router-llm-gateway.md` — Pointing Charon's `LLM_BASE_URL` at the local 9router gateway: endpoint shape, where the API key lives, model prefix (`kr/`, `cx/`), `pm2 restart --update-env` requirement, verification curl.
- `references/entry-exit-logic-notes.md` — `PITFALL: Configuring strategy fields that the code doesn't read` — **read before configuring profit_lock or any new flag**.

## Position Monitor Interval

- Config: `POSITION_CHECK_MS` in `src/config.js` (env override available)
- Default was 10s, tuned to **5s** for meme coins
- Why: pump.fun tokens can dump 40% between checks. At 10s, SL set at -20% was exiting at -42%
- Tradeoff: more API calls to Jupiter for price checks

## LLM Concurrency System

File: `src/pipeline/orchestrator.js`

Original design: single LLM call with 15s debounce — all other tokens DROPPED (not queued).
Problem: 55+ tokens dropped per 200 signals, massive missed opportunities.

**Current design (3 parallel + queue 10):**
```
LLM_MAX_CONCURRENT = 3
LLM_QUEUE_MAX = 10
```

- 3 LLM calls run in parallel
- Overflow goes into FIFO queue (max 10)
- Queue items re-check filters before LLM call (position limits, cooldowns, dedup)
- Queue full → token dropped with log `[agent] LLM queue full`
- Function: `drainLlmQueue()` processes queue when slot frees
- Function: `processQueuedCandidate()` handles queued items with full pipeline

Log messages:
- `LLM busy (3/3), queued XXX... (queue: N)` = working correctly
- `LLM queue full (10), dropping XXX...` = overloaded, consider raising concurrent

## Profit Lock Confirm Delay

Config: `profit_lock_confirm_s` in strategy DB row (inside `config_json`)
- Was 45s, tuned to **15s**
- Purpose: avoid exit on brief wicks/dips
- At 5s check interval, 15s = 3 consecutive checks below floor before exit
- 45s was too long for meme coins — price can go from +15% to -10% in that time

To update:
```js
// In node REPL or script:
const row = db.prepare("SELECT config_json FROM strategies WHERE id = 'profit_lock'").get();
const config = JSON.parse(row.config_json);
config.profit_lock_confirm_s = 15;
db.prepare("UPDATE strategies SET config_json = ? WHERE id = 'profit_lock'").run(JSON.stringify(config));
```

## Route Blacklisting

File: `src/pipeline/candidateBuilder.js` in `filterCandidate()`

**Strategy-level config (preferred — May 2026):**
```js
// In filterCandidate(), before return:
if (Array.isArray(strat.blocked_routes) && strat.blocked_routes.length) {
  const route = candidate.signals?.route || candidate.signals?.label || null;
  if (route && strat.blocked_routes.includes(route)) {
    failures.push(`route blocked by /learn: ${route} (historical WR < threshold)`);
  }
}
```

Set `blocked_routes` array in strategy config_json:
```json
{
  "blocked_routes": ["graduated_trending", "fee_graduated_trending"]
}
```

**Data-driven route analysis (86 trades, May 2026):**
| Route | Trades | WR | Avg PnL | Action |
|-------|--------|-----|---------|--------|
| dual_source | 58 | 34% | +7.4% | ✅ Keep |
| fee_trending | 10 | 50% | +2.5% | ✅ Keep |
| graduated_trending | 15 | 13% | -16.9% | ❌ Block |
| fee_graduated_trending | 3 | 0% | -21.1% | ❌ Block |

**Legacy hardcoded approach (still works but less flexible):**
```js
const BLOCKED_ROUTES = ['smart_copy'];
```

## LLM Confidence Threshold vs Learning Lessons

**PITFALL:** The `llm_min_confidence` setting (DB) controls whether the system ACTS on a BUY verdict. But the LLM can self-impose a HIGHER threshold if a `learning_lessons` row tells it to.

**What happened:** A learning lesson said "Set minimum confidence ke 80+" — the LLM read this in `recent_lessons` and refused to give BUY verdicts below 80, even though DB threshold was 50. Result: zero entries for hours.

**Fix (three parts — ALL must be in sync):**
1. Retire/delete any learning lesson that sets a confidence threshold different from DB setting
2. Update `settings` table: `UPDATE settings SET value = '72' WHERE key = 'llm_min_confidence'`
3. Update strategy config_json: `config.llm_min_confidence = 72`
4. Update LLM prompt in `src/pipeline/llm.js` with explicit threshold instruction:
```
'IMPORTANT: The system threshold is 72. If your confidence >= 72 and verdict is BUY, the trade will execute. Do NOT apply your own higher threshold — use 72 as the bar.'
```

**CRITICAL: Three-place sync requirement:**
The confidence threshold is checked in THREE places that must all agree:
1. `settings` table (`llm_min_confidence` key) — used by orchestrator's `numSetting('llm_min_confidence', 75)` as fallback
2. `strategies.config_json` (`llm_min_confidence` field) — used by strategy-aware code
3. LLM system prompt in `src/pipeline/llm.js` — tells the LLM what threshold to use for its own scoring

If any one is out of sync, behavior is unpredictable. The orchestrator uses `numSetting()` which reads from settings table. The LLM uses whatever the prompt says. Always update all three together.

### PITFALL: Orchestrator ignored strategy-level confidence (upstream bug, May 2026)

Upstream Charon's `src/pipeline/orchestrator.js` (~line 90) hardcoded the global threshold read:
```js
// BUG: uses global setting (fallback 75), ignores strategy's per-strategy value
if (... && batchDecision.confidence >= numSetting('llm_min_confidence', 75)) {
```

Symptom: strategy config has `llm_min_confidence: 60`, settings table has `llm_min_confidence: 75`, LLM returns BUY with confidence 72. Expected: trade executes. Actual: `decision_logs.action = 'entry_not_approved'` with `guardrails.confidenceThreshold = 75`. No log line, no Telegram alert, position silently skipped.

**Fix (always apply on fresh clone):**
```js
const confidenceThreshold = Number(strat.llm_min_confidence) || numSetting('llm_min_confidence', 75);
if (selectedRow && boolSetting('agent_enabled', true) && batchDecision.verdict === 'BUY' && batchDecision.confidence >= confidenceThreshold) {
```

Also add an explicit skip log in the `else` branch so silent drops are visible:
```js
if (selectedRow && batchDecision.verdict === 'BUY' && batchDecision.confidence < confidenceThreshold) {
  console.log(`[agent] BUY skipped: confidence ${batchDecision.confidence} < threshold ${confidenceThreshold} (strategy ${strat.id}) ${selectedRow.candidate.token.mint.slice(0, 8)}...`);
}
```
And include `confidenceThreshold` + `confidence` in the `guardrails` payload of `logDecisionEvent` so `decision_logs` shows the actual values instead of the stale default.

**Diagnosis query** (when user reports "LLM said BUY but bot didn't buy"):
```js
db.prepare(`SELECT id, action, guardrails_json FROM decision_logs WHERE batch_id = ? ORDER BY id DESC`).all(batchId);
// If guardrails.confidenceThreshold > strategy's llm_min_confidence → this bug
```

**Root cause class:** Charon has several settings that live in both `settings` (global) and `strategies.config_json` (per-strategy). The orchestrator code was written assuming global-only. Same class of bug previously found for `max_open_positions`. Audit for others: grep `numSetting\(` in `src/pipeline/` and `src/execution/` — any setting that also exists in strategy config needs the `strat.X ?? numSetting(...)` pattern.

### PITFALL: LLM suggestion overrides strategy TP/SL (upstream bug, May 2026)

Upstream `src/db/positions.js` in both `createDryRunPosition()` and `createLivePosition()`:
```js
// BUG: LLM-suggested values take priority over user's strategy config
const tp = Number(decision.suggested_tp_percent || strat.tp_percent || numSetting('default_tp_percent', 50));
const sl = Number(decision.suggested_sl_percent || strat.sl_percent || numSetting('default_sl_percent', -25));
```

Symptom: user sets `ponyin_scalp` strategy with `tp_percent: 35, sl_percent: -25, partial_tp_at_percent: 35`. LLM returns a BUY with `suggested_tp_percent: 80, suggested_sl_percent: -30`. Position gets created with TP=80%/SL=-30% — partial_tp (fires at `tp_percent`) never triggers because price never reaches +80%, and trailing arm (which looks at `tp_percent`) is also misaligned.

User-visible sign: `/positions` shows `TP: +80.0% · SL: -30.0%` when the strategy is set to 35%/-25%. User will ask "kenapa TP 80%?"

**Fix (always apply on fresh clone; affects both dry-run and live position creation):**
```js
// Always honor strategy config — LLM suggestions are advisory only.
// Rationale: user explicitly set per-strategy TP/SL/trailing; LLM proposing different values
// breaks partial_tp wiring (partial fires at tp_percent) and trailing behavior.
const tp = Number(strat.tp_percent ?? decision.suggested_tp_percent ?? numSetting('default_tp_percent', 50));
const sl = Number(strat.sl_percent ?? decision.suggested_sl_percent ?? numSetting('default_sl_percent', -25));
```

Use `replace_all: true` when patching — the same two lines exist in `createDryRunPosition` and `createLivePosition`.

**Design rule:** LLM `suggested_tp_percent` / `suggested_sl_percent` are **advisory only**. The user's strategy config is the source of truth. This matches the "strategy config is sacred" pattern used for `position_size_sol`, `trailing_percent`, etc. — all strategy-controlled, never LLM-controlled.

### PITFALL: Changing strategy config doesn't migrate existing open positions

Strategy TP/SL/trailing values are **copied into the position row** at creation time (`dry_run_positions.tp_percent`, `.sl_percent`, `.trailing_percent`). When the user updates strategy config_json mid-session, already-open positions keep their old values until closed.

**Symptom:** User changes ponyin strategy from 60%/−25%/20% to 35%/−25%/35%. New positions use new values. Position #12 (opened 2 minutes earlier) still shows the old values in `/positions`.

**Fix migration SQL (run after strategy config change if open positions exist):**
```js
// Update both the position row AND the tp_sl_rules shadow row
db.prepare("UPDATE dry_run_positions SET tp_percent=?, sl_percent=?, trailing_percent=? WHERE id=? AND status='open'")
  .run(newTp, newSl, newTrail, positionId);
db.prepare('UPDATE tp_sl_rules SET tp_percent=?, sl_percent=?, trailing_percent=?, updated_at_ms=? WHERE position_id=?')
  .run(newTp, newSl, newTrail, Date.now(), positionId);
```

Always offer this migration to the user after changing strategy TP/SL/trailing if open positions exist.

**Bulk migration for exit strategy switch (trailing → profit lock or vice versa):**
```js
// When switching from trailing to profit lock:
db.prepare(`
  UPDATE dry_run_positions 
  SET tp_percent = 9999, sl_percent = -30,
      trailing_enabled = 0, trailing_percent = 0, trailing_armed = 0
  WHERE status = 'open'
`).run();

// When switching from profit lock to trailing:
db.prepare(`
  UPDATE dry_run_positions 
  SET tp_percent = 9999, sl_percent = -25,
      trailing_enabled = 1, trailing_percent = 35, trailing_armed = 0
  WHERE status = 'open'
`).run();
```

**Rule:** When user asks to switch exit strategy, ALWAYS check for open positions and migrate them. Otherwise they'll exit via the old strategy logic.

**Diagnosis pattern:** If Charon stops entering positions and LLM responses say "tidak ada kandidat yang memenuhi threshold confidence X+" where X > DB setting → check `learning_lessons WHERE status='active'` for conflicting lessons.

```js
// Check active lessons:
db.prepare("SELECT id, lesson FROM learning_lessons WHERE status='active'").all()
// Retire a bad lesson:
db.prepare("UPDATE learning_lessons SET status='retired' WHERE id = ?").run(lessonId)
```

**Rule:** Learning lessons should NEVER override numeric thresholds that are configurable in strategy config_json. Lessons are for qualitative guidance (route preferences, pattern recognition), not for overriding quantitative settings.

## LLM Prompt Engineering for Entry Signals

File: `src/pipeline/llm.js`

### Setup A/B/C Classification (May 2026 — preferred framing)

When the user asks for "more flexible" entry (dip OR momentum both OK), switch the LLM prompt to an explicit 3-setup decision tree. This is more robust than free-form "asymmetric opportunity" language because the model classifies first, then scores.

```
Setup A — DIP BUY
  • Fundamentals kuat (narasi viral, smart wallet masuk, fee claim aktif)
  • Jarak dari ATH 24h: -30% s/d -60% (diskon nyata, bukan dead)
  • Volume masih tinggi, 1h/6h trend masih naik meski 5m negatif
  • MC 5K-50K, liquidity > $5K
  • Asimetri: upside besar karena beli diskon

Setup B — MOMENTUM BUY
  • Trending, volume 5m positif, holder growth positif
  • Jarak dari ATH > -15% (belum top blast) atau baru break ATH
  • MC < 100K (belum macro top)
  • buy_volume > sell_volume (5m + 1h)
  • Smart/KOL wallet mulai masuk = konfirmasi
  • Ride wave sampai ATH break

Setup C — AVOID
  • Top blast: jarak ATH < -5%
  • Rug setup: bundler > 30%, top holder > 80%, bot_degen > 40%
  • Volume 5m drop >80%, momentum negatif semua timeframe
  • MC > 200K tanpa katalis
```

Output schema adds `setup: 'A|B|C'` field. LLM MUST start `reason` with "Setup A dip —" or "Setup B momentum —" so the classification is auditable in Telegram / dashboard.

### Legacy 4-signal framing (still documented for reference)

Earlier prompt versions used these signal names instead of Setup A/B/C:
1. **DIP BUY** — token down >20% from ATH, fundamentals intact. "3 Konfirmasi Candle": green candle, volume up, holders stable.
2. **MOMENTUM BUY** — near ATH but volume/holders still rising
3. **EARLY ENTRY** — new token $7K-$50K mcap, fast holder growth
4. **KOL SIGNAL** — renowned_count >= 3 (very strong, prioritized)

Signal strength hierarchy in prompt:
- KOL >= 3: VERY STRONG
- smart_degen_count >= 5: strong
- dual_source (multiple scanners): strong
- Combination of above: highest conviction
- Dex Paid/Boost aktif = sinyal kepercayaan pasar (dev invest marketing)

RED FLAGS (AVOID / PASS):
- **BUNDLE TOKEN:** Holder balance seragam (many wallets hold similar amounts) = dev bundling supply. Will dump.
- At ATH + volume down + holders flat = late entry
- Liquidity < $5K = rug risk (1 seller can crash 50%+)
- Dump >50% without recovery = dead cat
- Top holder >40% (non-bonding-curve) = whale can dump anytime
- Bot holders percentage >60% = fake volume, not organic
- Organic score "low" + high swaps = wash trading / bot manipulation
- Dev claimed large fees but token still micro cap = dev taking profit, not building

MARKET CAP TIER STRATEGY (from Ponyin):
- New Pair ($7K-$100K): Pure chaos. Fast entry, faster exit. Narrative > fundamentals. HIGHEST risk but highest reward.
- Micro Cap ($100K-$5M): Can start TA analysis. Find reversals, scalp entry.
- Charon trades ONLY in New Pair tier → prioritize speed, narrative, early signals.

HOLDER ANALYSIS:
- Holders rising fast (>50 in 5 min) = organic interest, bullish
- Holders flat/dropping while price rises = whale accumulating, retail leaving. Careful.
- Top 20 holders >60% (exclude bonding curve) = too concentrated, rug risk
- Many wallets with nearly identical balance = bundled wallets (RED FLAG)

**Removed:** `topBlastRisk` — contradicts momentum buy logic. Token near ATH is fine if momentum is strong.

### Ponyin Trading Intel Integration (May 2026)

Source: https://www.ponyin.id/ — Solana on-chain trading education (Indonesian)

Key concepts integrated into LLM prompt from Ponyin Vol. 1 & Vol. 2:
- **Bundle Token detection** — uniform holder balances = hidden supply monopoly
- **Global Fees** — low organic score + high swaps = wash trading
- **3 Konfirmasi Candle** — validates dip buy entries (green candle, volume up, holders stable)
- **Cabal Play awareness** — coordinated groups pushing price
- **Membaca Holder** — reading holder distribution for rug signals
- **Market Cap Tier** — different strategies per tier (we're in New Pair tier)
- **Dex Paid/Boost** — market confidence signal (dev investing in marketing)
- **Dev track record** — farmers deploying thousands of tokens = avoid

### @sambelikaan Trading Intel Integration (May 2026)

Source: @sambelikaan on X/Twitter — Indonesian Solana trader, scalping/LP focused

Key concepts integrated into LLM prompt:
- **Koreksi Sehat** — healthy pullback = price drops accompanied by green candles (not vertical dump). Valid dip buy signal.
- **Bundler Candle** — long red candle in first minute after launch = dev dumping bundled supply. RED FLAG.
- **SL+ concept** — after profit, move SL to breakeven/profit. Already implemented as trailing stop (arm at +35%, trail 15%).
- **KOL quality** — not all KOLs are equal. Good: holding >1h, PnL 30d green. Bad: pump & dump <5min hold.
- **Narasi belum terbentuk** — token just bonded but volume immediately drops = no narrative formed, don't entry.

**NOT integrated (human-only advice):**
- LP/DLMM settings (HawkFi presets) — not relevant to spot trading bot
- Psychology/money management — bot doesn't have emotions
- Bridge/swap tips — bot uses Jupiter directly
- "Kalo loss gimana" — bot follows rules, doesn't need motivation
- Chain preference — Charon is Solana-only by design

These are encoded directly in the LLM system prompt as structured rules the model evaluates against candidate data.

## KOL Integration

File: `src/signals/newPairs.js`

- Source: GMGN `/defi/quotation/v1/rank/sol/swaps/5m?orderby=renowned_count&direction=desc&limit=30`
- Route: `gmgn_kol`
- Pre-filter: `renowned_count >= 3` (skip noise from 1-2 KOL buys)
- Data field: `trendingKolCount` in candidate metrics (from `renowned_count`)
- LLM sees this field and knows to prioritize it

### KOL Quality Filtering (from @sambelikaan intel)

GMGN only provides `renowned_count` (number of KOLs buying), not individual KOL identities. Cannot whitelist/blacklist specific KOLs by name.

**LLM prompt tiering (current):**
- renowned_count >= 5: VERY STRONG signal, almost certain entry
- renowned_count 3-4: strong signal, but needs confirmation (volume, holders, narrative)

**Quality indicators taught to LLM:**
- Good KOL: holding time >1 hour, PnL 30 days full green
- Bad KOL (pump & dump): holding <5 minutes = red flag
- KOL signal alone (3-4 count) is NOT sufficient without other confirmation

**Source:** @sambelikaan tweet — "ikutin RC, jijo, cooker, sama gake (or cari yang holding time nya itu >1h pnl 30d full ijo)" / "asal jangan cupsey, cented, duval"

**Limitation:** Cannot implement per-KOL filtering without GMGN endpoint that returns individual KOL wallet addresses per token. The `renowned_count` is an aggregate number only.

## Stale Position Cleanup

File: `src/execution/positions.js` in `refreshPosition()`

Tokens that never pump after entry occupy slots and block new entries. Auto-close them.

**Rule:** If position open >10 minutes AND high water mark never reached +10% → exit as `STALE`.

```js
const STALE_AGE_MS = 10 * 60 * 1000; // 10 minutes
const STALE_MIN_HIGH_PCT = 10; // must have reached at least +10%
```

Why 10 min / 10%:
- Meme coins that will pump usually do so in first 5-10 minutes
- Tokens stuck at 0-5% after 10 min = no interest, dead volume
- TITTY (+1103%) pumped immediately — would never be caught by this rule
- Frees slots for new entries with actual momentum

Log: `[stale] pos 94 SCRL closed: 78min old, high was only +1.9%`

Exit reason stored as `STALE` in DB.

## Emergency Exit (Rug Detection)

File: `src/execution/positions.js` in profit lock section

**Problem:** Token pumps +45% then dumps to -20% in seconds. Confirm delay (15s) means bot waits while price crashes through the locked floor, exiting far below where it should.

**Solution:** If drop from high water mark to current PnL exceeds 30%, skip confirm delay and exit immediately.

```js
const dropFromHigh = highWaterPnl - pnlPercent;
if (dropFromHigh > 30) {
  exitReason = 'PROFIT_LOCK';  // emergency, no confirm delay
}
```

**Logic:**
- Normal dip (drop ≤30%): use confirm delay 15s (could be a wick)
- Rug pull (drop >30%): instant exit (this is not a wick, it's a dump)

**Example:** ALX — high +45%, current -20% = drop 65% → emergency exit immediately. Without this, bot waited 15s confirm and exited at -20% instead of catching it at +5-10%.

Log: `[profit_lock] pos 133 EMERGENCY exit: drop 65% from high (pnl -20.0%, floor +15%, high +45.5%)`

## Token Age Filter

Config: `token_age_max_ms` in strategy config_json
- Was 3600000 (60 min), then set to 0 (disabled), then re-enabled at **86400000 (24 hours)**
- Reason for 24h: filters out very old tokens that have no momentum, while still allowing dip buys on tokens launched within the last day
- Applied in `src/signals/serverClient.js` line ~112: checks `tokenAge > strat.token_age_max_ms`
- Tokens from GMGN scanner have `createdAt` field used for age calculation

## Minimum Swaps Filter

Config: `trending_min_swaps` in strategy config_json
- Was 0, set to **20**
- Only applies to tokens with `candidate.trending` data
- Tokens with <20 swaps in 5min window = dead or manipulated (1-2 people trading with themselves)
- TITTY had 159 swaps at entry — well above threshold
- Filters out ghost tokens that waste LLM calls

### PITFALL: Swaps=0 means "no data", not "zero swaps"

Many signal sources (signal server, axiom_trending) don't provide swaps data — the field defaults to 0. The original filter `trendingSwaps < 20` blocked ALL these tokens.

**Fix (src/pipeline/candidateBuilder.js):**
```js
// WRONG: blocks tokens with no swaps data (swaps=0)
if (strat.trending_min_swaps > 0 && trendingSwaps < strat.trending_min_swaps)

// CORRECT: only filter when swaps data actually exists
if (strat.trending_min_swaps > 0 && trendingSwaps > 0 && trendingSwaps < strat.trending_min_swaps)
```

**Symptom:** After setting min_swaps=20, logs show `trending swaps: 0 < 20` blocking everything — no new entries at all. The `> 0` guard lets tokens without swaps data pass through (they'll be evaluated by LLM on other metrics).

## Key Settings (current)

| Setting | Value | Location |
|---------|-------|----------|
| POSITION_CHECK_MS | 5000 | src/config.js |
| Fast price watch interval | 1000ms (ALL positions — SL + trailing) | src/monitor/fastPriceWatch.js |
| max_open_positions | 20 | settings table + strategy |
| LLM concurrent | 3 | orchestrator.js |
| LLM queue max | 10 | orchestrator.js |
| llm_min_confidence | 72 | settings table + strategy config_json + LLM prompt |
| min_holders | 60 | strategy config_json |
| min_mcap | 10000 | strategy config_json |
| max_mcap | 100000 | strategy config_json |
| SL | -25% | strategy config_json |
| TP | 999 (unlimited) | strategy config_json |
| trailing_enabled | true | strategy config_json |
| trailing_percent | 35 | strategy config_json |
| trailing_arm_percent | 35 | strategy config_json |
| max_hold_ms | 0 (disabled) | strategy config_json |
| use_profit_lock | false | strategy config_json |
| profit_lock_tiers | [] (empty/disabled) | strategy config_json |
| max_bundler_ratio | 0.6 (60%) | strategy config_json |
| max_bot_degen_rate | 0.25 (25%) | strategy config_json |
| max_sniper_ratio | 1.0 (disabled) | strategy config_json |
| min_elite_holder_count | 0 (disabled) | strategy config_json |
| min_smart_wallet_count | 0 (disabled) | strategy config_json |
| trending_min_swaps | 20 | strategy config_json |
| max_top20_holder_percent | 75 (single holder) | strategy config_json |
| position_size_sol | 0.05 | strategy config_json |
| token_age_min_ms | 0 (disabled) | strategy config_json |
| min_liquidity_usd | 8000 | strategy config_json |
| blocked_routes | [] (empty — LLM decides) | strategy config_json |
| Stale exit | >10min, high <10% | src/execution/positions.js |

## Max Single Holder Filter

Config: `max_top20_holder_percent` in strategy config_json
- Set to **50%** — blocks tokens where 1 wallet holds >50% of supply
- Despite the setting name ("top20"), the actual code checks `maxHolderPercent` (single largest wallet)
- File: `src/pipeline/candidateBuilder.js` line 88

**Data-driven decision (from 126 closed trades):**
- Winners avg max holder: varies (TITTY had 43.7% — just under threshold)
- Losers with max holder >50%: KOTO 72.5% (-95%), PVE 48.8% (-95%)
- Pattern: single wallet >50% = almost guaranteed rug dump

**Why 50% and not lower:**
- TITTY (best trade, +1103%) had max holder 43.7% — would be blocked at 45%
- Pump.fun tokens are naturally concentrated early — too strict kills moonshots
- 50% = "one wallet controls majority" threshold — they can dump at will

**Note:** `top20Percent` (total top 20 holders combined) is NOT a reliable filter for pump.fun tokens. TITTY had top20 = 79.4% but still pumped 1103%. New tokens are always concentrated — it's the SINGLE holder dominance that matters.

## GMGN Dev Status + Elite Smart Wallet Filter (May 2026)

File: `src/pipeline/candidateBuilder.js`

GMGN token payload already contains dev status and wallet-tag counts — no extra API call needed. Extract once into `candidate.gmgnInsights`, then filter + feed to LLM.

### Data extraction (add to `buildCandidate`)

```js
function extractGmgnInsights(gmgn) {
  if (!gmgn) return null;
  const dev = gmgn.dev || {};
  const stat = gmgn.stat || {};
  const tags = gmgn.wallet_tags_stat || {};
  const totalHolders = Number(gmgn.holder_count) || 0;
  const smartCount = Number(tags.smart_wallets) || 0;
  const renownedCount = Number(tags.renowned_wallets) || 0;
  const ratCount = Number(tags.rat_trader_wallets) || 0;
  const sniperCount = Number(tags.sniper_wallets) || 0;
  const bundlerCount = Number(tags.bundler_wallets) || 0;

  return {
    dev: {
      status: dev.creator_token_status || null,   // creator_close | creator_hold | creator_sell_part
      holdRate: Number(stat.creator_hold_rate) || 0,
      teamHoldRate: Number(stat.dev_team_hold_rate) || 0,
      closedAll: dev.creator_token_status === 'creator_close' && Number(stat.creator_hold_rate) === 0,
    },
    walletTags: {
      smart: smartCount,
      renowned: renownedCount,
      eliteCount: smartCount + renownedCount,
      ratRatio: totalHolders > 0 ? ratCount / totalHolders : 0,
      sniperRatio: totalHolders > 0 ? sniperCount / totalHolders : 0,
      bundlerRatio: totalHolders > 0 ? bundlerCount / totalHolders : 0,
    },
    botDegen: { rate: Number(stat.bot_degen_rate) || 0 },
    top10HolderRate: Number(stat.top_10_holder_rate) || 0,
    top70SniperHoldRate: Number(stat.top70_sniper_hold_rate) || 0,
  };
}
```

Attach `gmgnInsights: extractGmgnInsights(gmgn)` to the candidate object next to `ponyin`.

### Filters (in `filterCandidate`)

All opt-in — only active when strategy sets the field. Use `undefined`/`null` to disable.

```js
// DEV must have sold (reject creator_hold + unknown status)
if (strat.require_dev_sold === true) {
  if (insights.dev.status === 'creator_hold') failures.push('dev masih hold penuh');
  else if (!insights.dev.status) failures.push('dev status tidak diketahui');
}
if (strat.max_dev_hold_rate != null && insights.dev.holdRate > strat.max_dev_hold_rate) { ... }
if (strat.max_dev_team_hold_rate != null && insights.dev.teamHoldRate > strat.max_dev_team_hold_rate) { ... }

// ELITE smart wallet minimums
if (strat.min_elite_holder_count > 0 && insights.walletTags.eliteCount < strat.min_elite_holder_count) { ... }
if (strat.min_smart_wallet_count > 0 && insights.walletTags.smart < strat.min_smart_wallet_count) { ... }

// SCAM ratios
if (strat.max_rat_ratio > 0 && insights.walletTags.ratRatio > strat.max_rat_ratio) { ... }
if (strat.max_sniper_ratio > 0 && insights.walletTags.sniperRatio > strat.max_sniper_ratio) { ... }
if (strat.max_bot_degen_rate > 0 && insights.botDegen.rate > strat.max_bot_degen_rate) { ... }
```

### Strict-mode preset (the user preference, May 2026)

When the user asks for "very strict smart-wallet filter, only real WR-tinggi wallets":
```json
{
  "require_dev_sold": true,
  "max_dev_hold_rate": 0.02,
  "max_dev_team_hold_rate": 0.05,
  "min_elite_holder_count": 3,
  "min_smart_wallet_count": 2,
  "max_rat_ratio": 0.02,
  "max_sniper_ratio": 0.10,
  "max_bot_degen_rate": 0.30
}
```

This rejects ~95% of candidates. Expect 1-3 BUY per hour instead of 10+. If too tight (≤1 BUY / 2 hours), drop `min_elite_holder_count` to 2 and `min_smart_wallet_count` to 1.

### Feed insights to LLM

In `src/pipeline/llm.js` `compactCandidateForLlm()`, include:
```js
gmgnInsights: c.gmgnInsights ? {
  dev: c.gmgnInsights.dev,
  walletTags: c.gmgnInsights.walletTags,
  botDegen: c.gmgnInsights.botDegen,
  top10HolderRate: c.gmgnInsights.top10HolderRate,
  top70SniperHoldRate: c.gmgnInsights.top70SniperHoldRate,
} : null,
```

System prompt must teach the LLM how to read these fields. Key rules to encode:
- `eliteCount ≥ 3 + dev closed/sold` → STRONG BUY, confidence 75+
- `eliteCount = 0` → WATCH/PASS regardless of other metrics (no winners confirming)
- `dev.status === 'creator_hold'` + sparse elite → PASS (supply overhead + no confirmation)

### GMGN wallet-tag meanings (for user-facing explanation)

GMGN auto-tags wallets from on-chain history. When user asks "what is smart wallet / KOL / rat?":
- **Smart wallet** — consistent profit, WR 60%+, big cumulative ROI, proven 30d track record. Follow signal.
- **Renowned** — veteran trench wallet, not as famous as KOL but profit konsisten.
- **KOL** — doxxed influencer/caller (e.g. @Cented7, @Cupseyy). Post-purchase narrative = momentum trigger. Caution: KOL dump risk after pump.
- **Top** — rank top 100 leaderboard for 7d/30d PnL.
- **Fresh** — wallet <7d old, no history. Tangan lemah, dump cepat saat profit kecil.
- **Rat trader** — scam / pump-and-dump operator. Insider buy → sell to retail. If >5%, avoid.
- **Sniper** — bot beli block 1-3, dump <5min. If top70_sniper_hold_rate > 10%, dump wave incoming.
- **Bundler** — buys bundled at launch to hide insider concentration. If bundler_rate > 30%, classic rug setup.
- **Bot degen** — automated copy/wash trading. If rate > 30%, volume palsu, real demand kecil.
- **Whale** — >50 SOL active. Accumulating = bullish, distributing = bearish. Check context.
- **Entrapment** — sophisticated bait wallets (fake volume for retail trap).

## Bundler Rate Filter

Config: `trending_max_bundler_rate` in strategy config_json
- Was 0.5 (50%), tuned to **0.3 (30%)**
- Only applies to tokens with `candidate.trending` data (GMGN trending scanner)
- Tokens from signal server / new_pairs without bundler data bypass this filter
- Bundler rate >30% = nearly 1/3 of transactions are bundled (insider/bot coordinated pump-dump)
- Legitimate community tokens typically have bundler rate <20%
- TITTY (+1103%) had no bundler data (entered via different route) — unaffected by this filter

## GMGN API Cloudflare Blocks

GMGN OpenAPI (`openapi.gmgn.ai`) is protected by **Cloudflare managed challenge** (as of May 2026). This is NOT a simple JS challenge or Turnstile widget — it's an invisible managed challenge that blocks all automated access.

### What DOESN'T work (exhaustively tested May 2026)

| Approach | Result | Details |
|----------|--------|---------|
| Direct curl/axios + API key | 403 | Returns Cloudflare challenge HTML page |
| Puppeteer + stealth plugin | 403 | `puppeteer-extra-plugin-stealth` not enough |
| Rotating residential proxy (DataImpulse) | 403 | IP rotation doesn't help — fingerprint-based |
| Proxy + stealth combined | 403 | Still blocked |
| 2Captcha Turnstile solver | ERROR_BAD_PARAMETERS | Sitekey not exposed in managed challenge |
| 2Captcha direct API | ERROR_BAD_PARAMETERS | Default sitekey `0x4AAAAAAADnPIDROrmt1Wwj` rejected |
| Wait for JS challenge auto-solve | Empty response | Page shows "solved" but body is empty |

**Why ALL approaches fail:** GMGN uses Cloudflare's **managed challenge** mode (not Turnstile widget):
1. No visible captcha or sitekey in HTML — cannot extract for 2Captcha
2. Challenge is invisible JavaScript fingerprinting
3. Detects headless browser characteristics even with stealth
4. `cf_clearance` cookie never issued to automated browsers
5. Even when page appears "solved" (no "Just a moment"), response body is empty
6. IP-based blocking is secondary — same IP works in real browser, fails in Puppeteer

**Technical evidence from testing:**
```
Page length: 6061 (Cloudflare challenge HTML)
Sitekey match: not found
Has CF challenge: true
Iframes: [] (no Turnstile widget iframe)
```

After waiting 12s for "JS challenge auto-solve":
```
Response length: 0
Has CF: false (challenge page gone)
Preview: (empty)
```

The challenge "solves" but returns empty body — GMGN server-side still rejects the request.

### What DOES work

1. **Charon Signal Server** (`api.thecharon.xyz`) — **RECOMMENDED**
   - Aggregates GMGN data via their own bypass
   - Already includes: `axiom_trending`, `jupiter_trending`, `pump_graduated`, `fee_claim`
   - No additional setup needed — Charon already polls this

2. **GMGN enrichment in bot** (intermittent)
   - Uses Ed25519 signed requests (keys at `~/charon/keys/`)
   - Works ~50% of the time for individual token lookups
   - Good enough for enrichment, not reliable for bulk polling

3. **Capsolver** (not tested, likely to work)
   - Specialized Cloudflare managed challenge solver
   - Different from 2Captcha — uses browser automation + AI solving
   - Would require integration into bridge

### Files created for future bypass integration

```
src/bridge/gmgnBridge.js   — Puppeteer bridge with proxy + 2Captcha (needs Capsolver)
src/bridge/runBridge.js    — PM2 entry point
src/signals/gmgnSource.js  — GMGN signal polling (new pairs, trending, smart money)
```

**To enable GMGN direct polling (when Capsolver is integrated):**
1. Replace 2Captcha calls in `gmgnBridge.js` with Capsolver API
2. Start bridge: `pm2 start src/bridge/runBridge.js --name gmgn-bridge`
3. Uncomment GMGN polling in `src/app.js` (search for "GMGN direct polling")

### Current recommendation

**Use signal server.** Direct GMGN polling is not worth the complexity until Capsolver integration is done. Signal server already provides sufficient coverage.

### Fallback for manual token checks

DexScreener API (no auth, no Cloudflare):
```bash
curl -s "https://api.dexscreener.com/latest/dex/search?q=SYMBOL+solana" | node -e "
let d=''; process.stdin.on('data',c=>d+=c); process.stdin.on('end',()=>{
  const j=JSON.parse(d);
  const p = j.pairs?.filter(p => p.chainId === 'solana')?.slice(0,3);
  p?.forEach(x => console.log(x.baseToken.symbol, '| mcap $'+(x.marketCap/1000).toFixed(1)+'K | liq $'+(x.liquidity?.usd/1000).toFixed(1)+'K | 1h:', x.priceChange?.h1+'%'));
});"
```

**Limitation:** DexScreener lacks holder data, KOL data, bundler rate — only price/volume/liquidity.

## Debugging: Stale PM2 Logs

After `pm2 restart charon`, old log lines remain in the buffer. This causes confusion when verifying changes (old "throttled" or "max positions" messages appear post-restart).

Fix: `pm2 flush charon` before checking logs, then wait for fresh activity:
```bash
pm2 flush charon && sleep 30 && pm2 logs charon --lines 20 --nostream
```

## Performance Notes

- dual_source route = best performer (25% WR, avg +291% PnL)
- graduated_trending = second best (19% WR, avg +39%)
- smart_copy = worst (0% WR, blacklisted)
- Overall: ~12% WR but profitable due to asymmetric winners
- Sweet spot entry: mcap $7K-$86K via dual_source/graduated_trending

### Impact of Tuning Changes (measured)

Before tuning (73 trades): 12.3% WR, +1.15 SOL
After tuning (25 trades, 2h window): **24.0% WR**, +0.26 SOL
Post-emergency-exit (22 trades): **27.3% WR**, -0.13 SOL (negative due to PROFIT_LOCK-at-loss bug)
Post-confidence-fix (18 trades): **38.9% WR**, -0.09 SOL (profit lock wins all positive, SL still drags)
Post-trailing-switch: First results — BOOBWIF +174.3%, USA +15.7% via TRAILING_TP
Post-fast-SL-watcher (64 trades): **38% WR**, trailing wins +0.23 SOL (12 trades, 100% WR), SL avg -36% (pre-watcher positions dragging). After fast SL watcher expanded to ALL positions: first SL exit at -20.7% (football #228) — much closer to target.
Post-Ponyin+sambelikaan-intel (109 trades): **39% WR**, -0.025 SOL. Trailing exits 100% WR. SL avg improved to -22.3% with fast watcher. Strategy is near breakeven — needs 1-2 more moonshots to flip positive.

**Key insight from trailing data:** Trailing strategy is correct for meme coins. 12/12 trailing exits are profitable (avg +38%). The drag comes from SL losses exceeding -20% due to fast dumps. Fast SL watcher (1s for ALL positions) should reduce this going forward.

**Confidence threshold tuning:** Raised from 50 → 72 to reduce low-quality entries. Must be synced in 3 places (settings table, strategy config_json, LLM prompt).

**Since fast SL + confidence 72 (pos >= 212): +0.0853 SOL PROFIT** (19 trades, 42% WR). This subset proves the strategy works when all components are active together.

Key changes that drove improvement:
- 5s position check (tighter SL execution)
- 15s confirm delay (faster profit lock exit)
- 3 concurrent LLM (fewer missed opportunities)
- Dip/momentum/KOL prompt (better entry selection)
- Route blacklist (eliminated 0% WR smart_copy drain)
- LLM confidence fix (retired conflicting lesson, added explicit threshold in prompt)
- **Trailing stop switch** (let winners run instead of capping at floor)

### Min Holders Consideration

TITTY (best trade, +1103%) had **109 holders** at entry with mcap $11.3K. Setting min_holders to 50 is safe for lowcap — filters out pump-and-dump tokens (5-20 holders) while keeping legitimate early-stage tokens. Tokens at $10-50K mcap with <50 holders are usually single-wallet manipulation.

### Entry Mcap Analysis (from 126 closed trades)

**< $15K mcap:** 8 trades, 12.5% WR, +0.43 SOL total
- 7 losses (mostly SL with heavy slip: -41%, -46%, -80%)
- 1 massive winner: TITTY +1103% (+0.55 SOL) — covers all losses
- Higher variance, lower WR, but asymmetric upside

**≥ $15K mcap:** 118 trades, 18.6% WR, +0.87 SOL total
- More consistent, less slippage on exits
- Winners smaller but more frequent

**Data-driven MCAP bucket analysis (86 trades, May 2026):**
| Bucket | Trades | WR | Avg PnL | Recommendation |
|--------|--------|-----|---------|----------------|
| <$10K | 15 | **0%** | -25.6% | ❌ Skip — pure rug zone |
| $10-30K | 17 | 35% | +4.2% | ✅ Keep |
| $30-60K | 14 | 29% | -13.6% | ⚠️ Marginal |
| $60-100K | 13 | 38% | +10.4% | ✅ Keep |
| >$100K | 27 | 44% | +18.6% | ✅ Best bucket |

**Action taken:** Raised `min_mcap_usd` from $3K to **$10K** based on 0% WR in <$10K bucket.

**Conclusion:** Keep min_mcap at $7K for 0.05 SOL position size. The moonshot potential at low mcap outweighs the lower WR. Only raise min_mcap if increasing position size above 0.05 SOL.

## Telegram Display

File: `src/telegram/format.js` in `formatPosition()`

- PnL shows both percent AND SOL value: `🟢 PnL: +1020.1% (0.5100 SOL)`
- Exit line also shows SOL: `🏁 Exit: SL at $23.7K (-42.5% · -0.0213 SOL)`
- Formula: `position.size_sol * pnl / 100` for open positions
- Closed positions use `position.pnl_sol` field directly

### Indonesian-language UI + SOL-first PnL display (the user preference)

User explicitly wants:
- All Telegram messages in **Bahasa Indonesia** (verdict labels, headers, status, exit reasons)
- **PnL in SOL is the primary metric**, percent is secondary — every PnL line shows SOL absolute first
- Block-style layout (📥 Entry / 💵 PnL / 🎯 Target & Stop / ⏱ Durasi) instead of single dense line
- Compact 1-line view for `/positions` lists, full block view for individual position detail
- **Total PnL summary** at bottom of every screening and position notification

**Implementation (May 2026):** Full Indonesian UI implemented in `src/telegram/format.js` and `src/telegram/send.js`:

**Key files modified:**
- `src/telegram/format.js` — all display functions rewritten with Indonesian labels + emoji
- `src/telegram/send.js` — notification messages use Indonesian labels

**Screening batch message structure:**
```
🧭 <b>Screening Charon</b>

📦 Batch: <b>#79</b> · Discan: <b>10</b> kandidat

🎯 Pemicu: <token line>
✅ Pilihan: <token line>  OR  ❌ Pilihan: <b>tidak ada</b>

🤖 Keputusan: <b>BUY/WATCH/PASS</b> 72.0%
💭 Alasan: <Indonesian reason from LLM>

━━━━━━━━━━━━━━━━━━━━
📊 Total PnL: <b>+0.0069 SOL</b>
📂 Posisi terbuka: <b>4</b> (0.20 SOL)
```

**Position card structure:**
```
🟢 <b>SYMBOL</b> #13

🪙 Token: <link>
📊 Status: <b>TERBUKA/TERTUTUP</b>
⚙️ Mode: <b>DRY RUN/LIVE</b> · Strategi: <b>degen</b>

💰 Entry: $77.6K mcap
📈 High: $85.2K mcap
💵 Size: <b>0.05 SOL</b>

🟢 PnL: <b>+28.9%</b> (<b>+0.0145 SOL</b>)

🎯 TP: +30.0% · SL: -15.0%
📉 Trailing: 5.0% 🔥 AKTIF / ⏳ standby / ❌ off

━━━━━━━━━━━━━━━━━━━━
📊 Total PnL: <b>+0.0069 SOL</b>
📂 Posisi terbuka: <b>4</b>
```

**Helper functions added to format.js:**
```js
// Get total realized PnL from DB
function getTotalRealizedPnl() {
  const result = db.prepare(`
    SELECT COALESCE(SUM(pnl_sol), 0) as total_pnl_sol
    FROM dry_run_positions WHERE status = 'closed'
  `).get();
  return result?.total_pnl_sol || 0;
}

// Get open positions stats
function getOpenStats() {
  const result = db.prepare(`
    SELECT COUNT(*) as count, COALESCE(SUM(size_sol), 0) as total_size
    FROM dry_run_positions WHERE status = 'open'
  `).get();
  return { count: result?.count || 0, totalSize: result?.total_size || 0 };
}
```

**Emoji conventions:**
- 🧭 Screening header
- 📦 Batch info
- 🎯 Trigger/TP target
- ✅ Selected / ❌ None selected
- 🤖 LLM decision
- 💭 Reason
- 🟢/🔴 Profit/Loss indicators
- 🟡 Open position status
- 📊 Stats/PnL summary
- 📂 Open positions count
- 💰 Entry price
- 📈 High water mark
- 💵 Size/money
- 📉 Trailing stop
- 🔥 Trailing armed
- ⏳ Trailing standby
- ━━━ Section divider

**Exit notification structure:**
```
🟢 <b>DRY RUN EXIT: TRAILING_TP</b>

<full position card with exit details>
```

**Verdict label map (use everywhere a verdict is displayed):**
```js
const verdictLabel = { BUY: '🟢 BELI', WATCH: '🟡 PANTAU', PASS: '🔴 LEWATI' };
```

**Exit reason label map:**
```js
const map = {
  TP: '🎯 Take Profit', SL: '🛑 Stop Loss',
  TRAILING_TP: '📉 Trailing Stop', PARTIAL_TP: '💰 Partial TP',
  MAX_HOLD: '⏰ Max Hold', MANUAL: '✋ Manual', LLM_EXIT: '🤖 LLM Exit',
};
```

**Status badge map:** `dry_run` → `🧪 DRY-RUN`, `confirm` → `🟡 CONFIRM`, `live` → `🔴 LIVE`. Apply in main menu header, position cards, and BUY/EXIT alert headers.

**Required helpers in `src/telegram/format.js`** (define once, reuse):
- `fmtSolSigned(value)` → `+0.0059` / `-0.0320` (always signed, 4 decimals)
- `fmtPctSigned(value)` → `+11.9%` / `-25.3%` (always signed, 1 decimal)
- `pnlEmoji(n)` → 🟢 (>0), ⚪ (≈0), 🔴 (<0)
- `holdDurationText(openedMs, closedMs)` → `35m` / `1j 14m` / `34d`
- `tokenAgeText(createdAtMs)` → `4 jam` / `35 menit`
- `formatPositionCompact(position)` → 1-liner: `🟢 🧪 <b>SYM</b> #11 · <b>+0.0059 SOL</b> (+11.9%) · 35m`
- `formatPosition(position)` → full block view with PnL absolute (SOL) AND percent on every line, Target & Stop showing both `+60.0%` and `≈ +0.0300 SOL`
- `getTotalRealizedPnl()` → queries DB for sum of closed position pnl_sol
- `getOpenStats()` → queries DB for open position count and total size

**DB helper functions for format.js (May 2026):**
```js
import { db } from '../db/connection.js';

// Get total realized PnL from DB
function getTotalRealizedPnl() {
  const result = db.prepare(`
    SELECT COALESCE(SUM(pnl_sol), 0) as total_pnl_sol
    FROM dry_run_positions WHERE status = 'closed'
  `).get();
  return result?.total_pnl_sol || 0;
}

// Get open positions stats
function getOpenStats() {
  const result = db.prepare(`
    SELECT COUNT(*) as count, COALESCE(SUM(size_sol), 0) as total_size
    FROM dry_run_positions WHERE status = 'open'
  `).get();
  return { count: result?.count || 0, totalSize: result?.total_size || 0 };
}
```

These helpers enable showing total PnL summary at the bottom of every screening and position notification.

**Portfolio summary (for `/menu` and `/positions`):** must always include:
- Open count + max
- Unrealized SOL (sum of `size_sol × (high_water/entry - 1)`)
- Closed count + win rate
- Realized SOL (sum of `pnl_sol`)
- **Total PnL in SOL** as the headline number

**LLM reason/risks language:** system prompt in `src/pipeline/llm.js` must instruct the model to write `reason` and `risks` in Bahasa Indonesia, keeping technical trading terms (MC, ATH, TP, SL, holder, liquidity, rug, dev) in their original form. Schema descriptions also Indonesian: `'penjelasan singkat keputusan dalam Bahasa Indonesia (1-3 kalimat)'`.

**Full Indonesian system prompt example (May 2026):**
```js
const system = [
  'Kamu adalah bot screening token. Jawab dalam JSON saja.',
  'Gunakan bahasa Indonesia untuk field "reason" dan "risks".',
  'Screen kandidat dengan flags ini (nilai dalam persen 0-100):',
  'Flag1: freshWalletRate > 30 (terlalu banyak wallet baru)',
  'Flag2: top10HolderRate > 50 ATAU maxHolderPercent > 20 (konsentrasi tinggi)',
  'Flag3: bundlerPct > 10 ATAU botDegenRate > 30 (banyak bot/bundler)',
  'Flag4: migrationMC > 0 DAN marketCapUsd > migrationMC * 10 (entry terlambat)',
  'Aturan: 0-1 flag = BUY, 2+ flag = PASS.',
  'Positif: smartWallets > 50 (bagus), distanceFromAthPct < -10 (beli di dip).',
  'Return JSON: {verdict, selected_id, confidence, reason}',
].join(' ');
const user = {
  task: 'Pilih kandidat terbaik untuk dry-run buy dari batch ini, atau pilih tidak ada jika tidak layak.',
  // ... rest of user object
};
```

When the user complains about Telegram output being "too plain" or "berantakan", the answer is almost always: switch from inline `·`-separated lines to block sections with emoji headers, and surface SOL absolutes alongside every percent.

### Telegram Message Length Limit (4096 chars)

File: `src/telegram/menus.js` — `positionsOpenText()` and `positionsClosedText()`

**Problem:** With 10+ positions, `formatPosition()` (full detail per position) exceeds Telegram's 4096 char limit → `ETELEGRAM: 400 Bad Request: message is too long`

**Solution:** Compact list view — 1 line per position:
```
🟢 TITTY #85 · +1020.1% (0.5100 SOL) · mcap $11.3K
🔴 MUSK #83 · -5.2% (-0.0026 SOL) · mcap $72.3K
```

Plus summary footer (unrealized total for open, W/L stats for closed). Full `formatPosition()` still used for individual position view (callback `pos:ID`).

### Telegram `/positions` Command Fix

File: `src/telegram/commands.js` — `sendPositions()`

Original code used `formatPosition()` for 12 positions → message too long. Fixed to use same compact view as menu:
```js
export async function sendPositions(chatId) {
  const { positionsText, positionsKeyboard } = await import('./menus.js');
  await bot.sendMessage(chatId, positionsText(), { parse_mode: 'HTML', disable_web_page_preview: true, ...positionsKeyboard() });
}
```

This shows the summary view with Open/Closed buttons, same as inline menu callback.

### Compact `positionsText()` Implementation (May 2026)

File: `src/telegram/menus.js`

### PITFALL: `positionsText()` totals accidentally used only the preview rows

After compacting the Positions menu, an easy regression is to compute `Total PnL`, `Win/Loss`, and open/closed counts from the same limited preview array (for example `allPositions(12)`). That makes the header wrong whenever total history exceeds the preview window — e.g. header says `3W / 8L` while the database actually has `11W / 24L`.

**Correct pattern:**
- Use dedicated aggregate SQL over the full `dry_run_positions` table for totals.
- Use separate limited queries only for the preview lists.

```js
const openRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status='open' ORDER BY opened_at_ms DESC LIMIT 6`).all();
const closedRows = db.prepare(`SELECT * FROM dry_run_positions WHERE status='closed' ORDER BY closed_at_ms DESC LIMIT 6`).all();
const totals = db.prepare(`
  SELECT
    COALESCE(SUM(CASE WHEN status='closed' THEN pnl_sol ELSE 0 END), 0) AS total_pnl,
    SUM(CASE WHEN status='closed' AND pnl_sol > 0 THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN status='closed' AND pnl_sol < 0 THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN status='closed' THEN 1 ELSE 0 END) AS closed_count,
    SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_count
  FROM dry_run_positions
`).get();
```

Rule: *summary header from full-table aggregates, list body from preview rows.*

### PITFALL: `menu:pnl` callback imported `sendPnl` from the wrong module

If `/pnl` works as a slash command but the inline menu button `menu:pnl` fails with `sendPnl is not a function`, check `src/telegram/callbacks.js`.

**Root cause:** `sendPnl()` lives in `src/telegram/commands.js`, but a refactor imported it dynamically from `./send.js`.

**Fix:**
```js
// callbacks.js
import { sendPnl } from './commands.js';
...
if (data === 'menu:pnl') return sendPnl(chatId, query);
```

Also export the function in `commands.js`:
```js
export async function sendPnl(chatId, query = null) { ... }
```

**Problem:** Original `positionsText()` used full `formatPosition()` for each position → 12 positions = 6091 chars, exceeds Telegram 4096 limit → callback fails silently.

**Solution:** Compact summary view with 1-line per position:
```js
export function positionsText() {
  const rows = allPositions(12);
  if (!rows.length) return '📍 <b>Posisi</b>\n\nBelum ada posisi.';
  
  // Get totals
  const open = rows.filter(r => r.status === 'open');
  const closed = rows.filter(r => r.status === 'closed');
  const totalPnl = closed.reduce((sum, r) => sum + (r.pnl_sol || 0), 0);
  const wins = closed.filter(r => (r.pnl_sol || 0) > 0).length;
  const losses = closed.filter(r => (r.pnl_sol || 0) < 0).length;
  
  const lines = [
    '📍 <b>Posisi</b>',
    '',
    `📊 Total PnL: <b>${totalPnl >= 0 ? '+' : ''}${fmtSol(totalPnl)} SOL</b>`,
    `📈 Win/Loss: <b>${wins}W / ${losses}L</b>`,
    `📂 Terbuka: <b>${open.length}</b> · Tertutup: <b>${closed.length}</b>`,
    '',
    '━━━ TERBUKA ━━━',
    ...open.map(p => {
      const pnl = p.high_water_mcap && p.entry_mcap 
        ? ((p.high_water_mcap / p.entry_mcap) - 1) * 100 
        : 0;
      const emoji = pnl >= 0 ? '🟢' : '🔴';
      return `${emoji} <b>${escapeHtml(p.symbol || short(p.mint))}</b> · ${fmtUsd(p.entry_mcap)} · ${pnl >= 0 ? '+' : ''}${fmtPct(pnl)}`;
    }),
    '',
    '━━━ TERTUTUP ━━━',
    ...closed.slice(0, 6).map(p => {
      const emoji = (p.pnl_sol || 0) >= 0 ? '🟢' : '🔴';
      const pnlSol = p.pnl_sol || 0;
      return `${emoji} <b>${escapeHtml(p.symbol || short(p.mint))}</b> · ${p.exit_reason} · ${pnlSol >= 0 ? '+' : ''}${fmtSol(pnlSol)} SOL`;
    }),
  ];
  
  return lines.filter(Boolean).join('\n');
}
```

**Result:** 480 chars (well under 4096 limit). Menu callback now works.

## Re-Entry Logic (hasMintPosition)

File: `src/db/positions.js` line 13

```js
export function hasMintPosition(mint) {
  const oneHourAgo = Date.now() - 60 * 60 * 1000;
  const existing = db.prepare(
    "SELECT id FROM dry_run_positions WHERE mint = ? AND (status = 'open' OR (status = 'closed' AND closed_at_ms > ?))"
  ).get(mint, oneHourAgo);
  return !!existing;
}
```

**Behavior:**
- Token with open position → blocked (no duplicate entry)
- Token closed < 1 hour ago → blocked (cooldown)
- Token closed > 1 hour ago → **allowed to re-enter** (both profit exits and SL exits)
- SL cooldown (`slCooldownMap` in orchestrator.js) is a SEPARATE 1-hour block on top of this

**So re-entry is possible** for tokens that previously profited, as long as:
1. Position is closed
2. More than 1 hour has passed since close
3. Token still passes all filters (mcap, holders, etc.)
4. Token appears again in signal flow (scanner picks it up again)

**Common reason re-entry doesn't happen:** Token pumped past max_mcap ($100K) — even if it dips back, it needs to be below max_mcap AND appear in signal sources again.

## Strategy: Trailing Stop (current — replaced Profit Lock)

> ⚠️ **VERIFY BEFORE TRUSTING:** The profit-lock sections in this playbook describe a feature from a different fork. The current Charon at `~/charon` (May 2026) has **no code that reads `use_profit_lock` or `profit_lock_tiers`**. `grep -rn "profit_lock" src/` returns zero. Before configuring profit lock for the user, confirm the feature is implemented. See `references/entry-exit-logic-notes.md` → "PITFALL: Configuring strategy fields that the code doesn't read".

**Decision date:** May 2026
**Data-driven switch:** Backtested 42 closed trades. Profit lock averaged +9.1% wins but -16.6% losses (net negative). Fixed TP 35% simulated +0.067 SOL. Trailing 15% from high simulated **+4.1 SOL** on moonshot tokens.

**Why trailing beats profit lock for meme coins:**
- Profit lock exits at floor (e.g., +5%) even when token is still pumping → caps upside
- Trailing lets winners run: TITTY +2808% → trailing exit ~+2387%, vs profit lock exit at +700%
- Meme coins are asymmetric: 90% lose, 10% moon. You NEED the full moon to cover losses.

**Current config (May 2026 — user-confirmed preferences):**
```json
{
  "tp_percent": 999,
  "sl_percent": -25,
  "trailing_enabled": true,
  "trailing_percent": 35,
  "trailing_arm_percent": 35,
  "max_hold_ms": 0,
  "use_profit_lock": false,
  "profit_lock_tiers": []
}
```

**User-stated preferences (the user, May 2026):**
- **TP unlimited:** "tp percent kan unlimited bro, pakai trailing stop aja" — set `tp_percent: 999` (effectively infinite), let trailing handle exits
- **Trailing 35%:** "trailing exit nya di 35%" — drop 35% from peak triggers exit
- **No max hold:** "max hold durasi ga perlu ada kecuali emang token tersebut stuck" — set `max_hold_ms: 0` (disabled)
- Exit logic is purely: partial TP at +35% (sell 40%), then trailing 35% from peak, or SL -25%

**Rationale for SL -25% and trailing 35%:**
- Meme coins are extremely volatile — normal pullbacks of 20-25% happen constantly before pumping again
- Trailing 35% gives tokens room to "breathe" — smaller drops from high are normal meme coin volatility, not a reversal signal
- Combined: fewer premature exits, let winners run further
- Max hold disabled: if token is moving (up or down), trailing/SL will handle it; time-based exit only makes sense for truly stuck positions

**How trailing works:**
1. Token enters, SL at -35%
2. Token pumps — high water mark tracked every check
3. When high water PnL reaches **+35%** → trailing ARMED
4. Once armed: if price drops **30%** from high water mark → exit as `TRAILING_TP`
5. If token keeps pumping, trailing follows (never exits while going up)

**Example outcomes:**
- Token pumps +35%, then drops 30% from high → exit at ~+0% (breakeven-ish)
- Token pumps +100%, then drops 30% from high → exit at ~+70% ✅
- Token pumps +500%, then drops 30% from high → exit at ~+350% ✅
- Token pumps +3000%, then drops 30% from high → exit at ~+2100% ✅
- Token pumps +30% (never reaches +35%) → stale exit or SL (trailing never arms)

**Code location:**
- Trailing arm logic: `src/execution/positions.js` line ~133
- `trailing_arm_percent` field in strategy config_json (custom, not standard Charon)
- Standard monitor checks: `highWaterPnl >= trailingArmPct` (uses high water, not current pnl)
- Fast watcher also handles trailing (1s polling for armed positions)

**Key code change (trailing arm at custom threshold, not TP):**
```js
// OLD: trailing armed only when TP hit (useless with TP=9999)
const trailingArmed = position.trailing_armed || (position.trailing_enabled && tpHit);

// NEW: trailing arms at trailing_arm_percent from strategy config
const trailingArmPct = Number(strat?.trailing_arm_percent || position.tp_percent);
const highWaterPnl = (highWaterMcap / Number(position.entry_mcap) - 1) * 100;
const trailingArmed = position.trailing_armed || (position.trailing_enabled && highWaterPnl >= trailingArmPct);
```

**Positions that never reach +35%:**
- Handled by stale exit (>10min, high <10%) or SL (-20%)
- No trailing involvement — they exit via standard mechanisms
- This is fine: tokens that can't pump 35% aren't moonshots anyway

## Fast Price Watcher (1s SL + Trailing Monitor)

File: `src/monitor/fastPriceWatch.js`
Integrated in: `src/app.js` (imported and started after position monitor)
Coordination: `src/execution/positions.js` exports `fastWatchedPositions` Set

**Purpose:** Monitor ALL open positions every 1 second for both SL and trailing stop. Standard 5s monitor is too slow for meme coin rugs — tokens can dump 50-90% between 5s checks, causing SL exits at -50% instead of -20%.

**What it watches:** ALL open positions (SL + trailing)

**Architecture:**
```
Standard Monitor (5s) → stale exit, max hold, high water updates (SL/trailing delegated to fast watcher)
Fast Watcher (1s)    → SL detection + trailing stop for ALL open positions
```

**How it works:**
1. Every 1s, queries ALL open positions (no filter — watches everything)
2. Batch-fetches prices from `https://lite-api.jup.ag/price/v3?ids=mint1,mint2,...` (up to 20 mints)
3. Calculates mcap from price ratio: `currentMcap = entry_mcap * (currentPrice / entry_price)`
4. **SL check:** if pnlPercent <= sl_percent → exit as `SL` (+ records SL cooldown)
5. **Trailing check:** if trailing armed AND drop from high > trailing_percent → exit as `TRAILING_TP`
6. On exit: closes position in DB, sends Telegram notification, records trade

**Coordination with standard monitor:**
- Fast watcher registers ALL position IDs in `fastWatchedPositions` Set (exported from `src/execution/positions.js`)
- Standard monitor skips SL AND trailing for positions in this set
- Standard monitor still handles: stale exit, max hold
- No double-exit risk: closed positions don't appear in `openPositions()` query

**Log prefix:** `[fast-watch]`
- `[fast-watch] pos 208 FREAKO SL HIT: pnl -20.3% <= -20%`
- `[fast-watch] pos 97 USA trailing ARMED at +67.7%`
- `[fast-watch] pos 97 USA TRAILING EXIT: drop -31.0% from high (pnl +15.7%, high +67.7%)`

**Real results:**
- BOOBWIF #160: high +65.9% → trailing exit at **+174.3%** (pumped more after arm, then dropped 15%)
- USA #97: high +67.7% → trailing exit at +15.7% (was already declining when watcher started)

**Why ALL positions (not just trailing-armed):**
Before this change, SL was only checked every 5s by standard monitor. Data showed 13 trades with SL exit worse than -25% (some as bad as -93%). Token pump.fun rugs dump 50-90% in <5 seconds. With 1s polling, SL detection catches dumps much closer to the -20% threshold.

**API rate consideration:** Jupiter price API handles batch requests well. 20 mints per request, 1 request/second = very light load. If positions exceed 20, only first 20 get fast-watched (BATCH_SIZE limit).

**To disable:** Remove `startFastPriceWatch()` call in `src/app.js`

## SL Slippage Problem (Pump.fun Token Rugs)

**Problem:** SL set at -20% but actual exit PnL is -35% to -93%. This is the #1 source of losses.

**Root cause:** Pump.fun tokens can dump 50-90% in seconds (dev sell, rug pull, liquidity removal). Between check intervals, price crashes far past the SL threshold.

**Data (from 17 SL exits worse than -25%):**
- JINWOO: $28.7K → $2.0K in 83 seconds (-93%)
- Tom: $23.8K → $11.0K in 406 seconds (-53%)
- FREAKO: $46.8K → $23.2K in 303 seconds (-50%)
- LITESVM: $11.1K → $6.2K in 2632 seconds (-44%)

**Pattern:** Low liquidity tokens ($5-10K liq) are most vulnerable. One large sell can crash price 50%+ instantly.

**Mitigation timeline:**
1. ~~5s position check~~ (original) — too slow, SL exits at -40% to -93%
2. ~~Fast watcher for trailing-armed only~~ — helped trailing but SL still on 5s cycle
3. **Fast watcher for ALL positions (1s)** — current. SL detected within 1s of breach.

**Remaining limitation:** Even at 1s polling, a token can dump 30%+ in <1 second (single large sell tx). In live mode, additional slippage from swap execution adds 5-10% on top. This is inherent to pump.fun meme coins — cannot be fully eliminated.

**Potential future mitigations:**
- Min liquidity filter ($10K) — tokens with <$10K liq are most vulnerable to single-seller crashes
- Solana websocket account subscription — react to on-chain events in <100ms (complex to implement)
- Smaller position size for low-liq tokens — reduce absolute loss per rug

**Impact on strategy math:**
- With SL at -35%: need 1 win of +175% per 5 losses to breakeven
- Trailing avg win is +38-83% — need occasional moonshots (+200%+) to be profitable
- Fast SL watcher ensures actual exit is close to -35% (not -50% or -90%)
- Wider SL means fewer total SL exits (tokens that pull back 20-30% then pump won't get stopped out)

**Measured improvement (after fast SL for ALL positions):**
- Before: SL avg -36.4% (19 trades, pos 140-211)
- After: SL avg -22.3% (first 2 trades post-change: -24.0%, -20.7%)
- Improvement: ~14% less slippage per SL exit

**Latest tuning (May 2026 — fresh start):**
- SL widened from -20% to **-35%** — meme coins pull back 20-25% routinely before pumping. Tighter SL caused premature exits.
- Trailing drop widened from 15% to **30%** — 15% drop from high is normal meme coin volatility, not a reversal.
- All positions and trades cleared for clean measurement from new settings.
- Ponyin + @sambelikaan trading intel integrated into LLM prompt (bundle detection, koreksi sehat, bundler candle, KOL quality tiering).

## KNOWN BEHAVIOR: PROFIT_LOCK Exit at Negative PnL

**Root cause (confirmed, not a bug):** Token pumps briefly (reaching a profit lock tier), then dumps faster than the check interval. Example: APSX pumped to +88% (tier +80%→floor +40% activated), then rugged to -80% within 5 seconds. Next check sees pnl=-79.9%, drop from high=167% → emergency exit fires.

**Why it happens:**
1. Token reaches tier threshold (e.g., +88% → tier +80% activates, floor = +40%)
2. Token dumps catastrophically between checks (5s interval, or 1s with fast watcher)
3. Next price check: pnl is already far below floor AND below entry
4. Emergency exit (drop >30%) fires with reason 'PROFIT_LOCK'
5. Exit price = current (already crashed) price, not the floor price

**Mitigation (implemented):** Fast Price Watcher (1s polling) significantly reduces the window. Instead of 5s gap, now only 1s gap for tier-active positions. APSX-style rugs (-80% in <5s) may still exit negative, but less severe (catch at -20% to -40% instead of -80%).

**Impact on analysis:** When filtering by exit_reason to evaluate profit lock performance, these emergency-at-loss exits pollute the data. PROFIT_LOCK shows 2/8 wins but 3 of the "losses" are actually emergency rug exits, not profit lock failures.

**TODO (nice-to-have):** Separate exit reasons — `PROFIT_LOCK` for genuine floor exits, `EMERGENCY` for >30% drop exits. This is a code change in `src/execution/positions.js` line ~169.

## Profit Lock Tiers — Design Principles

- Tiers should be granular at high percentages (meme coins can 10-100x)
- Gap between tiers shouldn't exceed 2x (e.g., don't jump from 1000% to 5000% without intermediate)
- Floor should lock ~65-80% of the tier threshold (enough room for volatility but captures most profit)
- Current full tier set: 20→5, 40→15, 80→40, 150→90, 300→200, 500→350, 1000→700, 1500→1000, 2000→1500, 3000→2500, 5000→4000, 10000→8000
- To add tiers: update `profit_lock_tiers` array in strategy `config_json` — no restart needed, read from DB each check cycle

## Live-Mode Readiness Assessment (when user asks "boleh masuk live?")

When the user asks whether they can switch from `dry_run` to `live`, run this assessment before saying yes. Do not just look at total PnL.

**SQL queries to run:**

```sql
-- Realized stats (last 12h)
SELECT count(*) total, sum(pnl_sol > 0) wins, sum(pnl_sol < 0) losses,
       round(sum(pnl_sol),4) total_pnl,
       round(avg(case when pnl_sol > 0 then pnl_percent end),2) avg_win_pct,
       round(avg(case when pnl_sol < 0 then pnl_percent end),2) avg_loss_pct
FROM dry_run_positions
WHERE status='closed' AND closed_at_ms > strftime('%s','now')*1000 - 12*3600*1000;

-- Unrealized peak (open positions at high water)
SELECT round(sum(size_sol * (high_water_mcap/entry_mcap - 1)), 4)
FROM dry_run_positions WHERE status='open' AND entry_mcap > 0;

-- All-time baseline
SELECT count(*) total, sum(pnl_sol>0) wins, round(sum(pnl_sol),4) pnl_all
FROM dry_run_positions WHERE status='closed';
```

**Decision framework (conservative):**

- WR < 30% all-time → not yet, even if 12h is profitable
- WR 30-50% AND R:R (avg_win / |avg_loss|) ≥ 2.0 AND ≥ 50 closed trades → eligible for **conservative** live (size 0.02 SOL, max 5 positions)
- WR ≥ 50% AND R:R ≥ 2.0 AND ≥ 100 closed trades → eligible for full live at user's configured size
- Recent strategy change with < 20 trades on the new config → **not yet**, no track record

**Always project slippage on top:**

- Live entry slippage: +2-5% on tokens < $30K mcap
- Live exit slippage normal: +3-5%
- Live exit during dump: +10-30%
- Rule of thumb: realized dry-run PnL × 0.5 ≈ realistic live PnL after slippage

**Always cross-check the unrealized number:**

The "unrealized peak" overstates expected exit by `trailing_percent`. With `trailing_percent: 35`, real exit ≈ `high_water - 35%`. Reduce the unrealized projection accordingly before quoting it.

**Always offer the ladder, not a binary:**

1. Stay dry-run another 24-48h with the new config
2. Live conservative: `position_size_sol: 0.02`, `max_open_positions: 5` → max exposure 0.1 SOL
3. Live full: current config

Default recommendation when in doubt: **option 2**. The user explicitly likes seeing the option breakdown — don't just say "go live" or "don't go live".

## Live Mode Considerations (1 SOL capital)

When transitioning from dry_run to live mode with limited capital:

**Position sizing math:**
- 0.05 SOL × 10 positions = 0.50 SOL (leaves 0.50 for buffer + gas)
- Gas per trade (entry + exit): ~0.002 SOL worst case (priority fee)
- 20 trades × 0.002 = 0.04 SOL total gas — negligible

**Slippage reality:**
- Token $7K mcap, liq ~$5-6K: buy 0.05 SOL = ~0.8% slippage (acceptable)
- Token $7K mcap, liq ~$5-6K: buy 0.1 SOL = ~2-3% slippage (concerning)
- Exit during dump: slippage 5-10% on top of price drop
- Rule: if position_size > 0.05 SOL, raise min_mcap to $15K

**Don't raise min_mcap for 0.05 SOL size:**
- Data shows tokens <$15K mcap have 12.5% WR vs 18.6% for ≥$15K
- BUT the single biggest winner (TITTY +1103%, entry $11K) came from <$15K
- At 0.05 SOL size, max loss per trade = ~0.01 SOL, upside = 0.5+ SOL
- Risk/reward still favorable at low mcap with small size
- min_holders = 50 is the real rug protection, not mcap floor

**Recommended live settings (1 SOL capital):**
- position_size_sol: 0.05
- max_open_positions: 10
- min_mcap: $7K (keep low for moonshot access)
- min_holders: 50 (rug protection)
- Everything else same as dry_run

**STALE exit in live mode:**
- Still worth it: exit at -5% costs ~0.0028 SOL vs SL at -20% = 0.01 SOL
- Gas fee for stale exit: ~0.001 SOL — still saves 0.006 SOL vs waiting for SL
- Consider raising stale timeout to 15min in live (from 10min) to reduce unnecessary exits

## Pitfall: Dual max_open_positions

`max_open_positions` exists in TWO places:
1. `settings` table (key: `max_open_positions`) — used for log display
2. `strategies.config_json` (field: `max_open_positions`) — used by `canOpenMorePositions()`

The actual check in `src/db/positions.js` line 24:
```js
const max = strat.max_open_positions ?? numSetting('max_open_positions', 3);
```

Strategy config takes priority. If you only update settings table, positions still get blocked. **Always update both:**
```js
// Settings table
db.prepare("UPDATE settings SET value = '20' WHERE key = 'max_open_positions'").run();
// Strategy config
const row = db.prepare("SELECT config_json FROM strategies WHERE id = 'profit_lock'").get();
const config = JSON.parse(row.config_json);
config.max_open_positions = 20;
db.prepare("UPDATE strategies SET config_json = ? WHERE id = 'profit_lock'").run(JSON.stringify(config));
```

Symptom: log says `max positions reached (10/20)` — the 20 comes from settings, but actual limit is strategy's value (was still 10).

## Database Location

The SQLite database is at `~/charon/charon.sqlite` (NOT `charon.db` — that file exists but is empty/unused).

## Fresh Start / Reset Pattern

When user wants to reset PnL tracking and start fresh without reinstalling:
```js
const Database = require('better-sqlite3');
const db = new Database('./charon.sqlite');
// Close all open positions
db.prepare("DELETE FROM dry_run_positions").run();
db.prepare("DELETE FROM dry_run_trades").run();
// Reset auto-increment
try { db.prepare("DELETE FROM sqlite_sequence WHERE name = 'dry_run_positions'").run(); } catch(e) {}
try { db.prepare("DELETE FROM sqlite_sequence WHERE name = 'dry_run_trades'").run(); } catch(e) {}
```

Then `pm2 restart charon`. Settings/strategies/lessons are preserved — only trade history is cleared.

**Full uninstall (user wants to reinstall from scratch):**
```bash
pm2 stop charon && pm2 delete charon
pm2 stop gmgn-bridge && pm2 delete gmgn-bridge
rm -rf ~/charon
pm2 save --force
```

Access pattern:
```js
const Database = require('better-sqlite3');
const db = new Database('./charon.sqlite');
```

Note: `sqlite3` CLI is not installed on this VPS. Always use `node -e` with `better-sqlite3` for DB queries.

## Updating Strategy Config (no restart needed)

All strategy settings live in SQLite `strategies` table, `config_json` column. Changes take effect on next position check (5s). Pattern:

```js
import('./src/db/connection.js').then(({db}) => {
  const row = db.prepare("SELECT config_json FROM strategies WHERE id = 'profit_lock'").get();
  const config = JSON.parse(row.config_json);
  config.KEY = VALUE;  // e.g. profit_lock_confirm_s, profit_lock_tiers, max_mcap_usd
  db.prepare("UPDATE strategies SET config_json = ? WHERE id = 'profit_lock'").run(JSON.stringify(config));
});
```

Settings table (`max_open_positions`, etc.) also no-restart — read via `numSetting()` each call.
