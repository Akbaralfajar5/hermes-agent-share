# Past Project Reviews — Pattern Reference

## TickUp Fun (tickup.fun) — Jul 2026
**Score: 5/10**
**Type:** SocialFi + RWA (friend.tech fork + tokenized stock rewards)
**Chain:** Robinhood Chain Testnet (Arbitrum Orbit, chain ID 46630)

**Mechanics:**
- Bonding curve keys: `price = supply² ÷ 16000` ETH
- 1% fee per trade (buy & sell)
- Fee split: Creator 35%, RWA rewards 35%, Protocol 20%, Referrer 10%
- $TICK token with buy & burn
- RWA weighted by cost basis (anti-sybil)

**Red flags:**
- 🟡 Testnet only — ETH from faucet, tokenized stocks are placeholders
- 🟡 friend.tech fork — original model failed (volume -99%)
- 🟡 Chat feature "not shipped yet" — core utility missing
- 🟡 RWA provider unclear
- 🟡 No contract address visible in docs

**Verdict:** Farm testnet, zero capital risk. Don't expect guaranteed mainnet.

---

## ColibriSwap (colibriswap.com) — Jul 2026
**Score: 2/10**
**Type:** Privacy swap aggregator (mixer rebrand)
**Chain:** Claims 100+ chains

**Mechanics:**
- "Private Swap" = 2-leg routing via 2 exchanges + intermediary L1 token
- Non-custodial claim BUT uses deposit addresses
- No wallet connect needed (paste address)
- "All-in" fees (non-transparent)
- 10-30 min for private, 1-4 min for fast

**Red flags:**
- 🔴 Deposit address model = custodial moment (they hold your funds temporarily)
- 🔴 No audit, no team dox, no GitHub
- 🔴 Identical to known scam mixer pattern
- 🔴 Fee structure hidden behind "all-in quote"
- 🔴 "Newly launched" per own docs
- 🟡 Robinhood Chain support (unknown ecosystem)
- 🟡 Buzzword-heavy landing page without technical backing

**Verdict:** Do NOT deposit. High scam probability. If you need private swaps, use THORChain, Railgun, or Aztec.

---

## Pattern: How to spot a mixer rebrand scam
1. Claims "non-custodial" but requires deposit to their generated address
2. No smart contract audit or open source code
3. "Privacy-first" without ZK proofs
4. 2-exchange intermediary routing (= just a mixer)
5. Anonymous team
6. Freshly launched, no track record
7. Fees hidden in "all-in" quotes

## Pattern: SocialFi bonding curve (friend.tech model)
- Historical failure rate: ~95% of forks die within 6 months
- Core problem: no sustainable utility beyond speculation
- What to look for in a viable fork: real yield mechanism (not just trading fees), genuine utility (not "chat coming soon"), mainnet with real assets
- Score ceiling for testnet-only SocialFi: 6/10 max

---

## Pattern: 🟠 LIVE BUT ZERO TRACTION (most common verdict for new chain projects)

Two real reviews from 13 Sep 2026, both on Robinhood Chain mainnet (4663). Both had real
contracts, honest marketing numbers, working frontends — and zero users. This pattern
repeats constantly on new chains, so recognise it fast.

### Qelora (qelora.net) — launchpad with programmable rules
**Verdict: 🟠 LIVE, ZERO TRACTION — intriguing product, no docs, never used**

What it is: launchpad where tokens get ongoing `IF → THEN` rules (trigger: someone buys /
fees generated / mcap hits $100K / volume milestone → action: route fees to liquidity /
distribute to holders / burn / unlock a new rule / buyback / change future fee split).

Evidence gathered (all tool-verified, none copy-pasted from the site):
- Contract `0x9934ad7dd30d7E3fCE54DDE1ce60a1Af92E7edaC`, `eth_getCode` = 26.636 hex chars → real
- `owner()` = `0x4f5bbe1a728ca595670b5e14dda330ac3ef7ab0d` (EOA, nonce 71)
- `launchFee()` = 1e15 wei = 0,001 ETH — **matches the site's claim exactly** ✅
- `launchCount()` = **0** → not a single token ever launched
- ABI `launch()` extracted from the JS bundle (nested tuple: stages[cond, threshold, feeBps, legs[action, bps, dest]])
- 6 embedded bytecode blobs (798–11.188 chars) = token templates deployed client-side
- `/docs`, `/whitepaper`, `/about` all 404; Vercel deploy `last-modified` hours old

Lesson: honest numbers + real contract + zero usage. Neither "scam" nor "good project",
and the report must say exactly that.

### Stockless (stockless.fun) — tokenized-stock liquidity vaults
**Verdict: 🟠 LIVE, ZERO TRACTION — better documented, equally empty**

Docs claim TVL, a live harvest cycle since 7 Sep 2026, and a graduated token. The site's
own Pools page renders `TVL $0 · 0 cycles · distributed $0` — the frontend was honest.
On-chain confirmed it:
- `$STOCKSS` `0x7bC5ff817462b8c8185FAC5c8834F0561FC33f27`: `name()`=STOCKLESS, `symbol()`=STOCKSS, `decimals()`=18, `totalSupply()`=1.000.000.000 (fixed supply claim ✅)
- Harvest `0x64f55d15b7074d527108001894c3937c78bc9161`: **balance 0 ETH**, `balanceOf` = **0 STOCKSS** → no funds under management at all
- Fee wallet `0x8151…0476`: nonce `0x61` (97 tx — the keeper genuinely runs), balance ~0,0021 ETH
- DexScreener pair: `price $0,00000348 · FDV $3.479 · liq $5.482 · vol 24h $32,86 · txns 24h 1 buy / 8 sell`

Lesson: the fee wallet having 97 transactions proves the keeper loop works. A running keeper
with zero fees is a very specific and very loaded signal — the machine is on, nobody is
using it. Worth calling out explicitly.

### Checklist distilled from both
1. `eth_getCode` → is it deployed?
2. `eth_getTransactionCount` on the contract → `0x1` = deploy only
3. `eth_call` the marketing numbers (`launchFee`, `totalSupply`, counts) → do they match?
4. Key counters (`launchCount()`, holder count, TVL) → zero?
5. DexScreener `txns.h24` + volume → is anyone actually trading?
6. Are the docs pages 404? (thin product surface, not necessarily a scam)
7. Report as `🟠 LIVE, ZERO TRACTION` — real code, real contract, zero users

---

## Pattern: 🟠 TEMPLATE LAUNCH (no contract at all — judge the site, not the chain)

The third review type. DePIN / AI / SaaS-style projects have nothing to `eth_call`, so the
verdict comes from **who built the site and whether the reward token is tradable anywhere**.

### OrbitAI DPN (orbitaidpn.com) — bandwidth-sharing DePIN on Unicorn Ultra
**Verdict: 🟠 TEMPLATE LAUNCH — real subnet underneath, amateur wrapper on top**

What it is: share unused internet bandwidth as a "Contributor Node", earn AWD tokens; clients
buy bandwidth pay-as-you-go. Built on the AWD subnet of Unicorn Ultra Network (U2U).

Evidence gathered (all tool-verified):

| Check | Command / source | Result |
|---|---|---|
| Domain age | `rdap.verisign.com/com/v1/domain/orbitaidpn.com` | registered 7 Jan 2025 (~20 months) |
| **Site builder** | `curl -skI` → `x-powered-by: HostingerWebsiteBuilder`, `platform: hostinger` | 🔴 drag-drop AI builder, not engineering |
| **Brand mismatch** | HTML `<title>` + JSON-LD `"name"` = `AZUREWAVE`; visible product = `OrbitAI DPN` | 🟠 template leftover, unproofread |
| Docs host | `azurewave.gitbook.io/azurewave` — GitBook path is ALSO `azurewave` | 🟠 brand mismatch in docs too |
| **Docs freshness** | GitBook footer | **"Last updated 1 year ago"** while site modified 11 days ago |
| Docs images | pulled from `docs.u2dpn.xyz` (different project's domain) | 🟠 copy-paste chain |
| Reward token | `api.dexscreener.com/latest/dex/search?q=AWD` | **no matching pair** — rewards uncashable |
| Claimed stats | own landing page | 49K total nodes / **1,3K active** (2,6% — severe churn) / 7 validators |

**The headline finding is the untradable reward token:** the user would burn real data quota
and battery sharing bandwidth for AWD tokens that have no market. That goes first in the
report, not as a footnote.

**Second finding:** a 7-validator network advertised as "fully decentralized" — the
decentralization claim is cosmetic, and the shared-bandwidth model carries a genuine legal
exposure for the user (their IP appears in logs for traffic they relayed).

**Residual risk pattern for any bandwidth/relay DePIN** (state this explicitly when advising):
- User's own IP is the egress for someone else's traffic → legal exposure if that traffic is illegal
- "Risk-free passive income" in the copy is itself a red flag — nothing is risk-free
- Validator count is the decentralization reality check: 7 nodes = one operator in practice

### Checklist distilled (no-contract projects)
1. `curl -skI` → is `x-powered-by` an AI/website builder? → 🟠 template launch
2. Does HTML `<title>` / JSON-LD `"name"` match the product name? → leftover = unproofread
3. RDAP domain age → young = thin track record
4. GitBook/GitHub `last updated` → "1 year ago" on an active site = docs are dead
5. **DexScreener search the reward symbol → no pair = farming is unpaid labour**
6. Claimed node/validator counts → active-vs-total ratio exposes churn
7. Report as `🟠 TEMPLATE LAUNCH` and say: real infra possibly underneath, wrapper is not built

**Distinguish the two 🟠 labels — never merge them:**
- `LIVE, ZERO TRACTION` (Qelora, Stockless) = genuine engineering, no users yet → worth watching
- `TEMPLATE LAUNCH` (OrbitAI) = no engineering, template + copywriting → don't spend effort

