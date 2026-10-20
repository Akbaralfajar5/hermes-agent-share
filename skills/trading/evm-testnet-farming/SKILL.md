---
name: evm-testnet-farming
cluster: blockchain
description: "Crypto farming automation — EVM testnet interactions (deploy, swap, bridge) for airdrop eligibility AND NFT whitelist/allowlist applications (social tasks, form submission, bulk wallets). Multi-wallet scripts, daily routines, and tracking."
tags: ["testnet", "airdrop", "evm", "l2", "farming", "multi-wallet", "ethereum", "nft", "whitelist", "allowlist"]
dependencies: ["ethers-js"]
composes: []
similar_to: ["ethereum-wingman"]
called_by: []
authorization_required: false
scope: general
model_hint: claude-sonnet
embedding_hint: "testnet farming airdrop multi-wallet EVM L2 faucet deploy contract interact daily routine NFT whitelist allowlist WL garap"
---

# EVM Testnet Farming

## Purpose
Automate multi-wallet testnet interactions on EVM-compatible chains (L2s, sidechains) to build on-chain history for potential airdrop eligibility. Covers wallet generation, faucet claiming, contract deployment, token interactions, and daily activity routines.

## When to Use
- User asks to "farm" or "garap" a testnet
- User wants multi-wallet scripts for any EVM testnet
- User mentions airdrop preparation on a new L2/chain
- User wants automated daily on-chain activity
- User shares a tweet/thread listing testnet protocols to interact with
- Keywords: testnet, farming, airdrop, multi-wallet, garap, L2, footprint

## Architecture Pattern

```
~/project-testnet/
├── config.js           # RPC, chain ID, contracts, timing
├── wallets.json        # Generated wallets (KEEP PRIVATE)
├── generate-wallets.js # Create N wallets
├── fund-wallets.js     # Distribute ETH from wallet #1
├── interact.js         # Full interaction suite
├── daily.js            # 24h routine (cron-able)
├── playground.js       # Protocol-specific contract calls
├── claim-faucet.js     # Faucet automation (if API available)
├── status.js           # Check all balances/nonces
├── run-all.js          # Master CLI runner
└── results.json        # TX logs
```

## Step-by-Step Workflow

**CRITICAL: Test-First Pattern** — When setting up multi-wallet farms, ALWAYS test delegation + mint on wallet #1 FIRST before distributing ETH to all wallets. If delegation/minting doesn't work, you've only wasted gas on 1 wallet instead of 50. See `references/eip7702-delegation-rpc-pitfalls.md` for details.

### 1. Research the Chain
Before scripting, gather:
- RPC URL and Chain ID
- Block explorer URL
- Faucet URLs and their APIs (inspect JS bundles for endpoints)
- Key contract addresses (tokens, DEX, bridges, name services)
- Playground/quest activities available
- Whether faucet needs auth/captcha

### 2. Setup Project
```bash
mkdir ~/chainname-testnet && cd ~/chainname-testnet
npm init -y
npm install ethers@6 axios
```

### 3. Generate Wallets
```javascript
const { ethers } = require('ethers');
const wallet = ethers.Wallet.createRandom();
// Save: address, privateKey, mnemonic
```
Generate 5-20 wallets. Store in `wallets.json`.

### 4. Fund Wallets
- Claim faucet for wallet #1 (often manual due to captcha)
- **TEST delegation + mint on wallet #1 FIRST** before distributing to other wallets
  - This prevents wasting gas on 50+ wallets if the flow is broken
  - User frustration signal: "proses dulu mint di wallet pertama, jangan send dulu ke yg lain"
  - Verify: delegation confirms, MCP responds, mint succeeds
- Only after successful test: distribute from wallet #1 to others via script
- Amount per wallet: enough for ~50-100 transactions

### 5. Interaction Activities (ordered by value)
### 5. Interaction Activities (ordered by value)
1. **Self-transfer** — simplest activity proof
2. **Wrap/Unwrap ETH ↔ WETH** — DeFi interaction signal
3. **Deploy contract** — developer activity signal
4. **Contract interaction** — store/read values
5. **On-chain attestation/identity** — Dojang, EAS, soulbound tokens (often prerequisite for other actions)
6. **Token claims** — protocol-specific faucets (may require attestation first)
7. **Inter-wallet transfers** — network usage
8. **Name service registration** — identity signal (may require attestation)
9. **Bridge usage** — cross-chain activity (high value)
10. **NFT minting** — if available
11. **DEX swaps** — if testnet DEX exists
12. **EIP-7702 delegation** — delegate EOA to smart contract (new pattern, requires Foundry `cast --auth`)

### 5b. Dependency Chains (CRITICAL)
Many testnet ecosystems have **gated activities** where step N requires step N-1:
```
Attestation/Identity → Token Claim → Name Registration
```
Always reverse-engineer the dependency chain from the frontend JS BEFORE scripting. Look for constructor params like `dojangScroll_`, `attesterId_` that indicate gating. Use `estimateGas` to check eligibility before sending transactions — if it reverts, the prerequisite isn't met.

### Shell Wrappers for .env Loading
`npm run` doesn't inherit shell environment variables. Create wrapper scripts:
```bash
# check.sh, dist.sh, go.sh pattern
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi
npm run farm
```
See `templates/npm-wrapper.sh` for a reusable template.

### 6. Daily Routine (Cron)
Run every 24h to maintain consistent activity:
- Claim any daily tokens
- Self-transfer
- Wrap/unwrap small amounts
- Random inter-wallet transfers
- Token transfers between wallets

## Key Patterns

### Faucet Automation Notes
**Circle faucet (faucet.circle.com) — FULLY AUTOMATABLE via 2Captcha v2 fallback:**
The faucet uses reCAPTCHA Enterprise v3 with v2 fallback. The v3 token from 2Captcha gets rejected server-side ("ReCAPTCHA verification failed"), but the **v2 fallback works perfectly**.

**Working bypass (verified May 2026):**
1. GraphQL endpoint: `POST https://faucet.circle.com/api/graphql`
2. Mutation: `RequestToken` with input `{ destinationAddress, blockchain, token }`
3. Blockchain enum values: `"ARC"`, `"ETH_SEPOLIA"`, `"AVAX_FUJI"`, `"SOL_DEVNET"`, etc. (NOT "ARC-TESTNET")
4. Response fields: `amount blockchain contractAddress currency destinationAddress explorerLink hash status`
5. reCAPTCHA v2 sitekey: `6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve` (Enterprise)
6. Token sent via header: `recaptcha-v2-token: <token>`

```bash
# 1. Solve v2 captcha via 2Captcha API
curl -s -X POST 'https://api.2captcha.com/createTask' \
  -H 'Content-Type: application/json' \
  -d '{"clientKey":"YOUR_2CAPTCHA_KEY","task":{"type":"RecaptchaV2TaskProxyless","websiteURL":"https://faucet.circle.com","websiteKey":"6LcCqC8sAAAAAHGuWXnlpxcEYJD3lE_EFLebNnve","isEnterprise":true}}'
# Poll getTaskResult until ready (~45-60s)

# 2. Submit claim with solved token
curl -s -X POST 'https://faucet.circle.com/api/graphql' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://faucet.circle.com' \
  -H "recaptcha-v2-token: $TOKEN" \
  -d '{"operationName":"RequestToken","variables":{"input":{"destinationAddress":"0xYOUR_ADDRESS","blockchain":"ARC","token":"USDC"}},"query":"mutation RequestToken($input: RequestTokenInput!) { requestToken(input: $input) { amount hash status explorerLink } }"}'
```

**Key discoveries:**
- v3 Enterprise tokens from 2Captcha are REJECTED (server-side assessment too strict)
- v2 Enterprise tokens WORK via `recaptcha-v2-token` header (found by reverse-engineering JS bundles)
- The faucet page source has `recaptchaV2FallbackEnabled: true` — this is the signal
- Cooldown: 1 request per stablecoin+network pair every 2 hours
- Strategy: claim both USDC and EURC = 2x tokens per cooldown period
- Cost: ~$0.003 per solve (2Captcha v2 rate)
- **CRITICAL: Rate limit is per wallet+blockchain pair, NOT per IP.** Each new wallet = fresh claim. No proxy needed for mass farming. Tested 1000+ claims from single VPS IP.
- DataImpulse residential proxy (gw.dataimpulse.com) returns `403 SITE_PERMANENTLY_BLOCKED` for faucet.circle.com. Other residential providers may also block it. Since rate limit is per-wallet, proxy is unnecessary anyway.
- node-fetch + HttpsProxyAgent gives empty/broken responses for this endpoint. If proxy IS needed for other faucets, use curl subprocess or undici ProxyAgent.

**How the header was discovered:** In the faucet's webpack chunk (`97528-*.js`), the Apollo mutation context shows:
```javascript
context:{headers:{"recaptcha-v2-token":u.token,[i.dU]:a}}
```
The v2 token is sent when v3 fails (score too low). By sending v2 directly, we skip the v3 attempt entirely.

**Reverse-engineering methodology (reusable for any Next.js + Apollo + reCAPTCHA site):**
1. Find sitekey: `document.querySelectorAll('script[src*="recaptcha"]')` → extract `render=SITEKEY` from URL
2. Find GraphQL endpoint: try `POST /api/graphql` with `{"query":"{ __typename }"}` — if returns `{"data":{"__typename":"Query"}}`, it works
3. Find mutation name: send wrong mutation → error reveals correct name ("Did you mean X?")
4. Find input fields: send wrong field names → error reveals correct ones ("Field X is not defined")
5. Find response fields: query `__typename` first (bypasses field validation), then use error messages
6. Find captcha header: search webpack chunks for `context:{headers:` near the mutation call
7. Test v2 fallback: if page source has `recaptchaV2FallbackEnabled: true` AND a v2 sitekey, solve v2 and send via discovered header name

Always check if a faucet has captcha BEFORE building complex bypass solutions. Inspect feature flags in page source for `recaptchaEnabled`, `turnstileEnabled`, `recaptchaV2FallbackEnabled`, etc.

### Faucet API Discovery
Most faucets are Next.js apps. To find the API:
```bash
# Get page source, find JS bundles
curl -s 'https://faucet.example.io/' | grep -oP 'src="[^"]*\.js[^"]*"'

# Search bundles for API endpoints
curl -s 'https://faucet.example.io/_next/static/chunks/app/page-xxx.js' | grep -oP '.{0,100}(faucet|claim|charge).{0,100}'

# Find base URL in common chunks
curl -s 'https://faucet.example.io/_next/static/chunks/NNN-xxx.js' | grep -oP 'baseURL[^}]+'
```

### Frontend JS Reverse Engineering (Contract & API Discovery)
When a playground/dApp doesn't expose contract addresses or API URLs in docs, extract them from the frontend JS bundles:
```bash
# Find the app-specific chunk (usually has page name or largest)
curl -s 'https://playground.example.io/' | grep -oP 'src="(/_next/static/chunks/[^"]+)"'

# For Vite/React SPAs (non-Next.js): look for assets/*.js
curl -s 'https://app.example.com/' | grep -oP 'src="(/assets/[^"]+\.js)"'

# Discover API base URL (critical for SPAs with separate backend)
curl -s 'https://app.example.com/assets/index-HASH.js' | grep -oP 'https://[^"'\''`,\s]+' | sort -u
# Common patterns: api.example.com, example.com/api, backend.example.com

# Discover API route paths
curl -s 'https://app.example.com/assets/index-HASH.js' | grep -oP '"/[a-z][^"]*"' | sort -u
# Reveals: /auth/request, /mine, /challenge, /mint, /me, /ledger etc.

# Search for contract addresses, ABIs, and function names
curl -s 'https://playground.example.io/_next/static/chunks/CHUNK.js' | \
  grep -oP '.{0,300}(contractName|0x[0-9a-fA-F]{40}|functionName|ABI).{0,200}'

# Key patterns to look for:
# - "chainsToContracts" — maps chain IDs to contract addresses
# - "ABI" suffix variables — full ABI arrays
# - "payable" functions — indicate fee-based operations
# - Constructor params with "dojang", "attester", "scroll" — dependency signals
```
This technique revealed GIWA's `GIWAFaucetExtension.payAndIssueEAS()` (payable, 0.001 ETH fee) which was not documented anywhere.

### Attestation-Gated Ecosystems (EAS Pattern)
Many OP Stack L2s use Ethereum Attestation Service (EAS) to gate activities:
```javascript
// 1. Check if already attested
const isVerified = await dojangScroll.isVerified(wallet.address, attesterId);

// 2. If not, pay fee and get attestation
if (!isVerified) {
    const fee = await faucetExtension.fee(); // typically 0.001 ETH
    const tx = await faucetExtension.payAndIssueEAS({ value: fee });
    await tx.wait();
}

// 3. Now gated functions work
await tokenFaucet.claim(); // would revert without attestation
```
Key signals in frontend code: `attesterId`, `dojangScroll`, `isVerified`, `SchemaBook`, `EAS` at 0x4200...0021.

### Common Contract ABIs
```javascript
// WETH (universal on all EVM chains)
const WETH_ABI = [
    'function deposit() payable',
    'function withdraw(uint256 amount)',
    'function balanceOf(address) view returns (uint256)',
];

// ERC-20 Token
const ERC20_ABI = [
    'function balanceOf(address) view returns (uint256)',
    'function transfer(address to, uint256 amount) returns (bool)',
    'function name() view returns (string)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)',
];

// Simple deployable contract (Storage)
const STORAGE_BYTECODE = '0x608060405234801561001057600080fd5b5060c78061001f6000396000f3fe6080604052348015600f57600080fd5b506004361060325760003560e01c806360fe47b11460375780636d4ce63c146049575b600080fd5b60476042366004606b565b600055565b005b60005460405190815260200160405180910390f35b600060208284031215607c57600080fd5b503591905056fea264697066735822122000000000000000000000000000000000000000000000000000000000000000000064736f6c63430008130033';
const STORAGE_ABI = ['function set(uint256 x)', 'function get() view returns (uint256)'];
```

### Proxy Contract Detection
Many testnet contracts are proxies. Check implementation:
```javascript
// EIP-1967 implementation slot
const implSlot = '0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc';
const impl = await provider.getStorage(contractAddress, implSlot);
```

### Multicall3 Batch Balance Check (1000+ wallets)
```javascript
async function batchGetBalances(provider, wallets) {
    const multicall = new ethers.Contract('0xcA11bde05977b3631167028862bE2a173976CA11', [
        'function aggregate3(tuple(address target, bool allowFailure, bytes callData)[] calls) view returns (tuple(bool success, bytes returnData)[])',
        'function getEthBalance(address addr) view returns (uint256 balance)',
    ], provider);
    
    const BATCH_SIZE = 100;
    const balances = new Map();
    
    for (let i = 0; i < wallets.length; i += BATCH_SIZE) {
        const batch = wallets.slice(i, i + BATCH_SIZE);
        const calls = batch.map(w => ({
            target: '0xcA11bde05977b3631167028862bE2a173976CA11',
            allowFailure: true,
            callData: multicall.interface.encodeFunctionData('getEthBalance', [w.address]),
        }));
        const results = await multicall.aggregate3(calls);
        for (let j = 0; j < results.length; j++) {
            if (results[j].success) {
                const bal = ethers.AbiCoder.defaultAbiCoder().decode(['uint256'], results[j].returnData)[0];
                balances.set(batch[j].address, bal);
            } else {
                balances.set(batch[j].address, 0n);
            }
        }
        await sleep(500); // small delay between batches
    }
    return balances;
}

// Usage in daily(): filter funded wallets, skip empty ones
const balances = await batchGetBalances(provider, wallets);
const funded = wallets.filter(w => (balances.get(w.address) || 0n) > 0n);
// Only process `funded` array — skip 991 empty wallets instantly
```

### Foundry (cast) for EIP-7702 and Contract Inspection
```bash
# Install foundry (one-time) — already installed on VPS at ~/.foundry/bin/
curl -L https://foundry.paradigm.xyz | bash
export PATH="$HOME/.foundry/bin:$PATH"
foundryup
# NOTE: After install, must export PATH in every new shell/terminal command

# Key commands:
cast code $ADDRESS --rpc-url $RPC          # Check delegation/bytecode
cast balance $ADDRESS --rpc-url $RPC       # ETH balance (wei)
cast call $CONTRACT "functionName()" --rpc-url $RPC  # Read contract
cast send $TO --private-key $PK --rpc-url $RPC --auth $DELEGATE --gas-limit 100000  # EIP-7702
cast disassemble "$BYTECODE"               # Reverse-engineer contract
cast 4byte $SELECTOR                       # Lookup function selector
```

### Blockscout API for Base (Basescan v1 deprecated)
Basescan's v1 API (`api.basescan.org`) returns "deprecated V1 endpoint" errors. Use **Blockscout** instead:
```python
import requests
headers = {'Accept': 'application/json'}

# Get transactions for an address
url = f"https://base.blockscout.com/api/v2/addresses/{address}/transactions"
resp = requests.get(url, headers=headers, timeout=15).json()

# Get full tx details (including decoded_input!)
url = f"https://base.blockscout.com/api/v2/transactions/{tx_hash}"
resp = requests.get(url, headers=headers, timeout=15).json()
# resp['decoded_input'] gives method name, params with types and values

# Get token transfers in a tx
url = f"https://base.blockscout.com/api/v2/transactions/{tx_hash}/token-transfers"

# Get internal txs
url = f"https://base.blockscout.com/api/v2/addresses/{address}/internal-transactions"
```
Blockscout's `decoded_input` is extremely useful for reverse-engineering unknown contracts — it shows the full function signature and parameter values without needing the ABI.

### RPC Strategy for Unreliable Mining Backends
When mining via MCP servers or relayer endpoints that frequently timeout/500:
- **Test-and-hold beats time-based rotation** — Don't auto-rotate RPCs every N minutes
- User preference: manual RPC switching based on observed results
- Pattern: try RPC A → if mint succeeds within 10 min → keep using it
- Only switch when user sees prolonged failure (no mints for 30+ min)
- Aggressive retry (2s delay) on same RPC is better than premature switching
- Example: brainrot.dog $ROT mining — RPC publik worked after Ankr premium failed

**Why:** RPC quality varies by time/load, not just provider. A working RPC should be exploited until it stops working. Rotation introduces unnecessary variables when debugging MCP/relayer issues (which are often the real bottleneck, not RPC).

### Timing & Anti-Detection
```javascript
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
// Between transactions: 3-6 seconds
// Between wallets: 8-15 seconds (higher for 100+ wallets to avoid rate limits)
// Randomize: min + Math.random() * (max - min)
```

## Pitfalls

1. **Cloudflare Managed Challenge ≠ Turnstile Widget** — Critical distinction: Cloudflare WAF "managed challenges" (the "Just a moment..." page) protect the ENTIRE domain and cannot be solved by 2Captcha/anti-captcha services. These are NOT the same as standalone Turnstile widgets embedded in a page. 2Captcha's `TurnstileTaskProxyless` only works for standalone Turnstile widgets (with a visible sitekey in `data-sitekey`). For CF managed challenges, tasks get accepted but return `ERROR_CAPTCHA_UNSOLVABLE` after 3 minutes. Don't waste API credits trying multiple sitekeys — if the page shows "Just a moment..." with `cType: 'managed'` in the source, it's unsolvable via API.
2. **CloakBrowser + Turnstile** — CloakBrowser (pip install cloakbrowser) bypasses basic Cloudflare JS challenges but NOT Turnstile interactive checkboxes. With `headless=True` the Turnstile iframe doesn't load at all (0 frames). With `xvfb-run` + `headless=False` + `humanize=True`, the iframe appears but the checkbox click doesn't register (stays unchecked). Don't waste time trying multiple approaches — tell user to claim manually.
3. **2Captcha for Cloudflare** — 2Captcha API key: use `TurnstileTaskProxyless` type with `websiteURL` and `websiteKey`. Only works for STANDALONE Turnstile widgets (sitekey visible in page HTML as `data-sitekey`). For CF managed challenges, common sitekeys like `0x4AAAAAAACYaURIJcupMxTM` get accepted but never solve. The old API (`2captcha.com/in.php?method=turnstile`) also fails. Save the user's money — verify it's a standalone widget first.
4. **Nodit/third-party faucets need accounts** — API endpoint pattern: `POST /be/v2.0/faucet/charge` with `{address, protocol, network}` but requires auth token cookie. Signup also has reCAPTCHA.
5. **Rate limits on RPC** — Public testnet RPCs are rate-limited. Add delays between calls. Use `--connect-timeout 5 --max-time 10` for curl.
6. **EIP-7702 delegated EOAs cannot send normal transfers** — Once an EOA is delegated via EIP-7702, it cannot send normal ETH transfers until delegation is revoked (sign authorization to `0x0000000000000000000000000000000000000000`). Symptom: "gas required exceeds allowance (10500)" even with sufficient balance. See `references/eip7702-delegation-rpc-pitfalls.md` for revocation pattern.
6. **Contract call failures on proxies** — Proxy contracts may have different ABIs than expected. Always check code length and proxy implementation slot first. "missing revert data" usually means wrong ABI or the function doesn't exist on that contract.
7. **Gas estimation** — Testnet gas is cheap but not free. Keep ~0.001 ETH minimum per wallet for operations. For chains with attestation fees (like GIWA's 0.001 ETH Dojang), budget accordingly.
8. **24h cooldowns** — Token faucets typically have 24h cooldown. Track `lastClaimed` timestamp.
9. **Wallet security** — `wallets.json` contains private keys. Never commit to git. Add to `.gitignore`.
10. **Gated activities** — Many testnets require identity/attestation BEFORE token claims or name registration. Always check if `claim()` reverts with "not verified" — it means you need to issue attestation first.
11. **Funding math** — With 0.005 ETH faucet drip and 0.001 ETH Dojang fee + gas, you can realistically fund ~2-3 wallets per faucet claim. Plan multi-day accumulation for 10+ wallet farms.
12. **Simple Storage contract interaction** — The bytecode deploys fine but `set()` may fail with "missing revert data" if the bytecode metadata hash is zeroed out. Use a verified bytecode or skip the interaction step if it fails.
13. **Scaling to 1000+ wallets** — For large farms, generate all wallets upfront and export addresses to a text file for batch faucet claiming. User claims manually with proxy rotation (1 claim per IP per 24h). Script processes wallets sequentially with random delays. **Critical: use Multicall3 for balance checks** (see below) — querying 1000 wallets individually WILL hit rate limits on public RPCs.
14. **RPC rate limits on batch operations** — Public testnet RPCs (like GIWA's) return `-32016 over rate limit` when you make 100+ sequential calls. Solution: use **Multicall3** (`0xcA11bde05977b3631167028862bE2a173976CA11`, deployed on virtually all EVM chains) to batch `getEthBalance()` calls — 100 per multicall = 10 RPC calls for 1000 wallets instead of 1000. Also increase inter-wallet delays to 8-15 seconds for transaction operations. Filter funded wallets FIRST, then only process those.
14. **Windows EPERM on npm install** — `EPERM: operation not permitted, rmdir 'node_modules/...'` happens when antivirus or another process locks `node_modules`. Fix: close VS Code/editors, disable real-time AV scan on project folder, or delete `node_modules` manually before reinstall.
14b. **"Cannot find module" after extracting scripts** — When user extracts a tar.gz/zip of scripts and immediately runs `npx tsx script.ts`, they get `ERR_MODULE_NOT_FOUND` for viem/ethers/etc. Root cause: `node_modules/` is excluded from archives (correctly). Fix: user must run `npm install` first. Always include this in instructions. On Windows with `npx tsx`, tsx gets installed globally from npx cache but project deps are still missing locally.
15. **npm registry mismatch** — If recipient gets `ENOTFOUND mirrors.tencentyun.com`, their npm is configured for a China mirror. Fix: `npm config set registry https://registry.npmjs.org/`. Don't ship `package-lock.json` to avoid baking in mirror URLs.
16. **Discord/community access confusion** — Users often hear "you need to build to join Discord" but this usually refers to ambassador/contributor programs (e.g., Arc's "Architects"), NOT the Discord server itself. Always verify: most project Discords are open. Check for: (a) public invite link on website footer/community page, (b) ambassador programs that require contributions for elevated roles/badges. Clarify the distinction to the user.
16b. **Gradual-powered community hubs cannot be automated** — Some projects (e.g., Arc House at community.arc.network) use Gradual (gradual.app) as their community platform. These require genuine human interaction: posting discussions, commenting on content, attending events. Points/reputation are earned through real engagement. No API, no script bypass. Always tell user to handle these manually with their main account. Bot scripts are for on-chain activity only.
17. **Discord onboarding quizzes (anti-speculator filters)** — Many crypto Discords now have multi-question onboarding forms that filter out speculators/airdrop farmers. The correct answers always align with "builder" persona:
    - Role question → pick "Builder / engineer" or "Contributor (docs, QA, testing)"
    - Value contribution → pick "Sharing repos, demos, or deployment examples" or "Answering technical questions"
    - Trust/roles → pick "Respect the rules, help others, provide feedback without expecting perks"
    - **NEVER pick** options mentioning: speculation, rewards, lurking, pinging staff, demanding roles, promoting referral links. These are deliberate traps that result in application rejection.
    - Intro text: write 2-3 sentences about building/testing on the chain, mention specific tech (Foundry, smart contracts, DeFi analytics). Include interest in the chain's unique features (e.g., "stablecoin-native gas" for Arc).
18. **CloakBrowser + X OAuth for WL sites** — To authenticate with WL sites that use X OAuth2:
    - Set cookies on BOTH `.x.com` AND `.twitter.com` domains (OAuth uses twitter.com URLs)
    - Use `context.add_cookies()` BEFORE navigating to the OAuth URL
    - X authorize button text is locale-dependent: "Izinkan aplikasi" (ID), "Authorize app" (EN), "Allow" — use `button:has-text("Izinkan"), button:has-text("Authorize"), button:has-text("Allow")`
    - After authorize click, wait 8-10s for redirect chain to complete
    - Session cookies (`twitter_user`, `twitter_session`) persist in the browser context for subsequent API calls
    - Use `page.evaluate(fetch(..., {credentials: "include"}))` to hit authenticated API endpoints
19. **X auth tokens from spreadsheets expire** — Bulk-purchased X accounts have auth_tokens that expire within days/weeks. Always test tokens before building automation: `curl -s -D - "https://x.com/home" -H "Cookie: auth_token=TOKEN" -o /dev/null | grep ct0`. If response clears ct0 with `Max-Age=-`, token is dead. For reliable X automation, use the user's main account (env vars `TWITTER_AUTH_TOKEN` + `TWITTER_CT0`) or login fresh via CloakBrowser with username/password.
20. **xurl vs twitter CLI** — `xurl` (Go binary) requires X Developer API keys + OAuth2 setup (`xurl auth apps add` + `xurl auth oauth2`). If not configured, it shows "No apps registered." The `twitter` CLI (Python, `pip install twitter-cli`) works with browser cookies (`TWITTER_AUTH_TOKEN` + `TWITTER_CT0` env vars) and is already configured on this VPS. For quick X searches/lookups without developer API setup, always prefer `twitter` CLI. Commands: `twitter search "query" --json`, `twitter user "handle" --json`.
21. **X login via CloakBrowser** — X login form requires specific interaction pattern:
    - `page.keyboard.type()` works for input (React-compatible)
    - Button clicks via `page.click()` often fail silently — use `page.evaluate('el.click()')` or Tab+Enter
    - React input: set value via native setter + dispatch `input` event for state sync
    - Login flow: username → Next → (may get "Find your X account" verification) → email → (may get "Confirm username") → password → Enter
    - Accounts may trigger "confirmation code" flow (password reset) — need email access to complete
22. **Mainnet bonding curve buy — "insufficient funds" precision** — When buying via bonding curve routers (Uniswap V4 hooks), the tx value + gas must be EXACTLY within balance. On low-gas chains (Base: 0.006 gwei), gas cost is negligible but still matters. Formula: `buy_amount = balance - (gas_limit * gas_price * 3)`. Common failure: gas estimate succeeds (uses `eth_call` which doesn't check balance) but `send_raw_transaction` fails because value + gas exceeds balance by a few wei. Always leave a buffer. Also: use `w3.eth.get_transaction_count(addr, 'latest')` — rejected txs can inflate pending nonce on some nodes.
23. **EIP-7702 delegation gotchas** — When delegating via `cast send --auth`:
    - The type-4 tx may show `status: 0 (failed)` but the delegation IS applied. Always verify with `cast code`.
    - Check the project's `/api/config` or docs for the correct delegation target — the ERC20 token address and the MintDelegate address are different contracts. Delegating to the wrong one wastes gas and requires re-delegation.
    - `cast send $WALLET --auth $DELEGATE --value 0 --gas-limit 100000` — gas estimation often fails for self-txs, always set explicit `--gas-limit`.
    - Delegation code format: `0xef0100` + 20-byte address (lowercase). Check with `cast code $WALLET`.
23. **API geo-blocking / VPS IP blocking** — Some project APIs (e.g., rpow2's `api.rpow2.com`) are intermittently or permanently unreachable from VPS IPs (curl returns code 000, timeout) while the frontend SPA loads fine (served from CDN). This creates a deadlock: can't login, can't mine. Diagnosis: if `curl --max-time 30` returns exit code 28 (timeout) but the same URL works from user's PC, it's IP-based blocking (Cloudflare, nginx geo-rules, or rate limiting by IP range). **Workaround:** User logs in from PC/phone, extracts cookie from DevTools (Application → Cookies or `document.cookie` in console), sends cookie to agent. Agent uses cookie for API calls — but if API is ALSO blocked for mining requests, VPS mining is impossible. In that case, mining must run on user's PC (official CLI/native miner).
24. **Temp mail service selection for automated registration** — When automating multi-account signups that need email verification, use **mail.tm** (REST API: `api.mail.tm/accounts`, `/token`, `/messages`) — NOT generator.email (inbox requires WebSocket/socket.io, unreadable via curl/requests). mail.tm flow: create account → get Bearer token → poll `/messages` → read full message HTML → extract verify link. Domains rotate (check `GET /domains` first). Other services with proper APIs: Guerrilla Mail, Mailinator (paid). Avoid: TempMail.org (captcha), generator.email (WebSocket-only inbox), 10MinuteMail (no API).
25. **Email auth services with pending Postmark/SendGrid accounts** — Some new projects use magic-link email auth but their transactional email provider (Postmark, SendGrid) is still pending approval. Symptom: button disables (looks successful) but email never arrives to ANY external domain. **This can be intermittent** — sometimes the API returns 500 with the explicit error, other times it appears to succeed (no error) but email still doesn't arrive. Diagnosis: hit their API directly with curl — look for 500 with "While your account is pending approval, all recipient addresses must share the same domain as the 'From' address." Also check if the domain has MX records (`dig domain.com MX`) — if no MX exists, the "same domain" restriction creates a deadlock (no mailbox can receive). Nothing you can do except wait (can take days, not just hours) or find alternative auth. Always check the API response before assuming email delivery issues. **Magic link tokens expire quickly (often <5 minutes)** — if user provides the link, verify it IMMEDIATELY via curl (faster than browser navigation which can CDP-timeout). Use `curl -s -c cookies.txt "VERIFY_URL"` to capture the auth cookie. Opening in a different session than intended returns "invalid or expired link". If browser navigation times out, always fall back to curl.
24. **MCP-gated minting cannot be bypassed from VPS** — Some mainnet projects (e.g., dogeshit.meme) enforce `tx.origin == RELAYER` on-chain, where the relayer is only triggered via Claude.ai's MCP server (IP-restricted to Anthropic's server IPs). Running Claude model via Hermes ≠ being Claude.ai platform. Don't try X-Forwarded-For or Origin header spoofing — CF strips/ignores these. **Solution:** User opens Claude.ai (Free tier works!), adds custom connector (Settings → Konektor → "Tambah konektor kustom" → paste MCP URL), completes OAuth/SIWE in browser with wallet, then says "mint me some shit". Agent's role: (1) delegate wallet via `cast --auth`, (2) verify delegation, (3) guide user through Claude.ai UI. **Two failure modes:** (a) Relayer at capacity (50/50 in-flight) during high traffic — retry with smaller batches ("mint me 1 slot"); (b) Relayer gas cap exceeded (observed: 4.21 gwei) — wait for low-gas periods (WIB 07:00-13:00 or weekends). Monitor: `cast base-fee --rpc-url https://ethereum-rpc.publicnode.com`.
33. **Superbridge Sepolia→ARC: use chain ID 11155111, NOT 1** — The tweet URL `superbridge.app/?fromChainId=1` is wrong (chain 1 = Ethereum mainnet). Sepolia testnet chain ID is 11155111. Correct URL: `https://superbridge.app/?fromChainId=11155111`. Using chain 1 would bridge real mainnet ETH, not testnet ETH. Always verify chain ID before bridging.

34. **OnchainGM is a separate faucet + activity hub** — onchaingm.com has its own faucet (`/faucet`), deploy+GM (`/deploy`), and badge mint (`/badge-arc`). These are SEPARATE from ZkCodex and should be treated as additional daily activities. The GM streak on OnchainGM may be tracked independently from ZkCodex's streak.

25. **$HASH multi-wallet per VPS is WORSE than single wallet** — Tested May 2026: splitting 4 GPUs into 2 wallets × 2 GPU each resulted in 30+ minutes with 0 mints. Root cause: halved hashrate per wallet means expected time doubles, and the 10 mints/block limit is already filled by competitors so parallelism doesn't help. Always use 1 wallet per VPS with ALL GPUs. For more parallelism, add more VPS instances with different wallets.

25b. **Browser WASM mining >> VPS Node.js/C mining** — For browser-mined PoW tokens (e.g., hash256.org $HASH), Chrome/Brave WASM achieves ~95 MH/s (8 workers) vs Node.js ~1.7 MH/s (64 workers) — a 56x gap. Native C keccak256 gets ~9-10 MH/s but still 10x slower than browser. If user has a fast PC, recommend browser mining over VPS. VPS only makes sense for additional wallets or when user's PC is unavailable. The WASM file is typically NOT publicly accessible (served only in browser context via bundler), so you cannot just download and run it on VPS.
26. **Always check for official CLI/SDK before reverse-engineering** — Many crypto projects (rpow2, testnets, etc.) have official CLI tools or portable miner packages that handle auth, retries, challenge expiry, and multi-threading properly. Before spending time reverse-engineering JS bundles and writing custom miners, search for: (a) GitHub repos linked from the project, (b) Discord/Telegram pinned messages with download links, (c) README files mentioning CLI tools. Official tools are almost always faster (native C/Rust vs Python) and handle edge cases (challenge expiry, rate limits) that custom scripts miss.
30b. **$HASH contract address: always verify from website source, not memory** — The mining contract is `0xAC7b5d06fa1e77D08aea40d46cB7C5923A87A0cc` (footer link on hash256.org). There is also a token contract `0x000000000004444c...` which is NOT for mining. Wrong contract symptoms: `era: 0`, `difficulty: 0x3fff...fff` (max uint256), `missing revert data` on all calls, `eth_getCode` returns `0x`. Always verify bytecode exists before mining. See `references/hash256-mining.md` for extraction method.

30c. **$HASH CUDA keccak256 endianness bug** — The keccak256 output in CUDA is naturally little-endian per 64-bit word. The comparison loop must use big-endian byte order (j=0 first = MSB). The bug is NOT in the output encoding — it's in `bool valid = true` initialization. With `valid = true`, any hash where the loop exits without breaking (all bytes equal) incorrectly passes. Always initialize `valid = false`. Verify with empty string test: `keccak256("") == 0xc5d2460186f7233c...`. See `references/hash256-mining.md` for full diagnosis path.

30. **CUDA hash comparison: initialize `valid = false` not `valid = true`** — A subtle CUDA bug: if `bool valid = true` at the start of the big-endian comparison loop, then any hash where the first differing byte is LESS than difficulty passes (correct), but also any hash where ALL bytes equal difficulty passes (wrong — should be strict less-than). More critically, if the loop exits without breaking (all bytes equal), `valid` stays `true` incorrectly. Always initialize `valid = false`. Symptom: miner finds nonces quickly, gas estimate succeeds, but TX reverts with `0x4992976a` on-chain. Fix: `bool valid = false;` then `if (hash[j] < difficulty[j]) { valid = true; break; }`.

31. **ethers.js JsonRpcProvider 500 error on some RPCs** — dRPC and some Ankr endpoints return HTTP 500 when ethers.js auto-detects network. Fix: `new ethers.JsonRpcProvider(RPC_URL, 1, { staticNetwork: true })`. Diagnosis: curl to RPC works but ethers.js throws "server response 500 Internal Server Error". See `ethers-js` skill for details.

32. **A100 GPU is poor for keccak256 mining** — A100 SXM4 achieves only ~2.5-3.5 GH/s for keccak256 despite being a top ML GPU. RTX 4090 achieves ~4.5-5 GH/s at lower cost. A100 is optimized for FP16/BF16 matrix ops, not integer hash ops. For keccak256 mining, always prefer RTX 4090/5090 over A100/H100.

26. **eth.llamarpc.com is unreliable for Ethereum mainnet calls** — Returns `header not found` (-32014) errors on `eth_call`, causing `missing revert data` in ethers.js. This looks like a contract revert but is actually an RPC issue. Use `https://ethereum-rpc.publicnode.com` as default for Ethereum mainnet. Always check `err.info?.error?.code` — if `-32014`, it's the RPC, not the contract.
27. **"missing revert data" can mean two things on $HASH** — (a) RPC issue (llamarpc, see above) or (b) genesis not complete yet. Check `contract.genesisComplete()` first, then verify RPC health. Don't assume contract revert without ruling out RPC.
28. **Batch parallel minting vs sequential** — When MCP/relayer backends are unstable (frequent 500/502), **sequential minting (1 slot at a time) is more reliable than batch parallel**. User signal: "satu satu aja deh jangan batch" after batch attempt hung. Reason: parallel requests amplify backend load and all fail together when server is degraded. Sequential with aggressive retry (2s) gives each mint the best chance to slip through during brief windows of server availability. Only use batch parallel when backend is proven stable.
28. **Node.js keccak256 is 50-100x slower than browser WASM for PoW mining** — `ethers.keccak256()` in Node.js worker_threads achieves ~1.7 MH/s on 64 cores. Browser Chrome WASM achieves ~12 MH/s per worker (8 workers = ~95 MH/s). For browser-mined PoW tokens (e.g., $HASH on hash256.org), always recommend the user mine from their browser first. VPS Node.js mining is only worth it for multi-wallet parallelism, not raw hashrate. Native C (`gcc -O3 -march=native`) gets ~10 MH/s total on 64 cores — better than Node.js but still 10x behind browser WASM. The gap is V8's WASM SIMD optimization which C without explicit AVX2 intrinsics can't match easily.

28. **Browser WASM mining vs VPS native C** — For browser-based PoW tokens (hash256.org $HASH, rpow2.com), Chrome's V8 WASM is 50-100x faster than Node.js `ethers.keccak256`. VPS mining with Node.js is ~1.7 MH/s; native C multi-process is ~42 MH/s; browser WASM is ~95 MH/s. VPS is viable for extra wallets but won't beat a good PC running Chrome.
28b. **Multi-process beats pthreads for CPU-bound PoW mining** — Spawning N independent single-threaded C processes (each with own nonce range, no shared state) achieves ~99% CPU utilization. A single C process with pthreads + mutex achieves only ~62% due to lock contention. Pattern: `spawn(miner-solo, [challenge, difficulty, nonce_start=i, nonce_step=N])` for i in 0..N, kill all when first finds solution.
28c. **Hyperthreading doesn't help for PoW mining** — keccak256/SHA256 are pure integer ops that saturate a single core's ALU. Two HT threads on one physical core compete for the same execution units. Use physical core count only (e.g., 32 workers on a 32-core/64-thread CPU, not 64).
27. **CPU mining: multi-process beats pthreads** — For CPU-bound PoW mining (keccak256, SHA256), spawning N independent single-threaded processes achieves ~99% CPU utilization. A single process with N pthreads sharing a `global_found` mutex only achieves ~50% CPU due to lock contention. Pattern: `spawn N processes, each with nonce_start=i, nonce_step=N, first to find kills others`. Use `nproc` for worker count (logical CPUs, not physical — hyperthreading helps for independent processes). Measured: 64 pthreads = ~50% CPU, 64 independent processes = ~99% CPU on Threadripper 3970X.
28. **Browser WASM >> Node.js for keccak256** — Browser Chrome V8 WASM achieves ~10x higher hashrate than Node.js ethers.js for keccak256. A PC with 8 cores in browser can outperform a 64-core VPS running Node.js. For browser-mined tokens (hash256.org), native C multi-process is the right VPS approach (~84 MH/s on 64 cores), not Node.js workers (~1.7 MH/s).
28. **CPU mining: multi-process beats multi-thread for keccak256** — pthreads with mutex gives ~50-60% CPU utilization due to lock contention. Spawning N independent processes (each with own nonce range, no shared state) gives ~99% CPU. Pattern: `./miner-solo challenge diff nonce_start nonce_step` — process 0 starts at 0 step N, process 1 starts at 1 step N, etc. First to find prints FOUND, Node.js kills others. See `templates/hash256-miner-solo.c` and `templates/hash256-miner-v3.js`.

27. **Browser PoW mining (keccak256) — CPU multi-process beats pthreads** — For browser-mined tokens like $HASH (hash256.org), spawning N independent single-threaded C processes achieves ~99% CPU utilization. pthreads with shared `found_flag` + mutex only achieves ~50% due to lock contention. Rule: `WORKERS=$(nproc)` (logical CPUs, not physical) for max throughput. Hyperthreading helps for keccak256.

28. **Browser PoW mining — Node.js is slow, C is fast, CUDA is fastest** — ethers.js `solidityPackedKeccak256` in a tight loop = ~1.7 MH/s regardless of workers. Native C multi-process = ~84 MH/s (64-core). CUDA GPU = ~500+ MH/s per GPU. Always use native C or CUDA for serious mining. Node.js is only for orchestration (fetch challenge, submit tx).

29. **NEVER generate random hex strings as addresses/private keys**: generating a random 40-char hex string as "address" and a separate random 64-char hex as "private key" WITHOUT deriving the address from the PK. This results in an address that receives funds but has NO valid private key to access them. **Always use proper key generation:**
    ```javascript
    // CORRECT: generate PK first, derive address
    const wallet = ethers.Wallet.createRandom();
    console.log({ address: wallet.address, privateKey: wallet.privateKey });
    
    // CORRECT: derive address from existing PK
    const wallet = new ethers.Wallet(privateKey);
    console.log({ address: wallet.address }); // verify match!
    
    // WRONG: random strings (FUNDS LOST FOREVER)
    const fakeAddress = '0x' + crypto.randomBytes(20).toString('hex');
    const fakePK = '0x' + crypto.randomBytes(32).toString('hex');
    // These are NOT mathematically related!
    ```
    User signal: "yg ini pk nya gaada jaringan evm loh" or "address sudah benar tapi ga bisa diakses". Recovery: IMPOSSIBLE. Funds sent to orphan addresses are permanently lost. Always verify address matches PK using `eth_account` or `ethers` BEFORE asking user to send funds.

## VPS Deployment (24h Auto-Loop)

### Built-in Loop Command
Add an `autoLoop()` function to the script that runs `daily()` in an infinite loop with jitter:
```javascript
async function autoLoop() {
    const INTERVAL_HOURS = 24;
    const JITTER_MINUTES = 60; // ±60 min randomization
    while (true) {
        try { await daily(); } catch (err) { console.log('Cycle error:', err.message); }
        const jitter = (Math.random() * 2 - 1) * JITTER_MINUTES * 60 * 1000;
        const waitMs = INTERVAL_HOURS * 60 * 60 * 1000 + jitter;
        await sleep(waitMs);
    }
}
```
This is the **simplest VPS option** — no external scheduler needed.

### Running on VPS (3 methods, prefer dual-layer)
```bash
# Method 1: screen (simplest)
screen -dmS farmname node giwa-bot.js loop
# Reattach: screen -r farmname

# Method 2: PM2 (auto-restart + survive reboot)
npm install -g pm2
pm2 start giwa-bot.js -- loop
pm2 save && pm2 startup

# Method 3: crontab (most reliable for single daily run)
crontab -e
# 0 8 * * * cd /root/project-testnet && /usr/bin/node bot.js daily >> farm.log 2>&1
```

**Best practice: dual-layer** — run `screen` loop as primary + Hermes cronjob as watchdog/reporter. The cronjob does NOT farm — it checks if screen is alive, reports wallet status to user, and restarts screen if dead. This way: if screen dies (VPS reboot), cronjob catches it. If Hermes is down, screen keeps going. User still gets daily reports.

```bash
# Hermes cronjob prompt (watchdog pattern):
# "Check screen -ls | grep farmname. If dead, restart: screen -dmS farmname node bot.js loop.
#  Run node bot.js status. Report summary to user."
```

### Sharing Scripts to Others
When packaging for distribution:
- Ship only `bot.js` + `package.json` (no `node_modules/`, no `wallets.json`, no lockfile)
- Common issue: recipient's npm points to China mirror (`mirrors.tencentyun.com`) → fix: `npm config set registry https://registry.npmjs.org/`
- Remove heavy deps like `playwright` — keep it to `ethers` only for portability
- Include clear Quick Start in the script's help text

## Verification
```bash
node status.js  # All wallets should show non-zero nonce after interactions
```
Check explorer to confirm transactions are visible.

## Reference Files
- `references/eip7702-delegation-rpc-pitfalls.md` — **EIP-7702 delegation RPC issues**: delegated EOAs cannot send normal transfers (must revoke first), free-tier RPC timeout on waitForTransactionReceipt, gas estimation failures on self-txs, npm env var inheritance, test-first workflow (user frustration signal), web UI detection issues, MCP server timeouts
- `references/eip7702-mcp-minting.md` — **EIP-7702 + MCP minting pattern** (brainrot.dog $ROT, dogeshit.meme): complete multi-wallet farming architecture, wallet generation, ETH distribution, delegation automation, MCP mint calls, retry logic, shell wrappers, gas estimation, logging patterns
- `references/brainrot-rot-minting.md` — Brainrot `$ROT` token minting: EIP-7702 delegation + MCP-gated minting via relayer, multi-wallet farming scripts, budget planning, retry logic
- `references/brainrot-rot-minting-rpc-strategy.md` — **RPC strategy for unreliable backends**: test-and-hold beats time-based rotation, manual switching based on observed results, batch vs sequential minting, why public RPC can outperform premium, aggressive retry configuration
- `references/wallet-generation-critical-failures.md` — **Case study: orphan address fund loss** — what happens when you type random hex strings instead of proper key generation, verification protocol, user signals, prevention checklist
- `references/giwa-testnet.md` — GIWA Chain (Upbit L2) specific details: contracts, dependency chain, budget planning, Cloudflare findings
- `references/arc-testnet.md` — Arc (Circle L1) testnet: network config, 31 protocols to farm (incl. OnchainGM suite, NFTs2Me, Superbridge from @sellmanft May 2026), faucet API (no captcha, 20 USDC/2h, fully scriptable), known contracts + ABIs, 1000-wallet scaling architecture, ETH distribution flow (Sepolia→ARC bridge→distribute), community/Discord access, deploy guide, priority strategy
- `templates/arc-faucet.js` — Drop-in faucet claimer for Arc testnet: batch by index range, USDC+EURC, cooldown tracking via faucet-log.json, 4-5s delay between wallets
- `references/2captcha-turnstile.md` — 2Captcha API for Turnstile solving: when it works vs doesn't, API usage, sitekey discovery
- `references/nft-whitelist-farming.md` — NFT whitelist/allowlist farming: reconnaissance, form submission (browser + direct API/Supabase), OAuth2 PKCE points systems, bulk wallet generation, social task automation, comment crafting, tracking template, project-specific details
- `references/headcase-collective.md` — HeadCase Collective: OAuth2 points-based WL, API endpoints, task IDs, automation flow with CloakBrowser
- `references/project-legitimacy-check.md` — Due diligence workflow: check project legitimacy via X/Twitter smart followers analysis using `twitter` CLI (cookie-based). Search project URL → check sharers' follower counts/bios → assess green/red/yellow flags
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/hash256-mining.md` — **HASH256 ($HASH) browser-mined PoW token** on Ethereum mainnet: contract ABI, mining mechanics, hashrate benchmarks (browser WASM vs Node.js vs native C), working RPC, wallet setup, third-party miner review, QuickPod CPU recommendations
- `references/rpow2-mining.md` — rpow2.com browser-based PoW mining
- `references/hash256-mining.md` — hash256.org $HASH token: contract ABI, multi-process C miner, VPS setup, hashrate benchmarks, pitfalls (Hal Finney tribute): magic link login, SHA-256 trailing-zeros PoW algorithm, API endpoints, VPS miner deployment, official CLI + native C miner setup (Windows/Linux), MSYS2 UCRT64 vs MinGW pitfall, Long Shot gambling feature (10:1 odds, auto-stop script)
- `references/hash256-mining.md` — **$HASH token mining** (hash256.org): correct ABI, hashrate benchmarks (browser WASM vs Node.js vs native C), RPC notes, multi-wallet strategy, third-party miner evaluation
- `templates/hash256-miner-v2.js` — Node.js wrapper that spawns native C binary for $HASH mining (multi-worker, auto-submit)
- `references/rpow2-longshot.md` — Long Shot gambling feature: API endpoints, odds math, house edge, auto-spinner script pattern, rate limits, 10:1 vs 1:1 strategy, Long Shot gambling API endpoints + auto-spinner
- `scripts/rpow2_miner.py` — Ready-to-run Python CPU miner for rpow2.com (update COOKIE before use)
- `scripts/longshot.py` — Auto-spinner for RPOW2 Long Shot (1:1 odds, stake < 1 RPOW, auto-stop on low balance)
- `templates/npm-wrapper.sh` — Shell wrapper template for npm scripts that need .env variables (solves `npm run` not inheriting env)
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/hash256-mining.md` — $HASH (hash256.org) browser-mined PoW token: correct ABI, mining mechanics, hashrate benchmarks, optimal VPS multi-process architecture, RPC notes, VPS cost comparison
- `templates/hash256-miner-solo.c` — Single-process keccak256 C miner (no threads/mutex). Spawn N independently for max CPU utilization.
- `templates/hash256-miner-v3.js` — Node.js wrapper: spawns N independent C processes, fetches challenge from contract, submits mine() tx on success.

## NFT Whitelist
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/hash256-mining.md` — $HASH (hash256.org) browser/CPU PoW mining on Ethereum mainnet: contract address, ABI, difficulty math, RPC notes, common errors
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/hash256-mining.md` — **hash256.org $HASH token mining**: contract ABI, keccak256 algorithm, multi-process C miner architecture, hashrate benchmarks, VPS platform comparison, GPU mining notes, pitfalls (wrong ABI, wrong challenge, llamarpc broken)
- `templates/hash256-miner-solo.c` — Single-process C keccak256 miner (no deps, compile with gcc -O3 -march=native)
- `references/uniswap-v4-bonding-curve-buy.md` — Buying tokens via Uniswap V4 hook bonding curves (j3sse.org on Base): architecture, web3.py buy flow, calldata encoding, pitfalls (insufficient funds math, nonce inflation, selfDeprecated flag)
- `references/hash256-mining.md` — **hash256.org $HASH token mining**: contract ABI, keccak256 PoW mechanics, CPU multi-process architecture, CUDA GPU mining (RTX 5090 verified), cost comparison table, pitfalls (wrong ABI, challenge generation, RPC issues)
- `templates/hash256-cpu-miner-solo.c` — Single-process C keccak256 miner for $HASH (spawn N copies for parallel mining, no mutex overhead)
- `templates/hash256-cuda-miner.cu` — CUDA GPU keccak256 miner for $HASH (verified against ethers.js, supports multi-GPU with gpu_id offset)
- `templates/arc-mass-register.ts` — Arc ERC-8004 AI agent mass registration template (multi-worker, 2Captcha v2 bypass, proxy rotation, resume support)

## NFT Whitelist/Allowlist Farming

See `references/nft-whitelist-farming.md` for the full methodology covering:
- **Reconnaissance**: Finding WL forms (SPA modals, external forms), extracting requirements
- **Social Tasks**: Twitter follow/like/RT/comment automation via xurl CLI
- **Form Submission**: Direct Supabase API bypass for bulk (5000+ submissions in 25 seconds)
- **Bulk Wallets**: `eth_account.Account.create_with_mnemonic()` for EVM wallets with seed phrases
- **Tracking**: Active WL application status table
- **Pitfalls**: Honeypot fields, SPA modals, Supabase RLS, Discord onboarding quizzes
