# Proxy + Staking Protocol Audit Patterns

Source: SSV Network v2.0.0 audit session (UUPS proxy + delegatecall modules, dual SSV/ETH accounting, PackedETH/PackedSSV precision types, oracle-based EB updates, cSSV staking rewards).

## Architecture Reading Order

For large proxy-based protocols:
1. CLAUDE.md / README for architecture overview
2. Proxy contract (routing, fallback, access control)
3. Storage libraries (slot definitions, struct layouts)
4. Core types / packed libs (precision factors, type conversions)
5. Module contracts (business logic)
6. Token contracts (hooks, mint/burn authority)

## Key Patterns Discovered

### PackedETH Dust Loss (Systematic Value Leakage)

When fees are tracked in PackedETH (uint64 * 100_000 scale factor):
- Network fee earnings computed as `(blocks * fee * vUnits) / BPS_DENOMINATOR`
- Result stored in PackedETH → aligned to 100_000 wei granularity
- Staking accumulator reads this as `newFeesWei = unpack(packedNewFees)`
- Then: `accEthPerShare += (newFeesWei * 1e18) / totalStaked`
- Two layers of truncation → dust permanently trapped in contract

Impact: ~100k wei per sync operation in worst case. Accumulates over protocol lifetime.

### cSSV Transfer Hook Settlement Correctness

CSSVToken uses `_beforeTokenTransfer` to call `SSVStaking.onCSSVTransfer(from, to, amount)`.
- Mint (from=0): hook skipped (correct — stake() already settled the user)
- Burn (to=0): hook skipped (correct — requestUnstake() already settled)
- Transfer: hook fires, settles both parties at PRE-transfer balances

Verify: `_settle(from)` reads `balanceOf(from)` which is still the old (full) balance.
After hook returns, ERC20 moves tokens. Next time, `from`'s index is current, so no double-count.

### Reentrancy Guard Cross-Module Sharing

The reentrancy guard uses a diamond storage slot shared across ALL modules. This means:
- `withdraw` (nonReentrant) → ETH transfer → reenter `deposit` → blocked by guard
- Even functions WITHOUT `nonReentrant` cannot be reentered via the ETH path if the calling function has the guard

Functions intentionally without guard must have NO external calls before state writes.
Verify: `deposit`, `migrateClusterToETH`, validator register/remove.

### Liquidation Check Timing After EB Update

When `updateClusterBalance` increases vUnits (EB went up):
1. Fees are calculated with OLD vUnits
2. New vUnits are stored
3. Liquidation check uses NEW vUnits (higher burn rate)
4. Cluster may become liquidatable immediately

This is an intended auto-liquidation path. The protocol handles it by calling `_liquidateAfterEBUpdateIfNeeded` which performs a full liquidation inline.

### Operator Deviation Accounting Invariant

```
For each operator:
  operatorEthVUnits[opId] = SUM(cluster_deviation) for all active clusters using that operator
  where cluster_deviation = max(0, storedVUnits - baseline)
  and baseline = validatorCount * BPS_DENOMINATOR
```

Verify this invariant is maintained across:
- Registration (deviation unchanged — only baseline changes via ethValidatorCount)
- Removal (deviation cleaned up when validatorCount hits 0)
- Liquidation (deviation removed in _executeLiquidation)
- EB update (delta applied symmetrically to all operators in cluster)
- Migration (deviation added if cluster had explicit EB tracking)
- Reactivation (deviation restored from stored ebSnapshot)

### Oracle Quorum Mechanics

- Fixed 4 oracle slots (MAX_DELEGATION_SLOTS)
- Weight = frozenSupply / 4 per vote
- Quorum = frozenSupply * quorumBps / 10000
- With 75% quorum → need 3 of 4 votes
- Supply frozen on first vote of each round (prevents manipulation)
- `hasVoted` is never deleted (prevents re-voting on same commitmentKey)
- After quorum reached: root stored, commitments/frozenSupply cleared

### claimEthRewards Precision-Lock (Confirmed Medium, July 2026)

```solidity
uint256 payout = claimable - (claimable % ETH_DEDUCTED_DIGITS); // 100_000
if (payout == 0) {
    if (userBalance == 0) {
        s.accrued[msg.sender] = 0; // ← dust permanently zeroed out
        emit RewardsClaimed(msg.sender, 0);
        return;
    }
    revert NothingToClaim();
}
```

**Scenario:** User accrues < 100,000 wei in rewards → unstakes all cSSV → calls claim → `payout = 0` and `userBalance == 0` → accrued zeroed permanently. Individual loss < $0.01 but systematic.

**General pattern:** Any accumulator that rounds at claim-time AND has a "cleanup on zero balance" branch creates permanent dust loss. Fix: preserve sub-precision remainders or allow full claim when exiting.

### Bug Bounty Report Formatting

When reporting to protocols:
1. Title: concise (e.g., "Precision loss in staking accumulator permanently locks dust")
2. Severity: Critical (fund drain) / High (significant loss) / Medium (limited loss or DoS)
3. Root cause: one paragraph with code references
4. PoC: step-by-step attack scenario with numeric examples
5. Impact: quantify (how much $ at risk, under what conditions)
6. Fix: specific code change recommendation
