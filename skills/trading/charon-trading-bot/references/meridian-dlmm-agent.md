# Meridian — Autonomous DLMM LP Agent

Repo: https://github.com/yunus-0x/meridian (same author as Charon)

Meridian is an autonomous Meteora DLMM liquidity management agent for Solana. Unlike Charon (spot trading pump.fun tokens), Meridian provides liquidity into DLMM pools and earns fees.

## Setup

```bash
git clone https://github.com/yunus-0x/meridian ~/meridian
cd ~/meridian && npm install
```

### .env setup

```env
WALLET_PRIVATE_KEY=<base58 private key>
RPC_URL=https://mainnet.helius-rpc.com/?api-key=<HELIUS_KEY>
HELIUS_API_KEY=<helius_key>
LLM_BASE_URL=<provider_base_url>/v1
LLM_API_KEY=<api_key>
LLM_MODEL=<model_name>
DRY_RUN=true
```

### user-config.json

Copy from `user-config.example.json`. Key fields:
- `dryRun: true` for testing
- `managementModel`, `screeningModel`, `generalModel` — all should match your LLM provider
- `deployAmountSol: 0.5` — base SOL per position
- `maxPositions: 3` — concurrent LP positions

## PITFALL: Custom LLM provider gzip encoding error

Some custom providers return `content-encoding: gzip` header but body isn't compressed. Error: `incorrect header check`.

**Fix:** Patch `agent.js` line ~96 OpenAI client init — add custom fetch:

```javascript
const client = new OpenAI({
  baseURL: process.env.LLM_BASE_URL || "https://openrouter.ai/api/v1",
  apiKey: process.env.LLM_API_KEY || process.env.OPENROUTER_API_KEY,
  timeout: 5 * 60 * 1000,
  fetch: async (url, init) => {
    const resp = await globalThis.fetch(url, {
      ...init,
      headers: { ...init?.headers, 'Accept-Encoding': 'identity' },
    });
    return resp;
  },
});
```

## Running

```bash
# Dry mode (no on-chain tx)
DRY_RUN=true pm2 start index.js --name meridian --update-env

# Live mode
DRY_RUN=false pm2 start index.js --name meridian --update-env

# Logs
pm2 logs meridian --lines 30
```

## PM2 output buffering

PM2 buffers Node.js stdout. Use `stdbuf -oL -eL` for real-time foreground debugging:
```bash
cd ~/meridian && DRY_RUN=true stdbuf -oL -eL timeout 120 node index.js 2>&1
```

## Agent Cycles

| Cycle | Default | Purpose |
|-------|---------|---------|
| Screening | 30 min | Find and deploy into best DLMM pool |
| Management | 10 min | Monitor positions, claim fees, close OOR |

## Safety Checks (executor.js)

- bin_step within [minBinStep, maxBinStep]
- Position count < maxPositions
- No duplicate pool or base token
- SOL balance covers amount + gasReserve
- Single-side SOL deploys only (amount_y)

## Key Differences from Charon

| Aspect | Charon | Meridian |
|--------|--------|----------|
| Asset | Meme coins (spot) | DLMM LP positions |
| Exchange | Pump.fun / Jupiter | Meteora DLMM |
| Revenue | Price appreciation | Trading fees |
| Risk | Token rugs | Impermanent loss, OOR |
| LLM role | BUY/WATCH/PASS | Deploy/Close/Stay/Claim |

## WALLET NOTE

Generated wallet has 0 SOL. For live mode, deposit SOL first:
```
Address: <your_meridian_wallet>
```
