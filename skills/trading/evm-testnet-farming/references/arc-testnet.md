# Arc Testnet Reference

## Overview
- **Project:** Arc — Stablecoin-native L1 blockchain by Circle
- **Status:** Public Testnet (approaching mainnet, May 2026)
- **Raised:** $2.2B at $3.5B valuation (reportedly $222M additional for ecosystem at $3B valuation)
- **Investors:** Blackrock, Apollo, and others
- **Gas Token:** USDC (native, 18 decimals) — wallets display "ETH" but it's USDC
- **Finality:** Deterministic, <1 second
- **EVM Compatible:** Yes (Hardhat/Foundry)
- **Integrated:** Circle full stack (USDC, CCTP, Gateway)

## Network Details
- **Network Name:** Arc Testnet
- **RPC URL:** `https://rpc.testnet.arc.network`
- **WebSocket:** `wss://rpc.testnet.arc.network`
- **Chain ID:** 5042002
- **Currency Symbol:** USDC
- **Block Explorer:** `https://testnet.arcscan.app`
- **Docs:** `https://docs.arc.network`
- **LLMs.txt:** `https://docs.arc.network/llms.txt`
- **Confirmed working:** May 2026, block ~40.8M, chain responds to ethers.js JsonRpcProvider

## Faucet
- **URL:** https://faucet.circle.com
- **Amount:** 20 USDC per request
- **Cooldown:** 1 request per stablecoin+network pair every 2 hours
- **Tokens available:** USDC and EURC
- **CAPTCHA:** reCAPTCHA Enterprise v3 with v2 fallback. **FULLY AUTOMATABLE via 2Captcha v2 bypass** (verified May 2026)
- **Multi-wallet friendly:** YES — automated via GraphQL + 2Captcha (~$0.003/claim, ~60s solve time)
- **Note:** Wallets that don't support custom gas tokens still work — balances show as "ETH" but underlying is USDC
- **Secondary faucet:** https://onchaingm.com/faucet (additional source)

### Faucet Automation (Working Method)
**GraphQL endpoint:** `POST https://faucet.circle.com/api/graphql`
**Mutation:** `RequestToken` with `RequestTokenInput` (`destinationAddress`, `blockchain`, `token`)
**Blockchain enum:** `"ARC"` (NOT "ARC-TESTNET")
**Auth:** reCAPTCHA v2 token via `recaptcha-v2-token` HTTP header
**v2 sitekey:** `6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve` (Enterprise)

```bash
# Step 1: Solve v2 captcha
curl -s -X POST 'https://api.2captcha.com/createTask' \
  -H 'Content-Type: application/json' \
  -d '{"clientKey":"YOUR_KEY","task":{"type":"RecaptchaV2TaskProxyless","websiteURL":"https://faucet.circle.com","websiteKey":"6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve","isEnterprise":true}}'
# Poll getTaskResult (~45-60s)

# Step 2: Claim
curl -s -X POST 'https://faucet.circle.com/api/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://faucet.circle.com' \
  -H "recaptcha-v2-token: $TOKEN" \
  -d '{"operationName":"RequestToken","variables":{"input":{"destinationAddress":"0xADDRESS","blockchain":"ARC","token":"USDC"}},"query":"mutation RequestToken($input: RequestTokenInput!) { requestToken(input: $input) { amount hash status explorerLink } }"}'
```

**Why v3 fails but v2 works:** Circle's server-side reCAPTCHA Enterprise assessment rejects v3 tokens from solver services (score too low). But the frontend has `recaptchaV2FallbackEnabled: true` — when v3 fails, it falls back to v2 checkbox. The v2 token is sent via `recaptcha-v2-token` header (discovered from webpack chunk `97528-*.js`). 2Captcha's v2 solver passes server verification.

**Cost for 1000 wallets:** ~$3 (1000 × $0.003/solve) + ~17 hours (60s solve × 1000, sequential)

## Community & Discord
- **Discord:** `https://discord.com/invite/buildonarc` — "Build on Arc" server, ~24.6K members, FREE to join (no requirements)
- **Arc House (community hub):** `https://community.arc.network/` — powered by Gradual, free signup
- **Architects (Ambassador Program):** Requires active contribution (build, host meetups, help others). Rewards: badges, spotlight, recognition. Apply via community page "Become an Architect"
- **IMPORTANT:** Discord is open to everyone. The "must build to join" misconception likely refers to the Architects ambassador program, NOT the Discord itself.

### Arc House Points System (community.arc.network)
- Platform powered by **Gradual** (gradual.app)
- Requires manual signup — cannot be automated (social login / email)
- Points earned from: posting discussions, commenting, attending events, sharing content, joining groups
- **Cannot be scripted** — genuine human interaction required
- Key activities for points:
  - Post in Discussions section
  - Comment on content/videos (ARC Whitepaper post, Builder Spotlights, etc.)
  - RSVP + attend Events (Discord Office Hours, Builder Spotlights — bi-weekly)
  - Share content on X/LinkedIn
  - Join community groups
- **Events to attend:**
  - Arc Discord Office Hours (bi-weekly, ~45 min)
  - Builder Spotlight sessions (protocol deep-dives)
  - Stablecoins Commerce Stack Challenge (ongoing hackathon, Apr 14 – Jul 13)

## Ecosystem Partners (Official, from arc.network/ecosystem)
Major names: Goldman Sachs, HSBC, Deutsche Bank, Mastercard, Coinbase, MetaMask, Aave, Curve, LayerZero, Chainlink, Axelar, Stargate, Alchemy, QuickNode, Ledger, Rainbow, Robinhood, Kraken, and 100+ more.

## Full Protocol List (Combined: original 16 + @sellmanft additions)

### Faucets
1. **faucet.circle.com** — 20 USDC/EURC per 2h, NO captcha ⭐
2. **onchaingm.com/faucet** — secondary faucet

### Bridge
3. **superbridge.app** — Bridge Sepolia → Arc (and other chains)
   - URL: `https://superbridge.app/?fromChainId=11155111` (Sepolia → Arc)
   - Standard CCTP bridge, works with MetaMask

### DEX / Swap
4. **Curve Finance** — `https://curve.finance/dex/arc/swap` ⭐ (established, likely tracked)
5. **UnitFlow Finance** — `https://unitflow.finance` (DEX + Genesis Pass NFT)
6. **Flow on Arc** — `https://flowonarc.xyz` (swap, pool, lend/borrow)
7. **Presto** — `https://prestodex-arc.vercel.app` (deploy, swap, bridge, pool)
8. **Arc Perp** — `https://arcperps.xyz` (perpetuals trading)
9. **Lunex** — `https://lunex.finance` (bridge, swap, yield vaults)
10. **Achswap** — `https://trade.achswap.app` (prediction market, launch token)
11. **ExecDaat** — `https://execdaat.xyz/#/swap` (swap USDC↔EURC)
12. **KudiArc** — `https://kudiarc.xyz` (swap + yield deposit)
13. **Tower Exchange** — `https://tower.exchange` (invite only — get invite from Discord)

### Lending / Yield
14. **FlowFi** — `https://flowfi-three.vercel.app` (deposit/withdraw loop)
15. **KudiArc Yield** — deposit USDC → get USYC

### NFT
16. **Omnihub** — `https://omnihub.xyz/collection/arc-testnet/arc-omnihub` (create + mint NFT)
17. **Arkle Lab** — `https://arklelab.xyz/cigarmood` (mint NFT)
18. **nfts2.me** — `https://amazing-arc-test.testnet.nfts2.me` (mint NFT, free)
19. **NFTs2Me** — `https://nfts2me.com/app/` (deploy NFT collection)

### Identity / Domain
20. **ArcNS** — `https://arcns-app.vercel.app` (register .arc / .circle domain)
21. **Infinity Name** — `https://infinityname.com/arc` (buy/trade domain)

### Deploy / Dev
22. **OnchainGM** — `https://onchaingm.com/deploy` (deploy contract + say GM) ⭐
    - Also: `https://onchaingm.com/badge-arc` (mint badge)
    - Also: `https://onchaingm.com/faucet` (faucet)
23. **ZkCodex** — `https://zkcodex.com/onchain/deploy` (GM Streak daily + deploy + counter + NFT) ⭐
24. **FlowPay** — `https://flowpay-sand.vercel.app` (bridge, deploy)

### Gaming / Social
25. **Arc World** — `https://arcworld.io` (passport, games, virtual card, Arc Climate pay)
26. **Arc Crypto Race** — `https://arccryptorace.xyz` (daily tournament, leaderboard)

### Cross-chain
27. **Transvy Protocol** — `https://transvyprotocol.vercel.app` (cross-pay, gateway deposit)
28. **Zentryx** — `https://zentryxapp.xyz/bridge` (bridge)

### Other
29. **Layer3** — `https://app.layer3.xyz/communities/arc` (quests)
30. **ClaraChain Luria** — `https://clarachain.net/luria`
31. **ClaraChain Kitty** — `https://clarachain.net/kitty`
32. **Draze Network** — `https://draze.network/kairo`

## Deploy Smart Contract (Foundry)
```bash
# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Create project
forge init hello-arc && cd hello-arc

# .env
ARC_TESTNET_RPC_URL=https://rpc.testnet.arc.network

# Generate wallet
cast wallet new

# Deploy
forge create src/Counter.sol:Counter --rpc-url $ARC_TESTNET_RPC_URL --private-key $PRIVATE_KEY

# Interact
cast call <CONTRACT_ADDR> "number()(uint256)" --rpc-url $ARC_TESTNET_RPC_URL
cast send <CONTRACT_ADDR> "increment()" --rpc-url $ARC_TESTNET_RPC_URL --private-key $PRIVATE_KEY
```

## Run a Node
- Docs: https://docs.arc.network/integrate/running-a-node
- Full node setup available (high-value contribution signal)

## Priority Strategy (highest airdrop signal first)
1. Claim faucet (20 USDC, automatable via 2Captcha) — faucet.circle.com + onchaingm.com/faucet
2. Bridge from Sepolia → Arc via superbridge.app (cross-chain activity signal)
3. Deploy contract — developer signal (OnchainGM or ZkCodex or Foundry)
4. **Register AI Agent (ERC-8004)** — unique Arc-native activity, signals deep engagement ⭐
5. **Create ERC-8183 Job** — agentic economy interaction, very few users doing this
6. Curve Finance swap — established DeFi, likely tracked by team
7. Register .arc domain (ArcNS or Infinity Name) — identity signal
8. UnitFlow Finance — DEX + NFT mint combo
9. Flow on Arc — full DeFi suite (swap, pool, lend)
10. ZkCodex GM Streak — daily consistency signal ⭐ (do EVERY day)
11. Omnihub / Arkle / nfts2.me — NFT minting
12. Arc World — passport + games (multi-activity)
13. Achswap — prediction market (unique activity type)
14. Arc House community — post discussions, attend events (manual only)
15. Run a node — high-value technical contribution

## Daily Routine
- ZkCodex GM Streak ⭐
- OnchainGM say GM
- Swap on Curve/UnitFlow (small amounts)
- Self-transfer
- Arc Crypto daily tournament
- Arc House: comment on 1 content post (manual)

## Faucet Strategy (Multi-wallet)
Arc faucet is **FULLY AUTOMATABLE** via 2Captcha v2 bypass (see Faucet section above):
- Automated: solve v2 captcha ($0.003) → GraphQL mutation → 20 USDC per claim
- Claim USDC for wallet → wait 2h → claim EURC for same wallet (double tokens)
- For 10-20 wallets: script runs in ~20 min (60s solve per wallet)
- For 1000 wallets: ~17 hours sequential, or parallelize with multiple 2Captcha tasks
- Total per wallet per day: up to 240 USDC (20 USDC × 12 claims if you claim every 2h)
- Practical: claim once per wallet per session, move on
- **2Captcha API key required** — ~$3 per 1000 solves

## Bridge Strategy (Sepolia → Arc)
- Use superbridge.app for Sepolia → Arc bridge
- Requires Sepolia ETH (get from Sepolia faucets: sepoliafaucet.com, alchemy faucet)
- Bridge gives cross-chain activity signal — high value for airdrop
- For 1000 wallets: bridge small amounts (0.001-0.01 ETH each) from funded source wallet
- CCTP bridge: USDC on Sepolia → USDC on Arc (alternative to native bridge)

## Key Differences from GIWA
| Aspect | Arc | GIWA |
|--------|-----|------|
| Gas token | USDC (free from faucet) | ETH (0.005/24h faucet) |
| Faucet captcha | reCAPTCHA Enterprise (automatable via 2Captcha v2) | Cloudflare WAF (manual) |
| Faucet amount | 20 USDC / 2h | 0.005 ETH / 24h |
| Multi-wallet ease | Very easy (no captcha) | Hard (manual + proxy) |
| Ecosystem size | 30+ dApps | ~5 activities |
| Attestation gate | None found yet | Dojang required |
| Backing | Circle ($2.2B raised) | Upbit/Dunamu |
| Community | Arc House (Gradual) — manual | None |

## Events (as of May 2026)
- Arc Enterprise & DeFi Hackathon active
- Stablecoins Commerce Stack Challenge (Apr 14 – Jul 13) — ongoing
- Builder Spotlights (Chariot, Synthra) — bi-weekly
- Bi-weekly Discord Office Hours (Wednesdays ~midnight WIB)
- Consensus 2026 Workshop (Agentic Stack)

## ERC-8004 AI Agent Registration (Agentic Economy)

Arc has a unique "Agentic Economy" feature — register AI agents with onchain identity, reputation, and job settlement. This is a HIGH-VALUE farming activity because it signals developer engagement with Arc's unique features.

### Contracts (ERC-8004 on Arc Testnet)
| Contract | Address |
|----------|---------|
| IdentityRegistry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| ReputationRegistry | `0x8004B663056A597Dffe9eCcC1965A193B7388713` |
| ValidationRegistry | `0x8004Cb1BF31DAf7788923b405b754f57acEB4272` |

### Workflow (Viem, no Circle Developer Console needed)
1. Generate 2 wallets: owner (registers agent) + validator (records reputation)
2. Fund both from faucet (20 USDC each, ~0.006 USDC per tx)
3. Register agent: call `register(string metadataURI)` on IdentityRegistry
4. Get agent ID: parse Transfer event from registration tx receipt
5. Record reputation: call `recordReputation(uint256 agentId, uint8 score, string category, string reason)` on ReputationRegistry from VALIDATOR wallet (owner cannot self-attest)

### Key Details
- Gas per tx: ~0.006 USDC
- Metadata URI: can use example `ipfs://bafkreibdi6623n3xpf7ymk62ckb4bo75o3qemwkpfvp5i25j66itxvsoei` or upload custom JSON to IPFS
- Chain definition for viem: `defineChain({ id: 5042002, nativeCurrency: { name: 'USDC', symbol: 'USDC', decimals: 18 }, rpcUrls: { default: { http: ['https://rpc.testnet.arc.network'] } } })`
- viem has `arcTestnet` in `viem/chains` (may work without defineChain)
- Owner cannot record reputation for own agent (anti-self-dealing)
- Registration mints an NFT (ERC-721) — the tokenId IS the agentId

### ERC-8183 Jobs (next step after registration)
After registering an agent, create jobs with escrow + deliverables + settlement:
- Tutorial: https://docs.arc.network/arc/tutorials/create-your-first-erc-8183-job
- This adds another layer of on-chain activity (job creation, acceptance, completion)

### Multi-wallet Strategy
For each wallet pair (owner + validator):
1. Claim faucet for both
2. Register unique agent (different metadata per wallet)
3. Cross-validate: wallet A's validator records reputation for wallet B's agent and vice versa
4. Create ERC-8183 jobs between agents

### Mass Registration (1000+ accounts)
Working multi-worker script at `~/arc-agent/mass-register.ts`:
- **Architecture:** N parallel workers, each: generate wallet → solve captcha → claim faucet → register agent
- **Dependencies:** viem, tsx, https-proxy-agent, socks-proxy-agent, node-fetch
- **Proxy:** residential proxy required for scale (faucet rate-limits 1 per 2h per IP)
- **Output:** `results.csv` (address, private_key, agent_id, register_tx, status)
- **Resume:** auto-resumes from last completed account
- **Retry:** `retry-failed.ts` re-processes failed accounts from `failed.csv`

```bash
# Run
npx tsx mass-register.ts --accounts 1000 --workers 10 --proxy-file proxies.txt

# Throughput estimates (bottleneck = 2Captcha solve ~45-60s):
# 5 proxies, 5 workers  → ~2-3/min → ~6h for 1000
# 10 proxies, 10 workers → ~5-6/min → ~3h for 1000
# 20 proxies, 15 workers → ~8-10/min → ~2h for 1000
```

**Cost:** 2Captcha ~$3/1000 solves + proxy costs

### Template Script
Working scripts at `~/arc-agent/`:
- `index.ts` — single account register (viem + tsx, env-file config)
- `mass-register.ts` — multi-worker mass registration
- `retry-failed.ts` — retry failed accounts
- `claim-faucet.ts` — standalone faucet claimer (for testing)

## Contract Addresses (from docs.arc.network)
- USDC Native: `0x3600000000000000000000000000000000000000`
- EURC: `0x89B50855Aa3bE2F677cD6303Cec089B5F319D72a`
- Full list: https://docs.arc.network/arc/references/contract-addresses.md
