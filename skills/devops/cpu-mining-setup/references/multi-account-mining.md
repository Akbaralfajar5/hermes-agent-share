# Multi-Account Mining Analysis

## Thread Distribution Behavior

rpow2 Rust miner (rizkypujir/miner) reads `accounts.txt` with one cookie per line and **divides total threads equally** among all accounts.

### Performance Impact

| Accounts | Threads/Account | Speed/Account | Total Blocks/Min | Notes |
|----------|----------------|---------------|------------------|-------|
| 1 | 6 | 0.06-0.47s/block | ~20 | Baseline |
| 2 | 3 | 0.12-0.94s/block | ~20 | 2x slower per account |
| 3 | 2 | 0.18-1.41s/block | ~20 | 3x slower per account |
| 6 | 1 | 0.36-2.82s/block | ~20 | 6x slower per account |

**Key Finding:** Total output remains constant regardless of account count. Multi-account splits threads but does not increase total mining throughput.

## When Multi-Account Is Worth It

### Benefits
- **Diversification** — if one account banned, others continue
- **Referral bonuses** — if mining platform has referral program
- **Airdrop multipliers** — if snapshot rewards scale per account
- **Withdraw limit bypass** — if per-account withdrawal caps exist

### Drawbacks
- **Slower per account** — mining speed per account drops proportionally
- **Cookie management overhead** — need multiple emails/sessions
- **Ban risk** — multi-account farming may violate ToS
- **No earnings increase** — total blocks/min stays the same

## rpow2-Specific Recommendation

**Single account is optimal** for rpow2 because:
- No referral program detected
- No per-account limits observed
- No airdrop/snapshot mechanics announced
- Total output invariant to account count
- Simpler management (one cookie, one balance)

## Alternative Strategies for Higher Earnings

Instead of multi-account on one VPS:

### 1. Multiple VPS Instances
- Rent N VPS instances with 6 threads each
- Run 1 account per VPS
- Total: N × 6 threads, N accounts, **N× earnings**
- Cost: $101 × N per month

### 2. Larger VPS Instance
- Rent VPS with 32+ threads (full Threadripper)
- Run 1 account with all threads
- Faster mining speed per block
- Cost: $400-700/month (provider-dependent)

### 3. Current Setup (Recommended)
- 1 VPS, 6 threads, 1 account
- Cost: $101/month
- Earnings: ~13.44 rpow2/month (post-nerf)
- Wait for token listing to evaluate ROI

## Implementation Notes

If multi-account is still desired despite invariant output:

```bash
# Create accounts.txt with multiple cookies
cat > ~/rpow2-mining/accounts.txt << EOF
rpow_session=ACCOUNT_1_TOKEN
rpow_session=ACCOUNT_2_TOKEN
rpow_session=ACCOUNT_3_TOKEN
EOF

# Restart mining
cd ~/rpow2-mining
./stop.sh && ./start.sh

# Monitor per-account performance
tail -f mining.log | grep -E '\[.*@.*\]'
```

Each account will mine slower but total blocks/min remains ~20.

## Verification

Check thread distribution:

```bash
# Attach to mining session
screen -r rpow2

# Look for startup message showing threads per account
# Example output:
# [*] Accounts: 3
# [*] Total threads: 6
# [*] [user@example.com] Starting miner with 2 threads
# [*] [user@example.com] Starting miner with 2 threads
# [*] [user@example.com] Starting miner with 2 threads
```

Monitor mining speed per account in logs — should be proportionally slower.
