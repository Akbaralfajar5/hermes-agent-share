---
name: pump-analyzer-solana
description: Real-time monitoring and analytics platform for Pump.fun tokens on Solana using WebSockets, HTML/CSS/JS
triggers:
  - "set up pump analyzer"
  - "track pump.fun tokens"
  - "monitor solana token launches"
  - "add real-time token alerts"
  - "integrate pump.fun websocket"
  - "build memecoin dashboard"
  - "analyze pump.fun token trends"
  - "connect solana wallet to tracker"
  - "cari token early"
  - "scan pump.fun"
  - "sinyal token bagus"
  - "cari token baru launch"
  - "pump scanner"
  - "rugcheck token"
  - "analisis token lebih dalam"
  - "scan micin"
  - "snipe"
  - "pantau real-time"
  - "pantau pump.fun"
  - "token fresh"
  - "token baru"
  - "cari token baru launch"
---

# PumpAnalyzer — Solana Token Monitoring Platform

> Skill by [ara.so](https://ara.so) — Daily 2026 Skills collection.

PumpAnalyzer is a **static front-end platform** (pure HTML/CSS/JS, no build tools) that provides real-time monitoring, analytics, and alerts for tokens launched on [Pump.fun](https://pump.fun) on the Solana blockchain. It connects to Pump.fun's WebSocket API for sub-second updates, displays price/volume charts, supports custom alert criteria, and includes non-custodial Solana wallet connection.

---

## Two-Mode Scanning Strategy (CRITICAL — read first)

**There are TWO fundamentally different scanning modes. DexScreener and pump.fun WebSocket serve different time windows — do NOT use the same pipeline for both.**

Full methodology: `references/two-mode-scanning.md`

### Mode 1: "scan micin" — DexScreener + RugCheck
**Token age:** 30 min - 6 hours | **FDV:** $2K - $30K | **Risk:** Medium

When user says `scan micin`, `cari token`, `sinyal token bagus`:
1. DexScreener token-profiles + boosts + search
2. Filter by FDV, volume, buys
3. Full RugCheck (mint, freeze, LP, holders, distribution)
4. Quality score → ranked candidates
5. Entry plan with Fibonacci retracement zones

**Output:** Full analysis dengan safety score + entry zones + TP/SL

### Mode 2: "snipe" — pump.fun WebSocket real-time
**Token age:** 0 - 5 minutes | **MCap:** 28 - 50 SOL | **Risk:** Very high

When user says `snipe`, `pantau real-time`, `pantau pump.fun`:
1. Connect `wss://pumpportal.fun/api/data` → `subscribeNewToken`
2. Filter by name quality only (skip test/spam/generic)
3. Print immediately — name, mcap, CA, pump.fun link
4. RugCheck only for mint/freeze (distribution check useless — see pitfall)

**Script:** `scripts/pumpfun_sniper.py` — `python3 pumpfun_sniper.py [duration_sec]`
**Rate:** 5-15 filtered tokens per 30 seconds

### Key Tradeoff
| | Mode 1 (DexScreener) | Mode 2 (WebSocket) |
|---|---|---|
| Entry price | 2-7x dari launch | Dekat launch price |
| Safety data | ✅ Full | ⚠️ Mint/freeze only |
| Upside | 2-10x | 10-100x |
| Scam risk | Low-Medium | High |

---

## Token Analysis Workflow (Mode 1 — Deep Analysis)

When user asks "Good ga?" or "Gimana?" with a CA, follow this sequence:

### 1. Fetch Basic Data (pump.fun)
```bash
# Navigate to pump.fun page
https://pump.fun/[CA]
```
Extract:
- Name, symbol, age
- Current market cap
- 24h change (% and $)
- ATH (all-time high)
- Current vs ATH %
- Description
- Social links (Twitter, Telegram, Website)

### 2. Fetch Safety Data (RugCheck API)
```bash
curl -s "https://api.rugcheck.xyz/v1/tokens/[CA]/report" | jq '{
  name: .tokenMeta.name,
  score: .score,
  mint: .mintAuthority,
  freeze: .freezeAuthority,
  lpLocked: .markets[0].lp.lpLockedPct,
  holders: .totalHolders,
  topHolder: .topHolders[0].pct,
  creator: .creator,
  creatorBalance: .creatorBalance
}'
```

### 3. Safety Scoring
```
Mandatory checks (must pass all):
✅ Mint authority: null (revoked)
✅ Freeze authority: null (revoked)
✅ LP locked: 100%

Scoring (out of 100):
- LP locked: 30 pts (pass/fail)
- Mint revoked: 25 pts (pass/fail)
- Freeze revoked: 20 pts (pass/fail)
- Top holder <40%: 10 pts (8 if <50%, 5 if <60%, 0 if >60%)
- RugCheck score: 5 pts (5 if <500, 2 if 500-1000, 0 if >1000)
- Creator balance 0: 5 pts (creator sold all = no dump risk)
- Social links: 5 pts (has Twitter/Telegram/Website)

Total: 90-100 = Safe, 70-89 = Medium, <70 = Risky
```

### 4. Timing Analysis
```
Age-based assessment:
- <1 hour: VERY FRESH (high volatility, wait for stability)
- 1-6 hours: FRESH (good for early entry if safe)
- 6-24 hours: EARLY (still good timing)
- 1-7 days: ESTABLISHED (lower risk, lower upside)
- >7 days: MATURE (lowest risk, lowest upside)

Pump analysis:
- If +100%+ in last 24h: ALREADY PUMPED (wait for pullback)
- If -50%+ from ATH: DUMPING (wait for support)
- If -80%+ from ATH: DEAD or BOTTOMING (high risk)
```

### 5. Support/Resistance Identification
(See "Support/Resistance Identification" section above)

### 5a. Entry Zone Calculation (for "entry di berapa?")
When user asks for specific entry levels on a pumped token, use the Fibonacci retracement method from launch price. Full methodology in `references/entry-zone-calculation.md`. Core steps:

1. Derive launch price from 24h change (for tokens < 24h old, 24h change = total pump)
2. Fibonacci 0.236 / 0.382 / 0.5 for S1/S2/S3 zones
3. Check 5m momentum to determine if still pumping or ready to enter
4. Present as table: Level | Harga | FDV | Drop | Alokasi

### 6. Generate Recommendation
```
Format:
❌ TIDAK RECOMMENDED - if fails safety checks or terrible timing
⚠️ WAIT - if safe but bad timing (already pumped, or wait for support)
✅ GOOD - if safe + good timing + good entry price

Include:
- Verdict (❌/⚠️/✅)
- Safety score (X/100)
- Key positives (3-5 bullets)
- Key negatives (3-5 bullets)
- Support levels (if waiting)
- Entry setup (entry, SL, TP1, TP2, TP3, position size)
- Comparison with user's criteria ($10K threshold, etc.)
```

### 7. Example Output
```
## 🔍 ANALISIS: Token Name (SYMBOL)

**CA:** `[full_address]`

**Current:** $XXK market cap
**24h:** +XX% or -XX%
**ATH:** $XXM
**Age:** X hours/days

**Safety Score:** XX/100 ✅/⚠️/❌

**POSITIVES:**
✅ Mint revoked
✅ LP 100% locked
✅ X holders

**NEGATIVES:**
🚨 Already pumped +XXX%
⚠️ Down -XX% from ATH

**SUPPORT LEVELS:**
S1: $XXK (primary entry) ⭐
S2: $XXK (strong support)
S3: $XXK (major support)

**VERDICT:** ⚠️ WAIT FOR $XXK

**Entry Setup (if $XXK reached):**
Entry: $XXK
Stop: $XXK (-XX%)
TP1: $XXK (+XX%)
TP2: $XXK (+XX%)
Position: X%
```

## Bot Threshold Tuning

When setting up auto-screening bots, threshold selection is critical:

### Market Cap Threshold Selection

| Threshold | Alert Rate | Upside Potential | Risk Level | Use Case |
|-----------|-----------|------------------|------------|----------|
| $2-3K | 15-20/min | 10-50x | VERY HIGH | Degen mode, full-time monitoring |
| $5K | 8-12/min | 5-20x | HIGH | Active trading, high risk tolerance |
| $10K | 3-5/min | 3-10x | MEDIUM | Balanced, part-time monitoring |
| $20K | 1-2/min | 2-5x | MEDIUM-LOW | Conservative, established tokens |
| $50K+ | 5-10/hour | 1.5-3x | LOW | Ultra-conservative, lowest volatility |

### Tuning Process (from this session)

**User's journey:**
1. Started with $6K threshold → 0 alerts in 10 min (too strict, missed opportunities)
2. Adjusted to $2.6K → 9 tokens/min = 540/hour (too many, overwhelming)
3. User requested $10K → 0 alerts in 20 min (too strict again)
4. **Lesson:** Sweet spot is $5-10K for manageable alerts with good upside

**Recommended approach:**
1. Start with $10K (conservative)
2. If no alerts in 30 min → lower to $7K
3. If still no alerts → lower to $5K
4. If too many alerts (>5/min) → raise threshold
5. Target: 2-5 alerts per hour (manageable)

**PITFALL:** Don't set threshold based on "I want X alerts per day." Set it based on market cap range that matches your risk tolerance, then adjust alert frequency by adding filters (social links required, score threshold, etc.)

### Score Threshold Tuning

| Score | Pass Rate | Quality | Use Case |
|-------|-----------|---------|----------|
| 70+ | 80% | Mixed | Maximum opportunities, manual filtering needed |
| 80+ | 50% | Good | Balanced, most alerts worth checking |
| 85+ | 30% | High | Conservative, fewer but higher quality |
| 90+ | 10% | Excellent | Ultra-selective, might miss good tokens |

**Recommended:** Start with 80+, adjust based on false positive rate.

### Combined Threshold Strategy

**Best setup (from session):**
```python
MIN_MARKET_CAP_USD = 10000  # $10K (established tokens)
SAFE_SCORE_THRESHOLD = 80   # Good quality
SOCIAL_LINKS_REQUIRED = False  # Optional (many good tokens launch without social first)
```

**Result:** 1-3 alerts per hour, 90%+ are worth checking

**Alternative (more aggressive):**
```python
MIN_MARKET_CAP_USD = 5000   # $5K (earlier entry)
SAFE_SCORE_THRESHOLD = 85   # Higher quality to compensate
SOCIAL_LINKS_REQUIRED = True  # Filter out low-effort tokens
```

**Result:** 3-8 alerts per hour, 70-80% are worth checking

## Token Screening Fundamentals

Before building monitoring tools, understand what to screen for:

### Red Flags (Avoid)
- Initial buy > 10 SOL (creator setup for dump)
- Top holder owns > 50% supply
- Creator wallet has rug pull history
- No social media (Twitter/Telegram)
- Market cap < $2K (too small, easily manipulated)
- Pump 500%+ in < 5 minutes (artificial)
- Volume spike then disappears (pump & dump)

### Green Flags (Safe-ish)
- Initial buy 0.5-3 SOL (normal range)
- Market cap $5K-$50K (sweet spot for early entry)
- Holder distribution: top 10 < 30% supply
- Active social media (Twitter/Telegram with real engagement)
- Volume 24h > 20% of market cap
- Chart rises gradually with healthy pullbacks
- Holder count growing (not just trading back-and-forth)

### Safety Score Algorithm
```javascript
let score = 100;

// Initial buy check
if (initialBuy > 10) score -= 30;
else if (initialBuy > 5) score -= 15;
else if (initialBuy >= 0.5 && initialBuy <= 3) score += 0; // neutral/good

// Market cap check
if (mcap < 2) score -= 25;
else if (mcap >= 5 && mcap <= 50) score += 10;
else if (mcap > 100) score -= 10;

// Quality signals
if (hasDescription && description.length > 20) score += 5;
else score -= 10;

if (validNameAndSymbol) score += 0;
else score -= 15;

// Levels: 70-100 = safe, 40-69 = warning, 0-39 = danger
```

### Entry Strategy
- **Best timing:** 30 min - 2 hours after launch (price discovery done, scams visible, still early)
- **Position sizing:** 2-5% of portfolio max per token
- **Entry price:** Wait for pullback after first pump, don't FOMO at top

#### Support/Resistance Identification (for "Supportnya dimana?" questions)

When user asks "where's support?" or "good entry?", analyze:

1. **Fetch current data:**
   - Current market cap
   - 24h high/low
   - ATH (all-time high)
   - Current vs ATH percentage

2. **Identify support levels (buy zones):**
   - **S1 (Primary):** Current consolidation zone (usually 10-20% below current if already pumped)
   - **S2 (Secondary):** Mid-range between current and 24h low
   - **S3 (Major):** Near 24h low (strong bounce zone)
   - **S4 (Critical):** Below 24h low = support broken, wait for new level

3. **Identify resistance levels (sell zones):**
   - **R1:** Previous local high or 24h high
   - **R2:** Psychological round numbers (e.g., $500K, $1M)
   - **R3:** Previous support turned resistance (if dumped from higher)
   - **R4:** ATH (moon shot target)

4. **Calculate entry recommendations:**
   ```
   Example: Token at $433K, ATH $10.2M, 24h low $224K, 24h high $667K
   
   Support Levels:
   S1: $350-380K (primary entry, -12-19% from current)
   S2: $280-320K (strong support, mid-range)
   S3: $220-250K (major support, 24h low area)
   
   Resistance Levels:
   R1: $550-600K (24h high area)
   R2: $800K-1M (psychological)
   R3: $2-3M (previous support if applicable)
   R4: $10.2M (ATH)
   ```

5. **Entry strategy options:**
   - **Aggressive:** Enter now (higher risk, might pullback)
   - **Balanced:** Wait for S1 (best risk/reward) ⭐
   - **Conservative:** Wait for S2 or S3 (lowest risk, might miss)
   - **Layered:** Split position across S1, S2, S3 (recommended for volatile tokens)

6. **Layered entry example:**
   ```
   Total position: 3% (0.3 SOL)
   Entry 1: S1 ($380K) → 1% (0.1 SOL)
   Entry 2: S2 ($320K) → 1% (0.1 SOL)
   Entry 3: S3 ($280K) → 1% (0.1 SOL)
   
   Stop loss: Below S3 (e.g., $240K)
   Average entry: $327K (if all fill)
   ```

**PITFALL:** If token already pumped +100%+ in 24h, support levels are unreliable. Wait for 2-3 days of consolidation before identifying stable support.

### Exit Strategy (TP/SL Implementation)

**CRITICAL:** Pump.fun has **NO native TP/SL features**. You must implement manually using one of these methods:

#### Method 1: Jupiter Limit Orders (RECOMMENDED ⭐)
1. Entry on pump.fun (fastest execution)
2. Immediately set Jupiter limit orders for TP/SL:
   - Go to jup.ag
   - Select [Token] → SOL
   - Click "Limit Order"
   - Set multiple orders:
     - SL: -20-25% → Sell 30%
     - TP1: +50% → Sell 30%
     - TP2: +100% → Sell 30%
     - TP3: +200% → Sell 10%
3. Orders execute automatically 24/7
4. Fee: ~0.5% (worth it for automation)

**Pros:** Fully automated, works while sleeping, no monitoring needed  
**Cons:** Small fee, order might not fill if price gaps

#### Method 2: DexScreener Price Alerts + Manual Sell
1. Set alerts at dexscreener.com/solana/[CA]
2. Click bell icon → Set price alerts for SL/TP levels
3. Choose Telegram/Email/Push notification
4. When alert fires → manually sell on pump.fun

**Pros:** Free, simple  
**Cons:** Manual execution required, can miss exits if phone off

#### Method 3: Telegram Trading Bots (BonkBot, Maestro, Trojan)
1. Connect wallet to bot
2. Entry via bot (not pump.fun)
3. Set TP/SL in bot commands: `/sell [CA] -20%` (SL), `/sell [CA] +50%` (TP)
4. Bot auto-executes

**Pros:** Fully automated, fast execution  
**Cons:** Bot fees 1-2%, need to trust bot with wallet

#### Standard TP/SL Levels
- **TP1:** +50% (1.5x) → sell 30%
- **TP2:** +100% (2x) → sell 30%
- **TP3:** +200% (3x) → sell 30%
- **Moon bag:** Keep 10% for 5-10x
- **Stop loss:** -20-30% from entry (strict!)
- **Time stop:** If no profit in 24-48h → exit 50%+

#### TP/SL by Market Cap Entry
| Entry MCap | TP1 | TP2 | TP3 | SL |
|------------|-----|-----|-----|----|
| <$5K | +100% | +300% | +500% | -25% |
| $5-10K | +80% | +200% | +400% | -25% |
| $10-30K | +50% | +100% | +200% | -20% |
| $30-50K | +40% | +80% | +150% | -20% |
| $50-100K | +30% | +60% | +100% | -20% |
| >$100K | +20% | +40% | +80% | -15% |

**PITFALL:** Don't sell 100% at once! Scale out (30-30-30-10) to capture full move while securing profits early.

### Risk Management
- Max 10-20% total portfolio in pump.fun
- Max 3-5 tokens per day
- Stop trading after 3 losses in a row
- Never average down on losing positions

---

## Installation

```bash
git clone https://github.com/happyboy4ty25/pump-analyzer.git
cd pump-analyzer
open index.html   # or use a local dev server
```

No npm, no bundler, no dependencies — open `index.html` directly in a browser or serve with any static file server:

```bash
# Python
python3 -m http.server 8080

# Node (npx)
npx serve .

# VS Code
# Use the "Live Server" extension
```

---

## Project Structure

```
pump-analyzer/
├── index.html          # Main landing page & app shell
├── css/
│   └── style.css       # All styles, animations, responsive layout
├── js/
│   ├── main.js         # App init, UI interactions, animations
│   ├── websocket.js    # Pump.fun WebSocket connection & event handling
│   ├── wallet.js       # Solana wallet adapter (Phantom, Solflare, etc.)
│   ├── alerts.js       # Custom alert criteria logic
│   └── charts.js       # Price/volume chart rendering
└── assets/
    └── ...             # Icons, images
```

---

## Key Concepts & Architecture

### 1. Pump.fun WebSocket Connection

PumpAnalyzer subscribes to Pump.fun's real-time data stream. The core pattern:

```javascript
// js/websocket.js

const PUMP_FUN_WS_URL = 'wss://pumpportal.fun/api/data';

class PumpWebSocket {
  constructor(onToken, onTrade) {
    this.onToken = onToken;  // callback for new token launches
    this.onTrade = onTrade;  // callback for trade events
    this.ws = null;
    this.reconnectDelay = 1000;
  }

  connect() {
    this.ws = new WebSocket(PUMP_FUN_WS_URL);

    this.ws.addEventListener('open', () => {
      console.log('[PumpWS] Connected');
      this.reconnectDelay = 1000;

      // Subscribe to new token creation events
      this.ws.send(JSON.stringify({
        method: 'subscribeNewToken'
      }));

      // Subscribe to all trades on new tokens
      this.ws.send(JSON.stringify({
        method: 'subscribeTokenTrade',
        keys: []  // empty = all tokens
      }));
    });

    this.ws.addEventListener('message', (event) => {
      const data = JSON.parse(event.data);
      if (data.txType === 'create') {
        this.onToken(data);
      } else if (data.txType === 'buy' || data.txType === 'sell') {
        this.onTrade(data);
      }
    });

    this.ws.addEventListener('close', () => {
      console.warn('[PumpWS] Disconnected — reconnecting in', this.reconnectDelay, 'ms');
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
    });

    this.ws.addEventListener('error', (err) => {
      console.error('[PumpWS] Error:', err);
      this.ws.close();
    });
  }

  // Subscribe to trades for a specific token mint
  subscribeToken(mintAddress) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        method: 'subscribeTokenTrade',
        keys: [mintAddress]
      }));
    }
  }

  disconnect() {
    this.ws?.close();
  }
}

export default PumpWebSocket;
```

### 2. Handling New Token Events

```javascript
// js/main.js

import PumpWebSocket from './websocket.js';

const tokenList = [];

function onNewToken(tokenData) {
  // tokenData shape from Pump.fun:
  // {
  //   signature: string,
  //   mint: string,          // token mint address
  //   traderPublicKey: string,
  //   txType: 'create',
  //   name: string,
  //   symbol: string,
  //   description: string,
  //   imageUri: string,
  //   initialBuy: number,    // SOL amount
  //   marketCapSol: number,
  //   uri: string,
  //   timestamp: number
  // }

  tokenList.unshift(tokenData);
  renderTokenCard(tokenData);
  checkAlerts(tokenData);
}

function onTrade(tradeData) {
  // tradeData shape:
  // {
  //   signature: string,
  //   mint: string,
  //   traderPublicKey: string,
  //   txType: 'buy' | 'sell',
  //   tokenAmount: number,
  //   solAmount: number,
  //   newTokenBalance: number,
  //   bondingCurveKey: string,
  //   vTokensInBondingCurve: number,
  //   vSolInBondingCurve: number,
  //   marketCapSol: number,
  //   timestamp: number
  // }

  updateTokenMetrics(tradeData.mint, tradeData);
}

const pumpWS = new PumpWebSocket(onNewToken, onTrade);
pumpWS.connect();
```

### 3. Rendering Token Cards

```javascript
// js/main.js

function renderTokenCard(token) {
  const container = document.getElementById('token-feed');

  const card = document.createElement('div');
  card.className = 'token-card';
  card.dataset.mint = token.mint;

  card.innerHTML = `
    <div class="token-header">
      <img src="${token.imageUri || 'assets/placeholder.png'}" 
           alt="${token.symbol}" 
           class="token-image"
           onerror="this.src='assets/placeholder.png'">
      <div class="token-info">
        <span class="token-name">${escapeHtml(token.name)}</span>
        <span class="token-symbol">$${escapeHtml(token.symbol)}</span>
      </div>
      <span class="token-time">${formatTimestamp(token.timestamp)}</span>
    </div>
    <div class="token-metrics">
      <div class="metric">
        <label>Market Cap</label>
        <span class="market-cap">${formatSol(token.marketCapSol)} SOL</span>
      </div>
      <div class="metric">
        <label>Initial Buy</label>
        <span>${formatSol(token.initialBuy)} SOL</span>
      </div>
    </div>
    <div class="token-actions">
      <a href="https://pump.fun/${token.mint}" target="_blank" rel="noopener" 
         class="btn btn-small">View on Pump.fun</a>
      <button class="btn btn-small btn-outline" 
              onclick="setAlert('${token.mint}')">Set Alert</button>
    </div>
  `;

  // Animate in
  card.style.opacity = '0';
  card.style.transform = 'translateY(-10px)';
  container.prepend(card);
  requestAnimationFrame(() => {
    card.style.transition = 'opacity 0.3s, transform 0.3s';
    card.style.opacity = '1';
    card.style.transform = 'translateY(0)';
  });

  // Cap the list at 50 cards
  while (container.children.length > 50) {
    container.removeChild(container.lastChild);
  }
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function formatSol(amount) {
  return amount ? Number(amount).toFixed(2) : '0.00';
}

function formatTimestamp(ts) {
  return new Date(ts * 1000).toLocaleTimeString();
}
```

### 4. Custom Alerts System

```javascript
// js/alerts.js

const MAX_FREE_ALERTS = 5;

class AlertManager {
  constructor() {
    this.alerts = JSON.parse(localStorage.getItem('pump_alerts') || '[]');
    this.dailyCount = parseInt(localStorage.getItem('pump_alert_count') || '0');
    this.plan = localStorage.getItem('pump_plan') || 'free';
  }

  canAddAlert() {
    if (this.plan !== 'free') return true;
    return this.dailyCount < MAX_FREE_ALERTS;
  }

  addAlert({ mint, criteria }) {
    // criteria: { minMarketCap, maxMarketCap, minVolume, keywords }
    if (!this.canAddAlert()) {
      showUpgradeModal('You've reached the free plan limit of 5 alerts/day.');
      return false;
    }

    const alert = { id: Date.now(), mint, criteria, active: true };
    this.alerts.push(alert);
    this._save();
    return alert;
  }

  checkToken(tokenData) {
    for (const alert of this.alerts) {
      if (!alert.active) continue;
      if (this._matches(tokenData, alert.criteria)) {
        this._trigger(alert, tokenData);
      }
    }
  }

  _matches(token, criteria) {
    if (criteria.minMarketCap && token.marketCapSol < criteria.minMarketCap) return false;
    if (criteria.maxMarketCap && token.marketCapSol > criteria.maxMarketCap) return false;
    if (criteria.keywords?.length) {
      const text = `${token.name} ${token.symbol} ${token.description}`.toLowerCase();
      if (!criteria.keywords.some(k => text.includes(k.toLowerCase()))) return false;
    }
    return true;
  }

  _trigger(alert, token) {
    // Browser notification
    if (Notification.permission === 'granted') {
      new Notification(`🚨 Alert: ${token.name} ($${token.symbol})`, {
        body: `Market cap: ${token.marketCapSol.toFixed(2)} SOL`,
        icon: token.imageUri || 'assets/icon.png'
      });
    }

    // In-app notification
    showInAppAlert(token);

    this.dailyCount++;
    localStorage.setItem('pump_alert_count', this.dailyCount);
  }

  _save() {
    localStorage.setItem('pump_alerts', JSON.stringify(this.alerts));
  }
}

export const alertManager = new AlertManager();

// Request notification permission on load
if ('Notification' in window && Notification.permission === 'default') {
  Notification.requestPermission();
}
```

### 5. Solana Wallet Connection (Non-Custodial)

```javascript
// js/wallet.js

class SolanaWalletConnect {
  constructor() {
    this.publicKey = null;
    this.provider = null;
  }

  getProvider() {
    // Phantom
    if ('phantom' in window && window.phantom?.solana?.isPhantom) {
      return window.phantom.solana;
    }
    // Solflare
    if ('solflare' in window && window.solflare?.isSolflare) {
      return window.solflare;
    }
    return null;
  }

  async connect() {
    this.provider = this.getProvider();

    if (!this.provider) {
      window.open('https://phantom.app/', '_blank');
      throw new Error('No Solana wallet found. Please install Phantom.');
    }

    try {
      const resp = await this.provider.connect();
      this.publicKey = resp.publicKey.toString();
      this._onConnected();
      return this.publicKey;
    } catch (err) {
      if (err.code === 4001) {
        throw new Error('Connection rejected by user.');
      }
      throw err;
    }
  }

  async disconnect() {
    await this.provider?.disconnect();
    this.publicKey = null;
    this._onDisconnected();
  }

  _onConnected() {
    const btn = document.getElementById('wallet-btn');
    if (btn) {
      btn.textContent = `${this.publicKey.slice(0, 4)}...${this.publicKey.slice(-4)}`;
      btn.classList.add('connected');
    }

    // Unlock plan features based on on-chain subscription (check via RPC)
    this.checkSubscription();
  }

  _onDisconnected() {
    const btn = document.getElementById('wallet-btn');
    if (btn) {
      btn.textContent = 'Connect Wallet';
      btn.classList.remove('connected');
    }
  }

  async checkSubscription() {
    // Query your backend or on-chain program to verify subscription tier
    const RPC = 'https://api.mainnet-beta.solana.com';
    // ... implement based on your subscription contract
  }
}

export const wallet = new SolanaWalletConnect();

// Wire up button
document.getElementById('wallet-btn')?.addEventListener('click', async () => {
  try {
    if (wallet.publicKey) {
      await wallet.disconnect();
    } else {
      await wallet.connect();
    }
  } catch (err) {
    console.error('Wallet error:', err.message);
    showToast(err.message, 'error');
  }
});
```

### 6. Simple Price Chart (Canvas API)

```javascript
// js/charts.js

class PriceChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.dataPoints = [];
    this.maxPoints = 60;
  }

  addPoint(marketCapSol, timestamp) {
    this.dataPoints.push({ value: marketCapSol, time: timestamp });
    if (this.dataPoints.length > this.maxPoints) {
      this.dataPoints.shift();
    }
    this.render();
  }

  render() {
    const { ctx, canvas, dataPoints } = this;
    const { width, height } = canvas;

    ctx.clearRect(0, 0, width, height);

    if (dataPoints.length < 2) return;

    const values = dataPoints.map(p => p.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;

    const xStep = width / (dataPoints.length - 1);

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(20, 241, 149, 0.3)');
    gradient.addColorStop(1, 'rgba(20, 241, 149, 0)');

    ctx.beginPath();
    ctx.moveTo(0, height - ((dataPoints[0].value - min) / range) * height);

    dataPoints.forEach((point, i) => {
      const x = i * xStep;
      const y = height - ((point.value - min) / range) * height;
      ctx.lineTo(x, y);
    });

    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw line
    ctx.beginPath();
    ctx.strokeStyle = '#14F195';
    ctx.lineWidth = 2;
    dataPoints.forEach((point, i) => {
      const x = i * xStep;
      const y = height - ((point.value - min) / range) * height;
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
}

export default PriceChart;
```

---

## Configuration

All configuration is done via constants at the top of each JS file. No `.env` file needed for the front-end — but if you add a backend:

```javascript
// js/config.js
const CONFIG = {
  WS_URL: 'wss://pumpportal.fun/api/data',
  RPC_URL: process.env.SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com',
  API_BASE: process.env.API_BASE_URL || 'https://pump-analyzer.com/api',
  PLANS: {
    free:  { alertsPerDay: 5,         price: 0 },
    pro:   { alertsPerDay: Infinity,   price: 29,  sol: 0.5 },
    elite: { alertsPerDay: Infinity,   price: 99,  sol: 1.5 }
  }
};
```

---

## Common Patterns

### Filter tokens by keyword on arrival

```javascript
function onNewToken(token) {
  const keyword = document.getElementById('filter-input').value.toLowerCase();
  if (keyword && !`${token.name} ${token.symbol}`.toLowerCase().includes(keyword)) return;
  renderTokenCard(token);
}
```

### Debounce rapid trade updates

```javascript
const updateQueue = new Map();

function onTrade(trade) {
  clearTimeout(updateQueue.get(trade.mint));
  updateQueue.set(trade.mint, setTimeout(() => {
    updateTokenMetrics(trade.mint, trade);
    updateQueue.delete(trade.mint);
  }, 200));
}
```

### Show upgrade modal for free plan limits

```javascript
function showUpgradeModal(reason) {
  document.getElementById('upgrade-reason').textContent = reason;
  document.getElementById('upgrade-modal').classList.add('visible');
}
```

---

## Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| WebSocket won't connect | Browser blocks WSS or wrong URL | Check `wss://pumpportal.fun/api/data` is reachable; use DevTools Network tab |
| No tokens appearing | Subscription message not sent on `open` | Ensure `subscribeNewToken` is sent inside `ws.addEventListener('open', ...)` |
| Wallet button does nothing | Wallet extension not installed | Detect `window.phantom` before calling `.connect()` |
| Notifications not firing | Permission not granted | Call `Notification.requestPermission()` after a user gesture |
| Cards not updating market cap | `mint` mismatch between token and trade events | Normalize mint addresses to strings before comparison |
| Page flickers on new token | DOM prepend causes reflow | Use `requestAnimationFrame` + CSS transitions for card entry |

---

## Pricing / Plan Gating Pattern

```javascript
// Check plan before unlocking features
function requirePlan(minimumPlan, action) {
  const planRank = { free: 0, pro: 1, elite: 2 };
  const userPlan = localStorage.getItem('pump_plan') || 'free';

  if (planRank[userPlan] >= planRank[minimumPlan]) {
    action();
  } else {
    showUpgradeModal(`This feature requires the ${minimumPlan} plan.`);
  }
}

// Usage
requirePlan('pro', () => enableUnlimitedAlerts());
requirePlan('elite', () => enableAIInsights());
```

---

## Support Files

- **`references/screening-guide.md`** — Comprehensive token screening checklist, red/green flags, risk management strategy, entry/exit timing, and realistic expectations. Load this first when user asks "how to avoid scams" or "how to screen tokens".
- **`references/price-alert-setup.md`** — Pattern for setting up automated price alerts using Hermes cronjobs. Use when user asks "kasih tau kalau turun ke $XXK" or "alert me at support level". Includes cronjob setup, alert logic, troubleshooting, and why simple script + cronjob beats long-running process.
- **`references/gmgn-cli-workflow.md`** — gmgn-cli setup and workflows (smart money, bundle, sniper filters). PREFERRED over DexScreener. Load when user says "gmgn", "trenches", or wants smart-money-filtered tokens.
- **`references/cli-scan-workflow.md`** — Python-based CLI scanning workflow: DexScreener → RugCheck → quality scoring → ranked candidates. Covers two scanning modes (established vs early tokens), deep single-token analysis, Trojan/Photon app data interpretation, cron job pattern, and output format for Bahasa Indonesia user. Load this when user asks "cari token early", "scan pump.fun", or "sinyal token bagus".
- **`references/two-mode-scanning.md`** — Strategy guide for the two scanning modes (DexScreener vs WebSocket sniper). When to use each, pipeline differences, RugCheck limitations at launch, and combined strategy. Load when user asks "snipe", "pantau real-time", or conflates the two modes.
- **`references/entry-zone-calculation.md`** — Fibonacci retracement method for calculating entry zones on pumped tokens. Derive launch price, apply fib levels, check momentum, present entry plan.
- **`references/gemini-vision-api.md`** — Direct Gemini Vision API call pattern for analyzing trading bot screenshots (Trojan, Photon, BullX) when built-in vision_analyze fails. Covers base64 encoding, model fallback strategy, common prompts, and rate limit handling.
- **`scripts/deploy-dashboard.sh`** — One-command deployment script that creates a working real-time monitoring dashboard with auto-screening. Run `bash scripts/deploy-dashboard.sh ~/pump-monitor` then `cd ~/pump-monitor && python3 -m http.server 8888`.
- **`scripts/pumpfun_sniper.py`** — Real-time pump.fun WebSocket sniper. Connects to `wss://pumpportal.fun/api/data`, filters by name quality, prints tokens within seconds of launch. Run: `python3 pumpfun_sniper.py 120` (120 = duration in seconds). Requires `pip install websockets requests`.

## Three Scanning Modes (New — 2025-06)

The token scanning workflow now has three tiers, from fastest/riskiest to slowest/safest:

### Mode 1: Real-Time WebSocket Sniper (`snipe` / `pantau`)
- **Source:** `wss://pumpportal.fun/api/data` → `subscribeNewToken`
- **Speed:** Sub-second from token creation
- **MCap range:** ~28-35 SOL (bonding curve launch price)
- **Pros:** Catch tokens BEFORE any pump — maximum upside
- **Cons:** RugCheck useless (bonding curve = top1 80-100%); high scam rate; no holder/social data
- **Script:** `~/.hermes/scripts/pumpfun_sniper.py` — runs N seconds, prints filtered tokens
- **Best for:** Gambling on brand-new launches, catching the next 100x before anyone else

### Mode 2: gmgn-cli `market trenches` (PREFERRED ⭐)
- **Source:** gmgn.ai API via `gmgn-cli` (npm package, needs `GMGN_API_KEY`)
- **Speed:** Near real-time with smart filters
- **Key differentiator:** Filters by smart money count, KOL count, bundle%, sniper%, rug ratio — data DexScreener doesn't have
- **Command:** `gmgn-cli market trenches --chain sol --type new_creation --filter-preset smart-money --max-rug-ratio 0.3`
- **Presets:** `safe` / `smart-money` / `strict`
- **Setup:** `npm install -g gmgn-cli` + API key from https://gmgn.ai/ai
- **Skills catalog:** 51 AI trading skills at `https://gmgn.ai/static/opstatic/skills.json` (cached at `~/.hermes/data/gmgn_skills.json`)
- **Reference:** `references/gmgn-cli-workflow.md`

### Mode 3: DexScreener + RugCheck (`scan micin`)
- **Source:** DexScreener API + RugCheck API
- **Speed:** 30min-6h delay (token already pumped 200-700% by then)
- **Pros:** Full safety data, entry plans with support/resistance
- **Cons:** Late to the party; RugCheck rejects most early tokens
- **Reference:** `references/cli-scan-workflow.md`

### Mode 4: Fresh Token Scan — Age-First (`token fresh`, `token baru`)
- **Source:** DexScreener token-profiles + boosts + keyword search → RugCheck
- **Speed:** 30min-3h tokens (DexScreener latency floor)
- **Key difference from Mode 3:** Sort by AGE (newest first), not quality score. FDV range is wider ($1K+). Minimal other filters — freshness IS the filter.
- **When user says:** `token fresh`, `token baru`, `yang terbaru`, `cari token baru launch`
- **Pipeline:** Same DexScreener + RugCheck as Mode 3, but `pairCreatedAt` timestamp drives the sort order. Filter age < 3 hours, FDV > $1K, buys > 10.
- **RugCheck interpretation differs:** Top1 > 80% on < 1h token = bonding curve (normal). Top1 < 30% on < 1h = graduated AND distributed (very bullish). Holders < 20 on < 1h = normal.
- **Reference:** `references/cli-scan-workflow.md` (Mode C section)

### Mode Selection Guide

| Trigger | Mode | When to Use |
|---------|------|-------------|
| `snipe` | Mode 1 (WS) | Ultra-early, gambling, 28 SOL entry |
| `scan micin` | Mode 3 (DexScreener) | Established tokens, want entry plans |
| `gmgn` / `trenches` | Mode 2 (gmgn-cli) | Smart money filtered, best balance |
| `token fresh` / `token baru` | Mode 4 (Age-First) | Newest tokens, age-first sort |

## Critical pitfalls

### CA Verification Before RugCheck (June 2026 lesson)

**Contract addresses from DexScreener token-profiles/boosts are sometimes truncated or from wrong DEXes.** When you get a CA from the initial scan and run RugCheck on it, you may get empty/zero data (holders=0, top1=0%, lp_locked=0%) — this means the CA is wrong, not that the token is unsafe.

**Mandatory verification step before RugCheck:**
```python
# WRONG: Use CA directly from token-profiles scan
resp = requests.get(f"https://api.rugcheck.xyz/v1/tokens/{ca_from_scan}/report")

# RIGHT: Re-search DexScreener to get the correct CA first
resp = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={token_symbol}")
for pair in resp.json().get('pairs', []):
    if pair.get('chainId') == 'solana' and pair.get('dexId') in ('pumpfun', 'pumpswap', 'raydium'):
        correct_ca = pair['baseToken']['address']
        # Now use correct_ca for RugCheck
```

**Why this happens:** DexScreener sometimes returns CAs from meteora or other DEXes that have different addresses for the same token, or the CA gets truncated in the profiles endpoint response.

**Red flag:** If RugCheck returns `score: 999`, `holders: 0`, `top1: 0%`, `lp_locked: 0%` — the CA is almost certainly wrong. Re-verify before reporting.

### Multi-Pick Delivery Pattern

When user asks "selain X apalagi yang bagus" (what else is good besides X), they want **multiple ranked alternatives**, not just the #1 pick. Deliver:

1. **Top 3 picks** ranked by quality score
2. Each with: Safety score, RugCheck summary, holders, Top1%, B/S ratio, FDV, live price
3. **Quick comparison table** (safety, top1%, holders, B/S, FDV columns)
4. **Clear recommendation** ("Paling aman: X, Highest risk/reward: Y")
5. Each with full CA for Jupiter entry

Don't just re-scan — use the data from the initial scan and run RugCheck on the top 3-5 alternatives.

### PumpSwap — Graduated Token DEX

**PumpSwap (`pumpswap`) is now a major DEX for graduated pump.fun tokens.** When filtering by DEX, include `pumpswap` alongside `pumpfun` and `raydium`. Tokens on PumpSwap have graduated from the bonding curve and have real LP pools (unlike bonding curve `pumpfun` where liquidity is in the curve itself).

```python
# Correct DEX filter for graduated tokens
if dex not in ('pumpfun', 'pumpswap', 'raydium'):
    continue
```

**Key difference:** On `pumpfun`, the top holder is usually the bonding curve (80-95% is normal). On `pumpswap`/`raydium`, the bonding curve is gone and top holder % reflects real distribution. Top1 < 25% on `pumpswap` = excellent distribution.

### DexScreener API is too slow for truly early tokens.

By the time a pump.fun token appears in DexScreener's token profiles endpoint, it typically already has 100+ txns and has pumped 300-700%. The endpoint surfaces tokens AFTER they've gained significant volume.
**DexScreener surfaces tokens only after they've gained significant volume.** By the time a pump.fun token appears in the token profiles or pair endpoints, it typically already has 100+ transactions and has pumped 300-700%. For genuine early detection (0-30 min post-launch), use Mode 2 (WebSocket `subscribeNewToken`) — NOT REST APIs.

### RugCheck Useless on Sub-1-Minute Tokens (Bonding Curve)
**For tokens < 1 minute old, RugCheck's holder/distribution analysis is MEANINGLESS:**
- Top1 holder is always 80-100% because the bonding curve IS the top holder
- RugCheck score is always high — concentrated ownership triggers danger flags
- This is NORMAL for all legitimate new tokens on pump.fun

**What IS useful at launch:** mint authority check, freeze authority check, name quality.
Full safety analysis only becomes meaningful 5-15 minutes after launch when trading distributes supply.

### Token-2022 Detection
If RugCheck returns `tokenProgram: "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"`, the token uses Token-2022 (not standard SPL). Token-2022 supports hidden features like transfer taxes, permanent delegate, and clawback authority. **ALWAYS flag this in analysis output** — it's not automatically a scam (many pump.fun tokens now use Token-2022), but the user MUST be aware.

### Zero-Result Scan Fallback (Transparent Mode)
When safety filters return 0 candidates, **do NOT silently report "nothing found."** Switch to transparent mode:
1. Relax all filters (FDV $1.5K-$60K, top1 < 55%, RC score < 6000, lp_locked ≥ 90%)
2. Show ALL candidates with their issues explicitly flagged as 🚨/⚠️
3. Let the user see the market reality and decide

This prevents the "market looks dead" false impression when the issue is over-filtering.

### Scam Token Detection (Impossible Data)
Key signals of manipulated/fake tokens:
- **FDV > $1B with volume < $100K** — mathematically impossible for real tokens
- **LP Total = $0 on non-bonding-curve DEX** (pumpswap, raydium) — no real liquidity
- **Holder percentages > 100%** — corrupt supply calculation, often honeypot
- **RugCheck score > 1,000,000** — extreme danger, auto-skip
- **All top holders = burn addresses** (`11111111111111111111111111111111`) — supply is burned/minted to void

When encountering a token name that matches multiple contracts, show BOTH and clearly label which is the scam. Users often hear a name and don't know which CA is the real one.

### Entry Zone Calculation for Pumped Tokens
See `references/entry-zone-calculation.md` for the Fibonacci-based method. Core approach:
1. Calculate launch price from 24h change reversal
2. Apply Fibonacci retracement (0.236 / 0.382 / 0.5 / 0.618 / 0.786)
3. Map to FDV levels
4. Check 5m momentum (B/S ratio, price change %) to determine STATUS
   - 5m > +10% + B/S > 2x → "MASIH PUMPING KERAS — WAIT"
   - 5m +3-10% → "MASIH NAIK — TUNGGU KOREKSI"
   - 5m < -2% → "SUDAH KOREKSI — pantau support"
   - Else → "SIDEWAYS — bisa mulai akumulasi"


---

## Resources

- [Pump.fun WebSocket API (pumpportal.fun)](https://pumpportal.fun)
- [Solana Web3.js Docs](https://solana-labs.github.io/solana-web3.js/)
- [Phantom Wallet Developer Docs](https://docs.phantom.app/solana/detecting-the-provider)
- [Rugcheck.xyz](https://rugcheck.xyz) — automated rug detection
- [Solscan.io](https://solscan.io) — Solana blockchain explorer
- [Birdeye.so](https://birdeye.so) — DEX analytics and charts
