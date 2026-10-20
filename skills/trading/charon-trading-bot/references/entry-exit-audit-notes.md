# Entry / Exit Audit Notes

Session-derived checklist for auditing Charon execution logic.

## Highest-risk bug classes seen in practice

### 1. Live manual close using proxy PnL instead of realized swap output
- Symptom: manual sell executes on-chain, but `pnl_percent` / `pnl_sol` are stored from market-cap ratio.
- Why it matters: fee, slippage, and MEV make market-cap-derived PnL diverge from wallet reality.
- Audit rule: any live close path should prefer actual swap output / realized received amount.

### 2. Partial TP flags flipped before sell success
- Symptom: `partial_tp_done` becomes true before the partial sell succeeds.
- Why it matters: one transient sell failure can permanently disable future partial TP attempts for that position.
- Audit rule: flip partial-TP completion flags only after confirmed execution and durable state update.

### 3. Partial TP proceeds not accumulated into final position PnL
- Symptom: token balance is reduced after a partial sell, but realized partial proceeds are not stored anywhere used by final-close accounting.
- Why it matters: final PnL overstates or understates total performance because it only measures the last exit leg.
- Audit rule: store cumulative realized proceeds or realized PnL from each partial exit and include them in final totals.

### 4. Dry-run behavior diverges from live for partial exits
- Symptom: dry-run marks `partial_tp_done` but does not reduce simulated exposure or record a partial trade.
- Why it matters: strategy tuning becomes misleading because dry-run and live are no longer comparable.
- Audit rule: either simulate the economic effect in dry-run or document clearly that dry-run omits it.

### 5. Manual buy bypassing fresh execution revalidation
- Symptom: Telegram/manual buy uses stale candidate snapshot instead of running the same refresh-and-filter pass as auto-entry.
- Why it matters: users can enter positions that current filters would reject.
- Audit rule: manual buy, confirm flow, and auto-entry should converge on one fresh pre-execution validation path.

### 6. Duplicate live buy race between swap execution and DB dedupe
- Symptom: external swap is executed before local dedupe / insert, so concurrent triggers can buy twice while only one position is recorded.
- Why it matters: real wallet exposure exceeds tracked exposure.
- Audit rule: acquire per-mint lock or perform atomic dedupe before side effects.

### 7. Confirmation size mismatch
- Symptom: Telegram intent screen shows `dry_run_buy_sol`, but live executor uses strategy `position_size_sol`.
- Why it matters: user confirms one risk amount while the bot trades another.
- Audit rule: confirmation UI, stored intent, and executor must share a single size source of truth.

## Files worth checking first in Charon
- `src/pipeline/orchestrator.js`
- `src/execution/positions.js`
- `src/execution/router.js`
- `src/db/positions.js`
- `src/db/intents.js`
- `src/telegram/commands.js`
- `src/telegram/callbacks.js`

## Fast audit sequence
1. Inspect position creation for TP / SL / trailing / partial-TP fields.
2. Trace auto-entry, manual entry, and confirm flow to see whether all paths run fresh validation.
3. Trace auto-exit and manual close separately.
4. Compare live accounting with actual Jupiter swap outputs.
5. Check whether partial exits mutate both token exposure and realized PnL state.
6. Review duplicate-entry protections around swap execution.
7. Cross-check Telegram/UI numbers against executor inputs.
