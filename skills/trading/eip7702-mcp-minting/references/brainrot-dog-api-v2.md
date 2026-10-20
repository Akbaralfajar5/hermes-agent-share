# brainrot.dog MCP API v2 (May 2026)

## Tool List (current as of May 10, 2026)

Discovered via `tools/list` call:

| Tool | Description |
|------|-------------|
| `check_wallet` | Check delegation status, ETH balance, ROT balance, slots used/remaining |
| `get_supply` | Get remaining global mint slots (out of 20,000 total) |
| `mint` | Mint 1 slot (25,500 ROT). Returns tx hash OR job_id if relayer busy |
| `batch_mint` | Mint multiple slots at once (1-10). More gas-efficient |
| `check_mint_status` | Poll status of queued job_id |

## check_wallet Response Format

```
address: 0xc5DC85F9b1247aEd32FE49BA523CFB8462208bca
delegated: true
ETH balance: 0.006669360004983144 ETH
$ROT balance: 76500.0 ROT
slots used: 3
slots remaining: 7
```

## mint Response (success)

Returns tx hash directly:
```
tx: 0xe420bd65e755cae590a33b659545c4a7fb176ed78b07ff9a6165d0d4b8c3b066
```

Or job_id if relayer busy:
```
job_id: <uuid>
```

## Working curl Pattern

```bash
MCP_URL="https://www.brainrot.dog/api/mcp"

mcp_call() {
    local tool=$1
    local args=$2
    curl -s -X POST "$MCP_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "{\"jsonrpc\":\"2.0\",\"method\":\"tools/call\",\"params\":{\"name\":\"$tool\",\"arguments\":$args},\"id\":1}" \
        | grep '^data:' | sed 's/^data: //'
}

# Check wallet
mcp_call "check_wallet" "{\"address\":\"0x...\"}"

# Mint
mcp_call "mint" "{\"address\":\"0x...\"}"

# Check job status
mcp_call "check_mint_status" "{\"job_id\":\"<uuid>\"}"
```

## mine-v2.sh Pattern (bash, uses new API)

Key improvements over old script:
- Uses `check_wallet` instead of deprecated `balance`
- Handles both `tx:` (immediate) and `job_id:` (queued) responses
- Parses SSE response with `grep '^data:' | sed 's/^data: //'`
- Uses python3 for JSON parsing (no ethers.js dependency)

See `templates/mine-v2.sh` for full implementation.

## Old vs New Tool Names

| Old (broken) | New (working) |
|---|---|
| `balance` | `check_wallet` |
| `mint` (same name, different schema) | `mint` |
| N/A | `batch_mint` |
| N/A | `check_mint_status` |
| N/A | `get_supply` |

## Error: "Tool balance not found"

This means the script is using old tool names. Update to use `check_wallet`.

## Error: "has 0 slot(s) remaining in per-wallet cap"

MCP relayer counts submitted TXs toward cap even if they revert on-chain.
Wallet is soft-locked. Generate new wallet and continue minting there.

## Contracts (May 2026)

- $ROT token: `0xedbFDb2854C329d003005B6b4385a5D3a35C5722`
- Delegate: `0x1D370cFCeD3c7F9101f5dCa5EE626447276d20be`
- Pool: 20,000 wallets max, 25,500 ROT per slot, 10 slots per wallet
