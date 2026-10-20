# Binance CLI Reference (from binance-trading skill)

## Setup
- **Node.js 22+** required (binance-cli uses ESM `styleText` from `node:util`)
- Install: `source ~/.nvm/nvm.sh && nvm use 22 && npm install -g @binance/binance-cli`
- Verify: `binance-cli --version`

## Authentication
```bash
export BINANCE_API_KEY="<key>"
export BINANCE_SECRET_KEY="<secret>"
```
Or profiles: `binance-cli profile create --name <name> --api-key <key> --api-secret <secret> --env <prod|testnet|demo>`

## API Key Creation Checklist
1. Binance → API Management → Create API → System generated (HMAC)
2. Must add server IP to whitelist BEFORE enabling trading permissions
3. Enable: ✅ Reading, ✅ Spot & Margin Trading, ✅ Futures
4. Do NOT enable: ❌ Withdrawals
5. IP restriction is mandatory

## Available Subcommands
| Command | Description |
|---------|-------------|
| `algo` | Algo Trading |
| `convert` | Convert |
| `copy-trading` | Copy Trading |
| `derivatives-options` | Options |
| `futures-coin` | COIN-M Futures |
| `futures-usds` | USDS-M Futures |
| `margin-trading` | Margin Trading |
| `spot` | Spot Trading |
| `wallet` | Wallet |

## Common Commands
```bash
binance-cli futures-usds futures-account-balance-v3
binance-cli spot get-account
binance-cli futures-usds new-order --symbol INJUSDT --side BUY --type LIMIT --quantity 100 --price 3.55 --time-in-force GTC
binance-cli futures-usds new-order --symbol INJUSDT --side SELL --type STOP_MARKET --stop-price 3.18 --close-position true
```

## Pitfalls
- Spot: `binance-cli spot get-account` (NOT `account-information`)
- Futures: `binance-cli futures-usds futures-account-balance-v3`
- Run `binance-cli spot` or `binance-cli futures-usds` with no subcommand to see available commands
- IP whitelist gotcha: Binance UI disables trading permission checkboxes until at least one trusted IP is entered
- For endpoints not listed, use: `binance-cli request (GET|POST|PUT...) <url> [--signed] --param1 value`
