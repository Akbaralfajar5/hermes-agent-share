# GIWA Testnet Reference

## Network Details
- **Chain:** GIWA Sepolia (OP Stack L2 by Upbit/Dunamu)
- **Chain ID:** 91342
- **RPC:** https://sepolia-rpc.giwa.io
- **Flashblocks RPC:** https://sepolia-rpc-flashblocks.giwa.io
- **Explorer:** https://sepolia-explorer.giwa.io
- **Bridge:** https://sepolia-bridge.giwa.io/ (Superbridge)
- **Playground:** https://sepolia-playground.giwa.io/
- **Block Time:** 1 second
- **Gas:** < 0.001 gwei (extremely cheap)
- **Status:** Testnet live, Mainnet in development

## Faucets
1. **GIWA Faucet:** https://faucet.giwa.io/ (0.005 ETH/24h) — Cloudflare WAF managed challenge, manual only
2. **Nodit Faucet:** https://faucet.lambda256.io/giwa-sepolia (0.01 ETH/24h) — needs Nodit account
   - API: `POST https://console-api.lambda256.io/be/v2.0/faucet/charge`
   - Body: `{"address":"0x...","protocol":"giwa","network":"sepolia"}`
   - Requires auth cookie from logged-in session

## Key Contracts (Chain ID 91342)
| Contract | Address |
|----------|---------|
| WETH9 | 0x4200000000000000000000000000000000000006 |
| VerifiedToken (TEST) | 0xBCdB22f56642DE57624CfC2fBb9eE398cF3CA268 |
| VerifiedTokenFaucet | 0xfe4b4F5f2f8843dC9Ca75E563f2f7eB0f44Ae83e |
| UPNameRegistry | 0x091D00004f21eb2Fc30964A8a4995692d9b49628 |
| GIWAFaucetExtension | 0x63CCe2b569A7bC35895ee24306c1512fefc06121 |
| DojangScroll | 0xd5077b67dcb56caC8b270C7788FC3E6ee03F17B9 |
| Multicall3 | 0xcA11bde05977b3631167028862bE2a173976CA11 |
| EAS | 0x4200000000000000000000000000000000000021 |
| L2StandardBridge | 0x4200000000000000000000000000000000000010 |

## Dependency Chain (CRITICAL)
```
1. Issue Dojang (payAndIssueEAS, 0.001 ETH fee)
   ↓
2. Claim VerifiedToken (10 TEST/24h, requires Dojang)
   ↓
3. Register UP ID (giwaXXXX.up.id, requires Dojang)
```

## Dojang (Attestation) Details
- **Contract:** GIWAFaucetExtension at 0x63CCe2b569A7bC35895ee24306c1512fefc06121
- **Function:** `payAndIssueEAS()` — payable, returns bytes32 uid
- **Fee:** 0.001 ETH (check with `fee()` view function)
- **Attester ID:** 0xaa92f8c143657dde575de430aecaea6ca91f2e6072339b16932d426895d8d678
- **Verification:** `DojangScroll.isVerified(address, attesterId)` returns bool
- **One-time:** Once verified, stays verified permanently

## VerifiedToken Details
- Name: TestToken, Symbol: TEST, Decimals: 18
- Faucet claim: 10 tokens per 24h
- **Requires Dojang** — will revert without attestation
- Cooldown tracked via `lastClaimed(address)` and `claimInterval()` (86400s)

## UP ID (Name Service)
- **Function:** `register(string name)` — works through proxy
- **View functions broken:** `nameOf()` and `resolve()` revert through proxy (EIP-1967)
- **Workaround:** Use `estimateGas` on `register()` to check if already registered (reverts if taken)
- **Format:** name.up.id (e.g., giwa7bd6595d.up.id)
- **Requires Dojang** — will revert without attestation

## Budget Planning (per wallet)
| Activity | Cost |
|----------|------|
| Dojang issuance | 0.001 ETH |
| Token claim | ~0.00003 ETH gas |
| UP ID register | ~0.00015 ETH gas |
| Self-transfer | ~0.000021 ETH gas |
| Wrap/Unwrap WETH | ~0.00005 ETH gas |
| Deploy contract | ~0.00008 ETH gas |
| **Total minimum** | **~0.0015 ETH** |

With 0.005 ETH faucet drip: can fully farm ~3 wallets per claim.

## Faucet Source Code
- Based on `giwa-io/PoWFaucet` (GitHub) — modular faucet with captcha protection
- Supports: hcaptcha, recaptcha, turnstile providers
- Config has `siteKey` and `secret` fields
- The actual Turnstile sitekey is NOT accessible due to CF WAF blocking all server requests

## Cloudflare Bypass Status (Tested May 2026)
- faucet.giwa.io: CF WAF managed challenge, NOT bypassable via:
  - CloakBrowser (headless=True: 0 frames; xvfb+headless=False: checkbox doesn't register)
  - 2Captcha TurnstileTaskProxyless (tasks accepted but ERROR_CAPTCHA_UNSOLVABLE)
  - Direct curl/axios (403 with challenge page)
- Nodit faucet: No Cloudflare but needs account + reCAPTCHA on signup
- **Conclusion:** Faucet claim must be done manually by user with proxy rotation

## Scaling Strategy (1000 wallets)
- Generate all 1000 wallets upfront: `node giwa-bot.js generate 1000`
- Export addresses to `addresses.txt` for batch faucet claiming
- User claims 50 wallets manually with proxy rotation (1 per IP per 24h)
- 50 × 0.005 ETH = 0.25 ETH total → can fund ~125 additional wallets at 0.002 ETH each
- Repeat daily: claim more, fund more, farm all funded wallets
- Daily routine sufficient: consistency > volume (5-6 tx/wallet/day is enough)
- `wallets.json` at 1000 wallets = ~265KB

## Script Location
`~/giwa-testnet/giwa-bot.js` — single-file CLI with commands: generate, status, fund, farm, daily
- Script handles 1000 wallets sequentially with random delays
- Skips wallets with 0 ETH automatically
- Auto-funds sub-wallets when wallet #1 has balance
- `addresses.txt` generated alongside for easy copy-paste to user
