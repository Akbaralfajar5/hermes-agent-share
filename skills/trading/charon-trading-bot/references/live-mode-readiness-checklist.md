# Live Mode Readiness Checklist (May 2026)

## Decision Framework: When to Move from Dry-Run to Live

### Prerequisites

**1. Wallet Balance Check**
```bash
node --input-type=module - <<'NODE'
import { Keypair, Connection } from '@solana/web3.js';
import bs58 from 'bs58';

const privKeyStr = process.env.SOLANA_PRIVATE_KEY;
const keypair = Keypair.fromSecretKey(bs58.decode(privKeyStr));
const conn = new Connection(process.env.SOLANA_RPC_URL, 'confirmed');
const balance = await conn.getBalance(keypair.publicKey);
console.log('Balance:', (balance / 1_000_000_000).toFixed(4), 'SOL');
NODE
```

**Required balance:** `max_open_positions × position_size_sol + 0.1 SOL reserve`

Example:
- 3 positions × 0.05 SOL = 0.15 SOL exposure
- + 0.1 SOL reserve = **0.25 SOL minimum**

**2. Strategy Performance Baseline**

Before live, collect at least **20–30 closed trades** in dry-run to establish:
- Win rate (target: >30% for asymmetric meme coin strategy)
- Avg win % vs avg loss %
- Reward/risk ratio (target: >2.0x)
- Realized PnL trend (should be positive or near-breakeven)

**Example acceptable baseline (May 2026):**
- 102 trades, 36.3% WR, +0.0997 SOL realized
- Last 24h: 69 trades, +0.1209 SOL
- Unrealized peak: +0.1324 SOL
- Combined: +0.2321 SOL

**3. Exit Strategy Validation**

Confirm that:
- Partial TP fires at expected threshold (e.g., +50%)
- Trailing arm activates (e.g., +80%)
- Trailing exit triggers (e.g., 35% drop from peak)
- SL executes near target (e.g., -20%, not -50%)

Check logs for exit reason distribution. If all exits are one type (e.g., all SL, no trailing), strategy may be misconfigured.

### Live Mode Configuration

**Conservative (Recommended First)**
```json
{
  "position_size_sol": 0.05,
  "max_open_positions": 3,
  "max_exposure": 0.15,
  "wallet_requirement": 0.25
}
```

**Aggressive (After 48h+ live validation)**
```json
{
  "position_size_sol": 0.1,
  "max_open_positions": 5,
  "max_exposure": 0.5,
  "wallet_requirement": 0.6
}
```

### Slippage Reality Check

**Dry-run vs Live differences:**

| Factor | Dry-Run | Live |
|--------|---------|------|
| Entry slippage | 0% (estimated) | 2–5% (low mcap) |
| Exit slippage | 0% (estimated) | 3–5% (normal) |
| Panic dump exit | 0% (estimated) | 10–30% (rug) |
| Avg loss impact | -17% | -22% to -35% |

**Math adjustment:** If dry-run shows +0.1 SOL over 24h, expect ~50% reduction in live mode due to slippage. Realistic live: +0.05 SOL / 24h.

### Transition Steps

1. **Verify wallet balance** (must be ≥ requirement)
2. **Update `.env`:** `TRADING_MODE=live`
3. **Update strategy config:**
   ```js
   config.position_size_sol = 0.05;
   config.max_open_positions = 3;
   ```
4. **Restart bot:** `pm2 restart charon --update-env`
5. **Monitor first 3 entries:**
   - Check Telegram for live BUY notifications
   - Verify swap executed on-chain (check Jupiter history)
   - Monitor exit (partial TP, trailing, SL)
6. **After 24h live:**
   - Compare realized PnL vs dry-run baseline
   - If WR drops >10%, revert to dry-run and debug
   - If WR stable, continue monitoring

### Abort Criteria (Revert to Dry-Run)

- Realized PnL negative after 10+ trades
- Win rate drops below 20%
- Slippage consistently >10% worse than expected
- Any swap failures or execution errors
- Wallet balance drops below 0.1 SOL

### Session Example (May 15, 2026)

User moved to live mode after:
- 102 dry-run trades, 36.3% WR, +0.0997 SOL realized
- Wallet: 0.2268 SOL (sufficient for 3 × 0.05 SOL config)
- Exit strategy: partial TP +50%/30%, trailing arm +80%, trailing 35%, SL -20%
- Config: `position_size_sol: 0.05`, `max_open_positions: 3`

**Decision:** Conservative live mode approved. Baseline established, wallet sufficient, strategy validated.
