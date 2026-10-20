# RPOW2 Bot Detection Bypass (May 2026)

## Problem
RPOW2 API blocks automated miners with:
- `403 "automated mining clients are not permitted"`
- `403 "outdated browser"`

Simple User-Agent spoofing is insufficient.

## Solution: Full Browser Fingerprint

Requires **11 headers** matching Chrome 135:

```javascript
{
  "accept": "application/json",
  "accept-language": "en-US,en;q=0.9",
  "origin": "https://rpow2.com",
  "referer": "https://rpow2.com/",
  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
  "sec-ch-ua": '"Google Chrome";v="135", "Chromium";v="135", "Not-A.Brand";v="99"',
  "sec-ch-ua-mobile": "?0",
  "sec-ch-ua-platform": '"Windows"',
  "sec-fetch-dest": "empty",
  "sec-fetch-mode": "cors",
  "sec-fetch-site": "same-site"
}
```

## Critical Headers
- `sec-ch-ua*` — Client Hints (Chrome 89+)
- `sec-fetch-*` — Fetch Metadata (Chrome 76+)
- Must match `user-agent` version

## Verified Miners

### stablemarkk/rpow_cli_miner (Recommended)
- Native C miner: 2x faster than Python
- Patch line 497-502 in `rpow-cli.js` with headers above
- Build: `bash build-native.sh` (Linux) or `.\build-native.ps1` (Windows)
- Run: `node rpow-cli.js mine --count 1000 --engine native --workers <N>`
- Cookie injection: `.rpow-cli-state.json` → `{"cookies": {"rpow_session": "..."}}`

### Python fallback
- Use `requests` with full headers dict
- Add random delays (0.5-1.5s) between requests
- Trailing zeros must count from END of hash (reversed bytes)

## Performance
- 2 cores: ~3.4 MH/s (native C)
- 12 cores: ~20 MH/s (estimated)
- Difficulty 25 bits: ~2-20 seconds per solve

## API Endpoints
- `POST /challenge` → get mining task
- `POST /mint` → submit solution
- `GET /me` → check balance
- Cooldown: 2-5 seconds between challenges (429 error)

## Session Cookie Format
```
rpow_session=eyJlbWFpbCI6IjxlbWFpbD4iLCJleHAiOjx0aW1lc3RhbXA+fQ.<signature>
```
Expires ~30 days. No refresh mechanism — must re-login via magic link.
