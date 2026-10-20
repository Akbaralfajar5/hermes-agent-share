# Live Scan Examples — Real Session Results

Reference for calibrating scoring formula against real tokens.

## Example 1: OILMAXXING — Grade B+ [72/100] ✅ BEST OF SESSION
```
CA: FFRQbb9KaXomHrBKrtJ7UxrqSTxDGk8WLjacqnLLpump
MC: $92.8K | Liq: $23.6K | Holders: 4,821
T10: 2.6% ✅ | Bundler: 1.3% ✅ | Bot: 7 (0.12%)
SM: 1 | KOL: 0 | Snipers: 24
Dev: creator_close (0%) — graduated, normal
RugCheck: Score 1 | Top1: 21.4% | Top5: 36.9%
Mint/Freeze: renounced ✅ | LP burned 95%
Social: Twitter @OILMAXXING + website oilmaxxing.lol
CTO: yes
```
**Why it scored well:** Massive holder count (4.8K), extremely low T10 (2.6%), minimal bundler, dev sold (normal for graduated), clean RugCheck. Only weakness: SM=1 (low but not zero).

## Example 2: PARSEC — Grade B [63/100] ⚠️ BOT HEAVY
```
CA: 6fVn7Eiiw1mTKcSYU1kVErEUqfdJ9f11FsyyjtN1pump
MC: $76K | Liq: $20.1K | Holders: 304
T10: 17.4% ✅ | Bundler: 14.6% ⚠️ | Bot: 181 (55.5%) 🚫
SM: 2 (active, holding profit) | KOL: 3 👑 | Snipers: 11
Dev: creator_hold (0%) — first token ever
RugCheck: Score 1 | Top1: 20.7% | Top5: 44.1%
Mint/Freeze: renounced ✅ | LP burned
Social: Twitter @parsec + website parsec.ac
1h: 1004 buys vs 725 sells
```
**Why it scored mid:** Good fundamentals (T10, SM, KOL, RugCheck) but bot 55% dragged it down. Buy pressure strong (1.4:1 ratio). First-time dev is positive signal.

## Example 3: DJBOOM (SpaceX Seal) — Grade B [65/100] ⚠️ BOT+CONCENTRATION
```
CA: BaYJ9uTr7h7qfWhHSNffW41ZQnSbmidFwny9ETYfpump
MC: $22K | Liq: $12.2K | Holders: 631
T10: 20% | Bundler: 10.7% ⚠️ | Bot: 228 (30.2%)
SM: 9 💰 | KOL: 6 👑 | Snipers: 22
Dev: creator_close (0%) — first token
RugCheck: Score 1 | Top1: 24.9% | Top5: 54.8% ⚠️
Mint/Freeze: renounced ✅ | LP burned 95%
Social: Twitter community + charity angle (SR3)
```
**Notable:** Highest SM+KOL count in session (9+6). Charity angle. But Top5 at 54.8% and bot 30% are concerns.

## Example 4: CHAD (Yes Chad) — HARD STOP ❌
```
CA: H3iQhDGEBAJbTxp9x6Tykqpym9Txfka9QY9HwpHdpump
MC: $2.3K | Liq: $4.7K | Holders: 42
T10: 4.2% ✅ | Bundler: 0% ✅ | Bot: 8 (1.8%) ✅
SM: 0 | KOL: 0
RugCheck: Score 2999 | Top1: 94.7% 🚫🚫🚫
```
**WHY HARD STOP:** RugCheck Top1 = 94.7% means ONE wallet holds nearly everything. Despite looking clean on T10/bundler/bot metrics (which come from GMGN), RugCheck reveals the truth. **Always cross-verify with RugCheck — GMGN holder data can be misleading.**

## Example 5: Accelerate — Grade C [48/100] ❌ SERIAL DEPLOYER
```
CA: H4oM947yrUoa3NEAXA83vw2bghNc14ymzb8nWTgapump
MC: $55K | Liq: $16.6K | Holders: 511
T10: 23.6% ⚠️ | Bundler: 13.9% ⚠️ | Bot: 229 (56.2%) 🚫
SM: 6 | KOL: 4
Dev: creator_close — OPEN COUNT: 12 tokens, TWITTER TOKENS: 75 (!!)
RugCheck: Score 1 | Top1: 20.7% | Top5: 48.4%
```
**WHY SKIP:** Dev serial deployer (12 tokens launched, 75 Twitter promotions). Bot 56% without proportional SM engagement.

## Example 6: pickles (grillo's pickles) — HARD STOP ❌
```
CA: Dig6UdRdW3PjzvR1brBXSWSoAoWALS9na9qWTwUUpump
MC: $13.7K | Liq: $8.5K | Holders: 171
SM: 2 | KOL: 5 👑
RugCheck: Score 40801 🚫 | Risk: "Creator history of rugged tokens - danger"
```
**WHY HARD STOP:** RugCheck explicitly flags creator rug history. Score 40801 is extreme. No amount of SM/KOL interest compensates.

## Scoring Calibration Notes

| Scenario | Expected Grade | Notes |
|----------|---------------|-------|
| T10 < 5%, SM >= 3, no bot, RugCheck clean | A (≥75) | Rare but ideal |
| T10 < 20%, SM 2-3, bot < 30%, RugCheck clean | B (60-74) | Good entry candidate |
| T10 < 20%, bot 40-55%, RugCheck clean | B- / C+ (50-63) | Common pattern — bot heavy but fundamentals OK |
| RugCheck Top1 > 50% | HARD STOP | Single wallet domination |
| RugCheck creator rug history | HARD STOP | No exceptions |
| Bot > 50% + SM = 0 | C- / D (< 45) | Pure bot play, skip |
| Dev serial deployer (>5 tokens) | -10 penalty | On top of other scoring |
