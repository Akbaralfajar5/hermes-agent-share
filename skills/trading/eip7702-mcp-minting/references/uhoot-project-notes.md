# uHOOT Project Notes (May 2026)

## Overview

**URL:** https://uhoot.art/  
**Status:** Pre-launch (Swap = "SOON" as of May 10, 2026)  
**Chain:** Ethereum mainnet  
**Supply:** 5,000 uHOOT (hard cap)

## Mechanism

uHOOT is a hybrid ERC-20 + NFT system built on **Uniswap v4 hooks**:
- Token and NFT are the **same thing** — no separate contract
- **Buy uHOOT = NFT minted automatically** via afterSwap hook
- **Sell uHOOT = NFT burned permanently** (no recovery)
- No separate mint transaction, no whitelist, no pre-registration

## NFT Life Stages

| Stage | Hold Time | Notes |
|-------|-----------|-------|
| Egg | 0h (mint) | Traits sealed, only body palette visible |
| Hatchling | 24h continuous | Traits start revealing |
| Fledgling | 48h continuous | |
| Adult | 72h continuous | Full traits revealed |

- Highest stage ever reached is **locked permanently** (never regresses)
- Transfer resets hold timer to 0 (but stage lock preserved)
- Only whole tokens mint Hoots (0.4 uHOOT = 0 Hoots, 2.7 uHOOT = 2 Hoots)

## Launch Mechanics

- **Anti-sniper tax:** 25% at launch, drops 1%/5min → 0% after ~2 hours
- **Anti-whale cap:** First 5 hours: max 15 Hoots per buy (tokens arrive in full, only Hoot count capped)
- After 5 hours: no restrictions

## Strategy Notes

- Buy early (after tax drops below ~5%) to get lower-cost Hoots
- Hold 72h for Adult stage (higher rarity, better resale)
- Selling destroys NFT permanently — no partial exit
- Scarcity is price-implied: as price rises, most buys become fractional → fewer Hoots minted per trade
- Max 5,000 Hoots can exist simultaneously

## Contracts (to be confirmed at launch)

- Token contract: TBD
- Pool: Uniswap v4 with custom hook

## Related

- "The Oracle" section on site — may have additional mechanics
- Swap and Explore features marked "SOON"
