# xWorld.global — API-First RE Case Study

## Overview
xWorld is a real-time isometric MMO on Solana. Players mine resources on the Moon, donate to a colony rocket, and earn SPCX (tokenized SpaceX stock).

## Auth Flow (Challenge-Response)
```
1. POST /api/players/challenge  {walletId}  → {ok, nonce}
2. Sign nonce with Solana wallet (nacl.sign.detached)
3. POST /api/players/register   {name, walletId, nonce, signature(base64)} → {ok, name, token, streakData}
```
- Signature is base64-encoded (not hex like EVM)
- Session token returned in register response
- Wallet: Phantom/Solflare (Solana), not MetaMask

## REST API Endpoints
| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/players/challenge` | POST | No | Get auth nonce |
| `/api/players/register` | POST | No | Login/register |
| `/api/players/me?walletId=X` | GET | No | Player state |
| `/api/players/list` | GET | No | All players |
| `/api/players/count` | GET | No | Online count |
| `/api/colony/status` | GET | No | Rocket progress |
| `/api/colony/leaderboard` | GET | No | Top contributors |
| `/api/colony/harvest` | POST | Yes | Harvest resource |
| `/api/colony/donate` | POST | Yes | Donate to rocket |
| `/api/exchange/rate?walletId=X` | GET | No | SOL exchange rate |
| `/api/exchange/claim` | POST | Yes | BBL → SOL exchange |
| `/api/players/kill-mob` | POST | Yes | Report mob kill |
| `/api/players/bounty-complete` | POST | Yes | Complete bounty |

## WebSocket Protocol
- URL: `wss://xworld.global/api/ws`
- Auth: Send `{type:"join", id:walletId, name, ...}` on connect
- Receive: `welcome`, `player_join`, `player_leave`, `launch`, `chat`

## Key Patterns for Solana Wallet Auth
```javascript
// Node.js
const nacl = require('tweetnacl');
const bs58 = require('bs58');
const { Keypair } = require('@solana/web3.js');

const secretKey = bs58.default.decode(PRIVATE_KEY);
const keypair = Keypair.fromSecretKey(secretKey);
const walletId = keypair.publicKey.toBase58();

// Sign challenge
const messageBytes = new TextEncoder().encode(nonce);
const signature = nacl.sign.detached(messageBytes, keypair.secretKey);
const signatureB64 = Buffer.from(signature).toString('base64');
```

## Pitfalls
1. **bs58 v5** — `require('bs58').default` may be undefined. Use `require('bs58').default || require('bs58')`
2. **Output buffering** — Node.js background processes buffer stdout. Use `> file.log 2>&1` or `PYTHONUNBUFFERED=1`
3. **WebSocket reconnect** — Don't create new socket per reconnect without closing old one (memory leak + duplicate connections)
4. **Solana signatures are base64** — not hex like EVM signatures
5. **Session token from register** — not from a separate login endpoint
