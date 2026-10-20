# Uniswap V4 Bonding Curve Buy (j3sse.org pattern)

## Overview
Some tokens use Uniswap V4 hooks as bonding curves — no traditional LP, no AMM pool. Price is a pure math function of cumulative ETH inflow. The hook intercepts every swap and prices it through the curve.

**Key characteristics:**
- Buy/sell ONLY through the router contract (not open market DEX)
- No listing on Uniswap UI or other DEXes
- Always redeemable (sells always work while hook holds ETH reserve)
- Self-deprecating: buys revert after ~99% supply minted
- Anti-whale: per-tx buy cap (e.g., 10 ETH)

## Architecture (j3sse on Base)

| Component | Address | Role |
|-----------|---------|------|
| Token (ERC20) | 0x27306289A9D8237AADC9c1952c3E18a2c93bbbF4 | j3sse ERC20, mint/burn restricted to hook |
| V4 Hook | 0xb7C130e4eFbd2Be8f086f3281Ba8be89d38a6888 | Bonding-curve pricing engine |
| Swap Router | 0x68f869dE2e68985bc75793178fb0117B8d87B076 | Convenience wrapper for buy/sell |
| V4 PoolManager | 0x498581fF718922c3f8e6A244956aF099B2652b2b | Uniswap V4 official singleton on Base |

## How to Buy (web3.py)

### Step 1: Discover the buy function
Use Blockscout API to find recent successful buy txs:
```python
import requests
router_addr = '0x68f869dE2e68985bc75793178fb0117B8d87B076'
url = f"https://base.blockscout.com/api/v2/addresses/{router_addr}/transactions"
resp = requests.get(url, headers={'Accept': 'application/json'}, timeout=15).json()
# Look at decoded_input of successful txs
```

### Step 2: Decode the function signature
For j3sse, the buy function is:
```
buy((address,address,uint24,int24,address) key, address swapper, address recipient)
Selector: 0xaa6efaa6
```

Parameters:
- `key.currency0` = address(0) (ETH)
- `key.currency1` = token address
- `key.fee` = 10000 (1%)
- `key.tickSpacing` = 200
- `key.hooks` = hook contract address
- `swapper` = buyer's address
- `recipient` = buyer's address (same as swapper for self-buy)

### Step 3: Execute buy
```python
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
router_addr = Web3.to_checksum_address('0x68f869dE2e68985bc75793178fb0117B8d87B076')

def pad_address(addr):
    return addr[2:].lower().rjust(64, '0')
def pad_uint(val):
    return hex(val)[2:].rjust(64, '0')

# Build calldata
calldata = '0xaa6efaa6'
calldata += pad_address('0x0000000000000000000000000000000000000000')  # currency0 (ETH)
calldata += pad_address(token_addr)   # currency1
calldata += pad_uint(10000)           # fee
calldata += pad_uint(200)             # tickSpacing
calldata += pad_address(hook_addr)    # hooks
calldata += pad_address(buyer_addr)   # swapper
calldata += pad_address(buyer_addr)   # recipient

# Estimate gas first
gas_est = w3.eth.estimate_gas({
    'to': router_addr,
    'value': buy_amount_wei,
    'from': buyer_addr,
    'data': calldata
})

# Build tx
tx = {
    'to': router_addr,
    'value': buy_amount_wei,
    'gas': int(gas_est * 1.5),
    'gasPrice': w3.eth.gas_price,
    'nonce': w3.eth.get_transaction_count(buyer_addr),
    'chainId': 8453,  # Base
    'data': calldata
}

signed = w3.eth.account.sign_transaction(tx, private_key)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=90)
```

### Step 4: Verify token receipt
```python
# Check Transfer event in logs (topic[0] = Transfer signature)
# Or call balanceOf
balance_data = '0x70a08231' + buyer_addr[2:].lower().rjust(64, '0')
result = w3.eth.call({'to': Web3.to_checksum_address(token_addr), 'data': balance_data})
token_balance = int(result.hex(), 16) / 1e18
```

## Pitfalls

1. **"insufficient funds" even with enough balance** — The error `insufficient funds for gas * price + value` happens when buy_amount + gas_cost > balance. On Base, gas is ~0.006 gwei so gas cost is negligible (~0.000001 ETH), but you must account for it precisely. Use: `buy_amount = balance - (gas_limit * gas_price * 3)` for safety buffer.

2. **Nonce inflation from rejected txs** — RPC-rejected txs (insufficient funds) still increment the pending nonce counter on some nodes. Always use `w3.eth.get_transaction_count(address, 'latest')` not 'pending' for the next tx.

3. **balanceOf returns 0 immediately after tx** — Blockscout/explorers may not index immediately. Check via direct RPC `eth_call` to `balanceOf` — this reads current state and will show the correct balance even before explorer indexes.

4. **Token received but not visible on explorer** — The Transfer event logs confirm receipt. Parse logs from receipt: look for topic[0] = `0xddf252ad...` (Transfer) with topic[2] = your address.

5. **Gas estimate succeeds but tx reverts** — For bonding curves, `selfDeprecated` flag activates at 99% supply. If supply is near cap, your buy may revert with `SelfDeprecatedNoBuys`. Check total supply vs max before buying.

6. **Multiple pools on DexScreener** — Bonding curve tokens show multiple "pools" on DexScreener because each buy/sell creates a separate swap event. The prices may differ slightly. The actual price is determined by the curve formula, not by any pool.

## Bonding Curve Economics (j3sse specific)

- Max supply: 21,000,000 tokens
- ETH hard cap: 500 ETH cumulative inflow
- Price multiplier: 1x at 0 ETH → 20x at 500 ETH
- Buy fee: 1% flat
- Sell fee: 1% (empty) → 10% (at max supply), linear scale
- Per-tx buy cap: 10 ETH
- At 99% minted: `selfDeprecated` flag set, no more buys

## When NOT to use this pattern

- If the token is on a normal Uniswap/DEX pool → use standard swap
- If the project uses MCP-gated minting (like dogeshit.meme) → see eip7702-mcp-minting.md
- If it's a testnet token → use testnet faucet patterns

## Reverse Engineering Unknown Bonding Curves

When encountering a new bonding curve project:

1. **Check Blockscout for recent txs** to the router/hook contract
2. **Look at decoded_input** to understand function signature and params
3. **Read the whitepaper** for curve formula and fee structure
4. **Simulate with eth_call** before sending real tx
5. **Start with small amount** to verify the flow works
6. **Check selfDeprecated/paused state** before large buys
