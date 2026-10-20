---
name: dogeshit-meme-mint
description: "EIP-7702 delegation + MCP mint flow for dogeshit.meme ($SHIT token on ETH L1)"
version: 1.0.0
author: hermes
platforms: [linux]
prerequisites:
  commands: [cast]
metadata:
  hermes:
    tags: [crypto, mint, eip-7702, mcp, ethereum]
---

# Dogeshit Meme Mint ($SHIT)

Mint $SHIT tokens via EIP-7702 delegation + Claude.ai MCP connector on Ethereum mainnet.

## Contracts
- **Token ($SHIT ERC20):** `0xaF1E52927d724Fd34773Bd53adA57f4C2B742069`
- **MintDelegate:** `0x4206936776996fD5DFd13dB2D69b38a5FA23C848`
- **Relayer:** `0xFa0515D0AD9651B9aC0275E543251AfdbF1Cd86B`
- **LP Reserve:** `0x9Cd0137C159e100C5708360b7d586Ce735cBE274`

## Config
- Fee: 0.00111 ETH/slot (10M $SHIT per slot)
- Max: 10 slots/wallet (100M $SHIT)
- Gas cap: 4.21 gwei (relayer hard limit)
- Total supply: 420B (210B public mint + 210B LP/team reserve)
- Public mint cap: 21,000 mints (210B $SHIT)

## Steps

### 1. Install Foundry (if needed)
```bash
curl -L https://foundry.paradigm.xyz | bash
export PATH="$HOME/.foundry/bin:$PATH"
foundryup
```

### 2. Delegate wallet to MintDelegate
```bash
PK="<private_key>"
WALLET="<wallet_address>"
MINT_DELEGATE="0x4206936776996fD5DFd13dB2D69b38a5FA23C848"
RPC="https://ethereum-rpc.publicnode.com"

# Send EIP-7702 type-4 tx (self-tx with --auth)
cast send $WALLET --private-key $PK --rpc-url $RPC --auth $MINT_DELEGATE --value 0 --gas-limit 100000

# Verify delegation (should show 0xef01004206...)
cast code $WALLET --rpc-url $RPC
```
Note: TX may show status=0 (failed) but delegation still applies — this is normal for EIP-7702.

### 3. User mints via Claude.ai
1. Open claude.ai → Settings → Konektor → "Tambah konektor kustom"
2. URL: `https://dogeshit.meme/mcp`
3. New chat → "mint me 9 slots" (or however many)
4. Claude triggers OAuth/SIWE flow → user signs in wallet
5. Claude calls relayer via MCP → relayer sends batchMint to delegated wallet

### 4. Monitor
```bash
TOKEN="0xaF1E52927d724Fd34773Bd53adA57f4C2B742069"
# Check mints
cast call $TOKEN "mintsOf(address)(uint256)" $WALLET --rpc-url $RPC
# Check balance
cast call $TOKEN "balanceOf(address)(uint256)" $WALLET --rpc-url $RPC
# Check gas
cast base-fee --rpc-url $RPC  # must be < 4.21 gwei
```

## Pitfalls
- MCP endpoint IP-restricted to Claude.ai servers — cannot call from VPS
- **EIP-7702 must be signed in browser** at `/connect` page — even if delegation done via `cast`, Claude.ai won't recognize the wallet without the browser OAuth/SIWE flow. Claude says "wallet hasn't been authorized yet" without this step.
- Relayer gas cap 4.21 gwei — mint fails if base fee higher. Best time: WIB 07:00-13:00 or weekends
- Relayer queue max 50 concurrent — retry if "queue full"
- Claude Free tier works but has rate limits and may timeout on retries
- Wallet needs ≥0.0112 ETH (0.00111×10 + gas for delegation ~$1.2)
- First delegation tx costs gas from wallet (~36K gas)

## Revoke Delegation
```bash
cast send $WALLET --private-key $PK --rpc-url $RPC --auth 0x0000000000000000000000000000000000000000 --value 0 --gas-limit 100000
```
