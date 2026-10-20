# dogeshit.meme — First EIP-7702 + MCP Mint (May 2026)

## Project Info
- **URL**: https://dogeshit.meme
- **Token**: $SHIT (Dogeshit)
- **Chain**: Ethereum L1 (chainId 1)
- **Twitter**: No official account found (@dogaborshit = not exist)
- **Chrome Extension**: Dogeshit Wallet (epbdphmhjbjiemaeabfkghhopangghli), 26 users, v0.5.3

## Contract Addresses
- **Token (ERC20)**: `0xaF1E52927d724Fd34773Bd53adA57f4C2B742069`
  - Name: Dogeshit, Symbol: SHIT, Decimals: 18
  - Functions: balanceOf, totalMints, mintsOf, mint (internal)
- **MintDelegate**: `0x4206936776996fD5DFd13dB2D69b38a5FA23C848`
  - Functions: mint(), batchMint(uint256), RELAYER(), TOKEN(), FEE_WEI(), LP_RESERVE()
  - Selectors: 0x1249c58b (mint), 0x8467be0d (batchMint), 0x82bfefc8 (TOKEN), 0xfdf6642e (FEE_WEI), 0x1cda51f1 (LP_RESERVE)
- **Relayer**: `0xFa0515D0AD9651B9aC0275E543251AfdbF1Cd86B`
- **LP Reserve**: `0x9Cd0137C159e100C5708360b7d586Ce735cBE274` (also delegated, holds 16+ ETH)

## Config Endpoint
```
GET https://dogeshit.meme/api/config
{
  "chain": "Ethereum",
  "relayer": "0xFa0515D0AD9651B9aC0275E543251AfdbF1Cd86B",
  "token": "0xaF1E52927d724Fd34773Bd53adA57f4C2B742069",
  "mintDelegate": "0x4206936776996fD5DFd13dB2D69b38a5FA23C848",
  "feeWei": "1110000000000000",
  "maxTotalMints": "21000",
  "mintAmount": "10000000000000000000000000",
  "maxPerWallet": "10",
  "baselineSupply": "210690000000000000000000000000",
  "maxSupply": "420690000000000000000000000000"
}
```

## Tokenomics
- Fee per mint: 0.00111 ETH (~$2.54 at $2289 ETH)
- Per mint: 10,000,000 $SHIT (10M)
- Max per wallet: 10 mints (100M $SHIT)
- Max total mints: 21,000
- **Total supply: 420.69B $SHIT**
- Public mint supply: 210B $SHIT (50%)
- LP reserve: 210B $SHIT
- Team: 690M $SHIT

## Post-Mint Market Data (May 8 2026)
- **Supply exhausted**: All 21,000 mints claimed
- **DEX**: Uniswap V3 (ETH L1), multiple pools
- **Main pool liquidity**: ~$57K
- **Price after mint**: ~$0.0000035
- **FDV**: ~$740K
- **24h pump**: +753% after supply cap hit
- **DexScreener**: `https://api.dexscreener.com/latest/dex/search?q=dogeshit`
- **Thin liquidity warning**: >$500 trades cause significant slippage

## API Endpoints Found
- `GET /api/config` — public config
- `GET /api/oauth/session/{id}` — check OAuth session
- `POST /api/oauth/siwe-verify` — verify SIWE signature
- `POST /api/oauth/consent` — approve OAuth, returns redirect_to
- `POST /mcp` — MCP endpoint (IP-restricted to Claude.ai)

## On-Chain Enforcement
```
token contract: tx.origin == RELAYER && msg.sender.code == 0xef0100 || MINT_DELEGATE
receiver is always msg.sender — even the relayer can't mint to anyone else
```

## Relayer Behavior (observed May 8 2026)
- Gas cap: 4.21 gwei (refuses to send if base fee exceeds this)
- Queue limit: 50 in-flight transactions
- Nonce progression: 1930 → 1986 in ~30 min during peak
- Sends batchMint(N) to delegated wallets (type 2 tx, gasLimit 280000)

## CT China Sentiment (May 8 2026)
- @Feng_btc (11.6K followers): "有claude的可以打...好像一发有几U利润"
- @Big_Tea_Rice (16.7K): "有Claude的可以看看这个...自行决定 钱包用新钱包！"
- @luyuban69 (3.9K): "已铸造：8723 / 21000 完成度：41.5%"
- All say DYOR, use new wallet
- No official project Twitter account exists

## Key Learnings
1. Config labels are confusing: "token" = ERC20, "mintDelegate" = delegation target
2. EIP-7702 type-4 tx can show status:0 but delegation still applies
3. MCP endpoint strictly IP-whitelisted (Cloudflare level)
4. Claude.ai Free tier CAN use MCP connectors (confirmed)
5. Relayer gas cap is the main bottleneck during high-gas periods
6. Claude.ai Free tier may timeout on first MCP call ("Gathering my thoughts" for minutes) — be patient
7. Claude responds "What are you looking to create?" if MCP connector not properly linked
8. When Claude shows "Searched available tools >" = MCP is working
9. Relayer queue 50/50 is application-level, not blockchain mempool congestion
10. Gas cap (4.21 gwei) is hard-coded server-side — no user override possible
11. `twitter search` CLI (cookie-based) works for CT due diligence when xurl has no auth
12. Foundry `cast` is the best tool for EIP-7702 delegation (supports --auth flag natively)
13. **EIP-7702 MUST be signed in browser** at `/connect` page — Claude.ai says "wallet hasn't been authorized yet" without the browser OAuth/SIWE flow, even if delegation was done via cast
14. Supply exhausted quickly (~hours) — multi-wallet strategy needs to be ready BEFORE mint goes live
15. Post-mint pump is typical (+700%+) but liquidity is thin — sell early or hold with tight SL
