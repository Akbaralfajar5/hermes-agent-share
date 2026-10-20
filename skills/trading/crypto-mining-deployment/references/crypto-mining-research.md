---
name: crypto-mining-research
description: Research and evaluate cryptocurrency mining opportunities - Discord analysis, ROI calculation, risk assessment, and go/no-go decisions
dependencies: [browser_vision, web_search]
---

# Crypto Mining Research & Evaluation

Systematic approach to evaluate new mining opportunities before committing GPU/VPS resources.

## Research Workflow

### Phase 1: Initial Discovery (5 min)

Gather basic facts:
- **Reward structure**: tokens per block, OTC price, block value
- **Hardware requirements**: GPU model, VRAM, architecture-specific features
- **Rental costs**: $/hour for required hardware
- **Community size**: Discord members, active miners

**Red flags (immediate skip):**
- No public community or ghost Discord
- Reward structure unclear or "TBA"
- Hardware requirements exceed datacenter GPUs (H100/H200)
- No OTC market or price discovery

### Phase 2: Community Analysis (30 min)

**Discord deep-dive:**

1. **Join Discord** and check these channels:
   - `#mining` or `#general` - recent 50 messages
   - `#announcements` - pinned messages + last 10 posts
   - `#help` or `#support` - common issues

2. **Search for success signals:**
   - `"block found"` - how often? by whom?
   - `"<GPU_MODEL>"` - what setups are people using?
   - `"profit"` or `"ROI"` - are people making money?
   - `"gave up"` or `"stopped"` - why did they quit?

3. **Extract key metrics:**
   - **Average block time** (single GPU): "found block after X hours"
   - **Success rate**: % of miners reporting blocks found
   - **Common failures**: setup issues, rejection rates, network problems
   - **Optimization tips**: flags, configs, tricks from successful miners

**Critical questions to ask in Discord:**
```
Hey! Researching [PROJECT] mining before renting GPU. Quick questions:

1. Average time to find 1 block with single [GPU_MODEL]?
2. How many blocks found daily on the network?
3. Is pool mining available?
4. Current network difficulty/hashrate?
5. Any [GPU_MODEL] optimization tips?

Trying to calculate ROI before committing. Thanks!
```

### Phase 3: On-Chain Analysis (15 min)

**Block explorer investigation:**

1. **Recent blocks** (last 24 hours):
   - Block frequency (blocks/hour)
   - Unique miner addresses (centralization check)
   - Block rewards (verify claimed amounts)

2. **Network stats:**
   - Total hashrate (if available)
   - Difficulty trend (increasing = harder to mine)
   - Miner distribution (Gini coefficient)

3. **Red flags:**
   - Single address mining >50% of blocks (centralization)
   - Blocks found in bursts (selfish mining attack)
   - Long gaps between blocks (network stalled)

### Phase 4: ROI Calculation (10 min)

**Probability modeling:**

```python
# Inputs from research
block_reward_usd = 980  # tokens × OTC price
gpu_cost_per_hour = 6
avg_block_time_hours = 72  # from Discord data
success_rate = 0.20  # % of miners who found blocks

# Scenarios
best_case_hours = avg_block_time_hours * 0.5
avg_case_hours = avg_block_time_hours
worst_case_hours = avg_block_time_hours * 3

# Costs
best_case_cost = best_case_hours * gpu_cost_per_hour
avg_case_cost = avg_case_hours * gpu_cost_per_hour
worst_case_cost = worst_case_hours * gpu_cost_per_hour

# Profits
best_case_profit = block_reward_usd - best_case_cost
avg_case_profit = block_reward_usd - avg_case_cost
worst_case_profit = block_reward_usd - worst_case_cost

# Expected Value
ev = (success_rate * avg_case_profit) + ((1 - success_rate) * -avg_case_cost)
```

**Break-even analysis:**
```
Break-even hours = block_reward_usd / gpu_cost_per_hour
```

If `avg_block_time_hours > break_even_hours`: **negative EV, skip**

### Phase 5: Risk Assessment

**Risk factors:**

| Factor | Weight | Score (1-5) | Notes |
|--------|--------|-------------|-------|
| Success rate from Discord | 30% | ? | 0% = 1, 50%+ = 5 |
| Network centralization | 20% | ? | >50% single miner = 1 |
| Technical complexity | 15% | ? | Plug-and-play = 5, expert setup = 1 |
| Block rejection rate | 15% | ? | >50% rejected = 1 |
| Community health | 10% | ? | Active support = 5, ghost town = 1 |
| Hardware availability | 10% | ? | Common GPUs = 5, H200 only = 2 |

## Decision Framework

### GO Criteria (all must be true):

1. ✅ **Positive EV**: Expected value > $0
2. ✅ **Success stories**: ≥3 Discord users report blocks found
3. ✅ **Reasonable time**: Average block time < 7 days
4. ✅ **Low rejection**: <30% blocks rejected
5. ✅ **Active community**: Recent messages in #mining (<24h old)

### NO-GO Signals (any one is enough):

1. ❌ **Zero success rate**: No Discord users report blocks despite trying
2. ❌ **Selfish mining**: Block explorer shows centralization attack
3. ❌ **Extreme rejection**: >50% blocks rejected/stale
4. ❌ **Negative EV**: Expected value < -$50
5. ❌ **Ghost community**: No recent activity in Discord

### TEST-FIRST Approach

When uncertain (medium risk):

1. **Rent minimum GPU** (1x, lowest tier that meets requirements)
2. **Test duration**: 6-12 hours
3. **Test budget**: $20-50 max
4. **Success criteria**:
   - ✅ "Block found" messages appear in logs
   - ✅ Blocks submitted to network
   - ✅ At least 1 block accepted (not rejected)
5. **Scale decision**:
   - If 0 blocks found in test → STOP (setup issue or bad luck)
   - If blocks found but 100% rejected → STOP (network issue)
   - If ≥1 block accepted → SCALE to 2-3 GPUs

## BSC / EVM PoW Token Research Checklist

When user shares a new PoW token on BSC or other EVM chain, quickly evaluate:

1. **Source code check** — Is the miner open source? What algorithm? (Keccak-256, SHA-256, Ethash, etc.)
2. **Hardware requirement** — GPU vs CPU? For keccak256 → GPU massively outperforms CPU (100-1000x)
3. **Gas fees** — Every PoW submit = on-chain TX = needs native token for gas. User needs BNB (BSC), ETH (Ethereum), etc. Budget $5-10 for hundreds of submits.
4. **Fair launch check** — No premine, no admin keys, no team allocation, contract not upgradeable → good signs
5. **Halving schedule** — Early era = higher rewards. Check % mined so far to estimate timing advantage
6. **Difficulty adjustment** — How often? Every N epochs? Dynamic? Affects mining strategy
7. **One-submit-per-challenge** — Does the protocol prevent duplicate submits? (saves gas)

**Quick research flow:**
```
GitHub repo → check algorithm (src files)
→ check if GPU miner exists (OpenCL/CUDA)
→ check contract on explorer (has bytecode? verified?)
→ check dashboard (total mined %, difficulty, era)
→ estimate ROI (reward × price - gas cost - rental cost)
```

**Example:** SAT (Satoshi) on BSC — Keccak-256, GPU via OpenCL, 50 SAT reward, ~7.76% mined, difficulty 25K, needs BNB for gas.

## Case Study: Pearl Mining

**Initial appeal:**
- $980 per block (2,800 tokens × $0.35)
- H100/H200 requirement (available on rental platforms)

**Research findings:**
- Discord: 0% success rate (3x H200 9h, 2x H200 10h, 1x H200 20h = $0)
- Selfish mining attack active (blocks found in bursts)
- 100% rejection rate (James Bond: 24 found, 0 accepted)
- Expected Value: -$120 to -$500

**Decision:** NO-GO

**Reasoning:** Despite $980 reward, probability of success is near-zero based on community data. Multiple H200 setups failed to earn anything. Network compromised by selfish mining. Better to buy PEARL tokens directly at $0.35 OTC.

**Lesson:** High reward doesn't matter if probability is zero. Discord testimonials > marketing claims.
