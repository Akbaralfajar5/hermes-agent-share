# Web3 Bot Automation Skills Landscape

Surveyed 2025-07. For building Node.js bots that automate: wallet connection to websites, NFT minting, token claiming/airdrop, social verification (Twitter/X, Discord), and multi-account management across EVM and Solana chains.

## Key Insight

**No single skill covers the full bot pipeline.** Each project (mint site, airdrop claim page) has a unique website flow. The toolkit approach is: browser automation + wallet libraries + social auth + chain-specific skills.

## Architecture of a Typical Web3 Automation Bot (Node.js)

```
┌─────────────────────────────────────────────┐
│           BOT AUTOMATION (Node.js)          │
├─────────────────────────────────────────────┤
│ 1. Browser Automation Layer                 │
│    └─ Puppeteer / Playwright (headless)     │
│    └─ MetaMask/Phantom extension injection  │
│                                             │
│ 2. Wallet Layer                             │
│    ├─ EVM: ethers.js + private key signing  │
│    └─ Solana: @solana/web3.js + Keypair     │
│                                             │
│ 3. Social Auth Layer                        │
│    ├─ Twitter/X: OAuth 1.0a / cookie session│
│    └─ Discord: OAuth2 / bot token           │
│                                             │
│ 4. Task Execution Layer                     │
│    ├─ Connect wallet to website             │
│    ├─ Mint NFT (sign transaction)           │
│    ├─ Claim token/airdrop                   │
│    └─ Verify social (X, Discord)            │
│                                             │
│ 5. Multi-Account Management                 │
│    ├─ Proxy rotation                        │
│    ├─ Wallet array management               │
│    └─ Session/cookie persistence            │
└─────────────────────────────────────────────┘
```

## Recommended Skill Bundle (10 skills)

### Core: Browser Automation

| Skill | Source | Installs | Resolved Path | Notes |
|-------|--------|----------|---------------|-------|

**Install commands:**
```bash
```

### EVM Chain (Ethereum, Base, Arbitrum, etc.)

| Skill | Source | Installs | Resolved Path | Notes |
|-------|--------|----------|---------------|-------|
| `ethereum-wingman` | BuidlGuidl (pre-installed) | — | autonomous-ai-agents | Full Ethereum/DeFi dev, Scaffold-ETH 2, Solidity, security |
| `nodejs-keccak256` | affaan-m/everything-claude-code | 1.3K | `.agents/skills/...` (complex path) | Node.js crypto hashing for EVM signing |

**Install commands:**
```bash
# ethereum-wingman: usually pre-installed
# nodejs-keccak256: complex repo structure, path discovery needed via tree API
```

### Solana Chain

| Skill | Source | Installs | Resolved Path | Notes |
|-------|--------|----------|---------------|-------|

**Install commands:**
```bash
```

**Download helius-phantom reference files (important — not auto-fetched):**
```bash
SKILL_DIR="$HOME/.hermes/skills/software-development/helius-phantom"
mkdir -p "$SKILL_DIR/references"
for ref in browser-sdk.md helius-das.md helius-wallet-api.md nft-minting.md payments.md transactions.md integration-patterns.md token-gating.md; do
  curl -sf "https://raw.githubusercontent.com/sendaifun/skills/main/skills/helius-phantom/references/$ref" -o "$SKILL_DIR/references/$ref"
done
```

### NFT Minting

| Skill | Source | Installs | Resolved Path | Notes |
|-------|--------|----------|---------------|-------|

**Install + download references:**
```bash

SKILL_DIR="$HOME/.hermes/skills/software-development/manifold-nft-minting"
mkdir -p "$SKILL_DIR/references"
for ref in minting-bot.md purchase-flow.md transaction-steps.md getting-started.md networks.md error-handling.md adapters.md full-docs.md product-data.md product-types.md rainbowkit-setup.md react-minting-app.md rpc-setup-guide.md studio-setup-guide.md; do
  curl -sf "https://raw.githubusercontent.com/manifoldxyz/manifold-ai/main/skills/manifold-nft-minting/references/$ref" -o "$SKILL_DIR/references/$ref"
done
```

### Social Auth (Twitter/X & Discord)

| Skill | Source | Installs | Notes |
|-------|--------|----------|-------|
| `xurl` | builtin | — | Twitter/X API: post, search, DM, media (pre-installed) |
| `discord-bot-architect` | sickn33/antigravity-awesome-skills | 925 | Discord bot architecture |
| `discord-bot` | claude-office-skills/skills | 738 | Discord bot development |
| `twitter` | sundial-org/awesome-openclaw-skills | 10 | Twitter/X integration |

**Note:** For bot automation, Twitter/X and Discord linking is typically done via:
- **Twitter/X:** OAuth 1.0a flow or injecting auth cookies into headless browser
- **Discord:** OAuth2 authorization code flow or bot token
- The `xurl` builtin skill covers X API interaction; for OAuth flows in a bot context, custom code is needed

## What Still Needs Custom Code (No Skill Covers These)

1. **MetaMask/Phantom extension injection in headless browser** — Loading wallet extensions in Puppeteer/Playwright with `--load-extension` flag, auto-importing private keys
2. **Anti-detection** — Fingerprint randomization, proxy rotation, user-agent spoofing (puppeteer-extra-plugin-stealth)
3. **Multi-wallet orchestration** — Managing arrays of wallets, sequential/parallel execution, cooldown timers
4. **Site-specific scraping logic** — Each mint/claim site has unique DOM structure and flow
5. **OAuth cookie injection** — Persisting Twitter/Discord sessions across bot runs

## Verification After Install

```bash
hermes skills list 2>&1 | grep -E "puppeteer|ethers|phantom|helius|manifold|browser-automation|wallet-monitoring|pump-analyzer|xurl|ethereum-wingman"
```

Expected: all 10 skills showing `enabled`.

## Search Queries Used to Discover These

```bash
npx skills find "web3 bot automation wallet"
npx skills find "airdrop claim mint NFT"
npx skills find "puppeteer playwright browser automation crypto"
npx skills find "solana token bot script"
npx skills find "discord bot twitter oauth connect"
npx skills find "ethers web3js solana web3 nodejs"
npx skills find "selenium headless chrome wallet extension metamask phantom"
```
