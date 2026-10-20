# rpow2.com — Browser-Based PoW Mining

## Overview
- URL: https://rpow2.com/#/
- "A modern tribute to the original RPOW by Hal Finney"
- Browser-based proof-of-work mining (CPU mining via Web Worker)
- Navigation: wallet | mine | send | activity | ledger | login
- Hosted on Netlify (SPA), API at `api.rpow2.com` (nginx/Ubuntu)
- Behind Cloudflare CDN

## Architecture (Updated May 11, 2026 — post-rewrite)
- Frontend: React SPA on Netlify (`rpow2.com`)
- Backend API: `https://api.rpow2.com` (Node.js 22 + Fastify + PostgreSQL 17)
- Infrastructure: OVH VPS (moved from Fly.io)
- Email service: **self-hosted Postfix + Resend fallback** (Postmark removed — was the cause of old intermittent failures)
- Mining worker: Web Worker for PoW (browser), Python/C for VPS
- Key API endpoints:
  - `POST /auth/request` — send magic link (body: `{"email":"...","turnstileToken":"..."}`) — **Turnstile required**
  - `GET /auth/verify?token=TOKEN` — verify magic link, returns Set-Cookie
  - `POST /auth/logout`
  - `GET /me` — current user info (balance, minted, sent, received, daily cap)
  - `POST /challenge` — get mining challenge (body: `{}`)
  - `POST /mint` — submit PoW solution
  - `GET /ledger` — token ledger
  - `POST /send` — transfer tokens

## New Features (post-rewrite)
- **Solana Bridge** — RPOW wrappable as SRPOW (SPL token) on Solana
- **Long Shot** — gambling feature (allowlist-gated)
- **Daily mint cap** — 1,000 RPOW/day per account (`daily_mint_cap_base_units: 1000000000000`)
- **Total supply** — 19,000,000 RPOW (fixed cap, ~10M already minted as of May 11 2026)
- **Halving** — reward halves at 10B base units minted (currently 0.01 RPOW/block, next: 0.005)

## Login & Auth

### Magic Link Flow
- Enter email → click "SEND LINK" → check inbox for magic link
- Button changes to `[ ... ]` (disabled) when sent successfully
- User email: you@example.com
- Rate limit: 429 with `retry_after` seconds if too many requests

### ⚠️ Turnstile Required (as of May 11, 2026)
- `POST /auth/request` now requires `turnstileToken` field
- Sending empty string `""` returns `{"error":"TURNSTILE_REQUIRED","message":"human verification required"}`
- **Cannot automate login from VPS** — must login from browser manually
- Workflow: user logs in via browser → copies `rpow_session` cookie from DevTools → pastes to agent

### Auth Cookie
- Cookie name: `rpow_session`
- Set on domain: `api.rpow2.com`
- Format: JWT-like base64 payload + HMAC signature
- Payload decodes to: `{"email":"...","exp":TIMESTAMP}` (expiry ~30 days)
- Current cookie (May 11, 2026): expires ~June 8, 2026

### VPS Login Strategy (Updated May 11, 2026)
1. User opens https://rpow2.com in browser
2. Login with email, complete Turnstile captcha
3. Click magic link from inbox
4. Open DevTools → Application → Cookies → `api.rpow2.com`
5. Copy `rpow_session` value, paste to agent
6. Agent updates cookie in `~/rpow2-miner/rpow2_miner_v2.py` and restarts screen

**Note:** Cookie lasts ~30 days so this is infrequent. Old curl-based verify flow still works IF user pastes the raw magic link token (not the full URL) — but Turnstile blocks the initial `/auth/request` step from VPS.

## Postmark Issue — RESOLVED (May 11, 2026)
Postmark has been replaced with self-hosted Postfix + Resend fallback. Email delivery is now reliable. The old intermittent 500 errors and "pending approval" deadlock no longer occur.

## Mining Algorithm (FULLY REVERSE-ENGINEERED)

### Challenge Response
```bash
# Get challenge
curl -s -b "rpow_session=COOKIE" \
  -X POST "https://api.rpow2.com/challenge" \
  -H "Origin: https://rpow2.com" \
  -H "Content-Type: application/json" -d '{}'
```
Response:
```json
{
  "challenge_id": "cac483ed-1618-4441-9b88-a792e9bca372",
  "nonce_prefix": "8f7faa19ec7bddb4efeb6f131e31fdad",
  "difficulty_bits": 25,
  "expires_at": "2026-05-11T04:51:11.980Z"
}
```

### Difficulty (Updated May 11, 2026)
- **Current difficulty: 25 bits** (was 31 bits — ~64x easier now)
- 2^25 = ~33.5M hashes avg
- Python 2-core (~1.9M H/s): ~17 seconds avg — **well within 5 min window**
- This means VPS Python miner is now viable (was ~33% success rate at 31 bits)

### PoW Algorithm (from miner.worker JS)
1. Input = `nonce_prefix` (hex → bytes, 16 bytes) + `nonce` (uint64, 8 bytes little-endian)
2. Hash = SHA-256(input)
3. Count **trailing zero bits** of hash (NOT leading zeros!)
4. If trailing_zeros >= difficulty_bits → solution found
5. Increment nonce and repeat

**Trailing zero bit counting** (critical — different from Bitcoin's leading zeros):
```python
def count_trailing_zeros(hash_bytes):
    count = 0
    for byte in hash_bytes:
        if byte == 0:
            count += 8
            continue
        bit = 0
        while not (byte & (1 << bit)):
            bit += 1
        return count + bit
    return count
```

### Submit Solution
```bash
curl -s -b "rpow_session=COOKIE" \
  -X POST "https://api.rpow2.com/mint" \
  -H "Origin: https://rpow2.com" \
  -H "Content-Type: application/json" \
  -d '{"challenge_id":"UUID","solution_nonce":"12345"}'
```

### Challenge Expiry (CRITICAL)
- **Challenges expire in 5 minutes (300 seconds)**
- If solution not submitted before expiry → 410 `{"error":"CHALLENGE_EXPIRED","message":"expired"}`
- This is the PRIMARY constraint — not hashrate

### Performance & Feasibility
- VPS hashrate (Python, single-core): ~950K H/s (measured), ~1.4M H/s (benchmark)
- VPS hashrate (Python, 2-core multiprocessing): ~1.9M H/s
- Difficulty 31 bits = avg 2^31 = ~2.1 billion hashes
- Estimated time per block (1 core): ~37 minutes
- Estimated time per block (2 cores): ~19 minutes
- **Challenge window: 5 minutes → need ~7.2M H/s to reliably solve**
- **With 2 cores (~1.9M H/s): ~33% chance of solving within 5 min window** (luck-based)
- Strategy: spam challenges continuously, accept ~1/3 success rate
- Better hardware: 8+ cores or C/Rust miner would make it reliable

### Multiprocessing Approach (DEPLOYED)
The actual VPS miner uses `multiprocessing.Process` with:
- Each worker gets `start_nonce=worker_id, step=NUM_WORKERS`
- Shared `Value('i', 0)` flag for found signal
- Main process monitors expiry and terminates workers if <5s remaining
- Auto-skips expired challenges and immediately requests new one

## VPS Miner Script

Location: `/home/ubuntu/rpow2-miner/miner.py`

Features:
- Infinite loop: get challenge → mine → submit → repeat
- Progress reporting every 2 seconds
- Balance check after each mint
- Auto-retry on challenge failure (30s wait)
- Unbuffered output for real-time logging

### Running
```bash
# In screen (preferred)
screen -dmS rpow2 bash -c 'cd /home/ubuntu/rpow2-miner && python3 -u miner.py'

# Check status
screen -r rpow2

# Or with logging
screen -dmS rpow2 bash -c 'cd /home/ubuntu/rpow2-miner && python3 -u miner.py >> miner.log 2>&1'
```

### Cookie Expiry
Cookie expires ~30 days from issue (based on decoded JWT `exp` field).
Current cookie issued: May 8, 2026 (expires ~June 4, 2026).
Need to re-login when expired — user must provide magic link token quickly (<5 min).

## Official CLI + Native C Miner (RECOMMENDED)

An official CLI package exists: `rpow_cli_miner-main` (Node.js wrapper + C miner).

### Included Files
- `rpow-native-miner.c` — Native C miner (much faster than Python/JS)
- `rpow-cli.js` — Node.js orchestrator (login, cookies, API, retries, logs)
- `rpow-miner-worker.js` — JS fallback miner (slower)
- `build-native.ps1` / `build-native.sh` — Build scripts

### Setup (Windows)
```powershell
# 1. Install Node.js 18+
# 2. Install MSYS2 from https://www.msys2.org/
# 3. Open "MSYS2 MinGW x64" (or install gcc in UCRT64 — see pitfall below)
pacman -S --needed mingw-w64-ucrt-x86_64-gcc   # for UCRT64
# OR open MinGW x64 terminal where mingw-w64-x86_64-gcc is already installed
# 4. Build:
cd /c/Users/USER/Downloads/rpow_cli_miner-main
gcc -O3 -march=native -pthread rpow-native-miner.c -o rpow-native-miner.exe
# 5. In PowerShell:
node rpow-cli.js login --email user@example.com
node rpow-cli.js complete-login --link "MAGIC_LINK_FROM_EMAIL"
node rpow-cli.js mine --count 10 --workers 8 --engine native
```

### Setup (Linux/macOS)
```bash
./build-native.sh
node rpow-cli.js login --email EMAIL
node rpow-cli.js complete-login --link "MAGIC_LINK"
node rpow-cli.js mine --count 10 --workers 8 --engine native
```

### MSYS2 Pitfall: UCRT64 vs MinGW x64
- `mingw-w64-x86_64-gcc` is for **MinGW x64** terminal
- `mingw-w64-ucrt-x86_64-gcc` is for **UCRT64** terminal
- If user opens UCRT64 but has MinGW gcc installed → `bash: gcc: command not found`
- Fix: install the matching package for the terminal they opened

### Double Mining
Same email account can mine from multiple machines simultaneously. Balance accumulates to one account. Recommended: PC (native C, 8+ cores) + VPS (Python fallback, 2 cores).

### Useful Commands
```powershell
node rpow-cli.js me          # Check balance
node rpow-cli.js ledger      # Token ledger
node rpow-cli.js activity    # Activity log
node rpow-cli.js mine --verbose  # Detailed HTTP logs
```

## Long Shot (Gambling Feature) — API Endpoints

URL: https://longshot.rpow2.com/
Requires `wrap_allowed: true` on the account (check `/me`).

### Access Check
```bash
curl -s -b "rpow_session=COOKIE" "https://api.rpow2.com/api/longshot/access" \
  -H "Origin: https://longshot.rpow2.com"
# Returns: {"access":"allowed"} or {"access":"denied"}
```

### Stats
```bash
curl -s -b "rpow_session=COOKIE" "https://api.rpow2.com/api/longshot/stats" \
  -H "Origin: https://longshot.rpow2.com"
# Returns: total_spins, total_volume, house_pnl, odds_breakdown (1:1/2:1/3:1/10:1)
```

### History
```bash
curl -s -b "rpow_session=COOKIE" "https://api.rpow2.com/api/longshot/history" \
  -H "Origin: https://longshot.rpow2.com"
```

### Spin (Place Bet)
```bash
curl -s -b "rpow_session=COOKIE" \
  -X POST "https://api.rpow2.com/api/longshot/spin" \
  -H "Content-Type: application/json" \
  -H "Origin: https://longshot.rpow2.com" \
  -d '{"stake_base_units":"970000000","odds_choice":"1:1"}'
# Returns: outcome (WIN/LOSE), net_user_change_base_units, balance_after_base_units
```

**Odds breakdown (observed):** 1:1 wins ~42.8% (428/1000 spins), 2:1 wins ~32.9%, 3:1 wins ~27.4%, 10:1 wins ~6.5%
**Stake must be < 1 RPOW** (970000000 base units = 0.97 RPOW works)
**Auto-spinner script:** `~/rpow2-miner/longshot.py` (screen -S longshot)

### Origin Header for Long Shot
Use `Origin: https://longshot.rpow2.com` (NOT `https://rpow2.com`) for all Long Shot API calls.

---

## Current Status (May 11, 2026)
- ✅ API live and responsive from VPS
- ✅ Login via browser cookie (Turnstile blocks VPS direct login)
- ✅ Cookie obtained May 11 2026, expires ~June 8, 2026
- ✅ `rpow2_miner_v2.py` running in `screen -S rpow2`
- ✅ Difficulty dropped to 25 bits — Python 2-core solves in ~9-17s (reliable!)
- ✅ **Long Shot auto-spinner** running in `screen -S longshot` (`~/rpow2-miner/longshot.py`)
- 💰 Balance: ~158 RPOW (May 11, after longshot spins) | Daily cap: 1000 RPOW/day
- ⚠️ Turnstile on `/auth/request` — cannot automate new account creation from VPS
- ⚠️ Halving approaching: next reward 0.005 RPOW at 10B base units minted
- ⚠️ Long Shot rate limit: 10 spins/minute — script handles 429 with **60s sleep** (not 10s — causes repeated 429 loop)
- 💰 Balance: ~164 RPOW (May 11, after longshot + miner running)
- See `references/rpow2-longshot.md` for full Long Shot API, odds math, and auto-spinner details

## Long Shot Gambling Feature
- URL: https://longshot.rpow2.com/
- API: `POST https://api.rpow2.com/api/longshot/spin`
- Body: `{"stake_base_units": "970000000", "odds_choice": "1:1"}`
- Same `rpow_session` cookie works for both mining API and longshot API
- Origin header must be `https://longshot.rpow2.com` for longshot endpoints
- Odds: 1:1 (47.5% win), 2:1 (31.7%), 3:1 (23.75%), 10:1 (8.6%) — 5% house edge baked in
- Rate limit: 10 spins/minute per IP
- Access check: `GET /api/longshot/access` → `{"access":"allowed"}` if on allowlist
- History: `GET /api/longshot/history?limit=100`
- Stats: `GET /api/longshot/stats`
- **No exploitable bugs** — randomness is CSPRNG `randomBytes(8)` server-side, all decisions server-side
- Auto-spinner script: `~/rpow2-miner/longshot.py` (screen -S longshot)
  - Stake: 0.97 RPOW (970000000 base units) — just under 1 RPOW
  - Odds: configurable (1:1 or 10:1), handles 429 with 60s wait
  - Auto-stop when balance > starting balance (profit mode)

### Long Shot Strategy Notes
- **1:1 odds** (47.5% win): grinds slowly, house edge bleeds balance over time. ~-5% EV per spin.
- **10:1 odds** (8.6% win): high variance, but single win = +9.7 RPOW. Better for "profit then stop" strategy.
- **Best approach**: use RPOW from free mining as bankroll. Spin 10:1, auto-stop on first win.
- **Rate limit**: 10 spins/minute per IP. Script must handle 429 with 60s sleep (not 10s — 10s causes repeated 429 loops).
- **Observed win rates** (1000 spins, 1:1): 428/1000 = 42.8% (slightly below theoretical 47.5% — house edge confirmed)
- **Long-term 1:1 result**: after 178 spins, P&L was -0.97 RPOW. Expected loss at 5% edge over 178 spins ≈ -8.6 RPOW, so variance was favorable but still net negative.

## API Instability Notes
- `api.rpow2.com` is intermittently unreachable from VPS (curl returns code 000, timeout)
- May be related to their nginx backend being overloaded
- The API worked fine initially (login, /me, /challenge all responded)
- Then became completely unresponsive (all endpoints timeout) — observed 3.5+ hour outage (May 8 23:18 → May 9 02:54)
- When API returns 504 Gateway Timeout, it's nginx-level (not Cloudflare)
- Strategy: add retry logic with exponential backoff to miner script
- **Key insight:** API can be down for hours then suddenly work perfectly — scripts MUST be persistent with auto-retry
- rpow2 `auth/request` returns `{"ok":true,"cooldown_seconds":30}` on success (HTTP 200)

## Multi-Account Strategy

### Manual Approach
- Same mining setup can run multiple accounts (different cookies)
- Store cookies in `accounts.txt` (one per line) and rotate per challenge
- Each account needs its own magic link login → cookie extraction
- When API is unreachable from VPS, user must login from PC/phone and provide cookie

### Automated Tuyul (mail.tm + rpow2 API) — PROVEN May 9, 2026
Fully automated multi-account registration using **mail.tm** REST API for temp emails:

**Why mail.tm works (and generator.email doesn't):**
- `generator.email` inbox loads via WebSocket (`socket.io`) + server-side rendering — cannot be read via simple curl/requests
- `mail.tm` has a proper REST API: create account → get token → poll inbox → read messages
- Domain rotates (was `wshu.net` on May 9, 2026) — check `GET https://api.mail.tm/domains`

**Flow (per account, ~60 seconds):**
1. `POST https://api.mail.tm/accounts` → create temp email (`{address, password}`)
2. `POST https://api.mail.tm/token` → get Bearer token for inbox access
3. `POST https://api.rpow2.com/auth/request` → request magic link (`{email}`)
4. Wait 15s, then poll `GET https://api.mail.tm/messages` (Bearer auth)
5. Find message from rpow2, extract verify link from HTML body
6. `GET https://api.rpow2.com/auth/verify?token=...` → get `rpow_session` cookie
7. Store cookie for mining

**Key API details:**
```python
# mail.tm account creation
requests.post("https://api.mail.tm/accounts", json={"address": "random@wshu.net", "password": "random16chars"})
# Returns 201 with {id, address, ...}

# mail.tm auth token
requests.post("https://api.mail.tm/token", json={"address": "...", "password": "..."})
# Returns {token: "eyJ..."}

# mail.tm inbox (with Bearer token)
requests.get("https://api.mail.tm/messages", headers={"Authorization": "Bearer TOKEN"})
# Returns {hydra:member: [{id, subject, from, ...}]}

# mail.tm full message
requests.get("https://api.mail.tm/messages/{id}", headers={"Authorization": "Bearer TOKEN"})
# Returns {html: ["<html>..."], text: "..."}
# Extract link: re.findall(r'https?://[^\s"<>]*rpow2[^\s"<>]*', html)
```

**Script location:** `~/rpow2-tuyul/tuyul_v2.py`
- Target: 20 accounts
- Auto-retry on API down (exponential backoff)
- Random delays between accounts (15-45s)
- Saves to `accounts_v2.json` with email, mail password, session cookie, status
- Run in screen: `screen -dmS rpow2-tuyul python3 ~/rpow2-tuyul/tuyul_v2.py`

**Results (May 9, 2026):**
- API was down for ~3.5 hours (23:18 - 02:54), then came back
- Once API up: 2 accounts authenticated in first 3 minutes
- Rate: ~1 account per minute when API is responsive
- rpow2 returns `{ok: true, cooldown_seconds: 30}` on successful auth request

**Pitfalls:**
- rpow2 API intermittently goes down (504 or timeout) — script must handle gracefully
- mail.tm domains change periodically — always fetch fresh from `/domains`
- Magic link tokens in rpow2 emails expire quickly (<5 min) — poll inbox immediately after request
- generator.email domains (code-gmail.com, smartnator.com, proto2mail.com) DO receive rpow2 emails but inbox is unreadable via API (WebSocket-only)
- rpow2 `auth/request` endpoint: NOT `/auth/login` or `/login` (those return 404)

## Frontend Error Messages (Diagnosis)
- `"error: try again shortly"` — API returned error (rate limit or server issue)
- `"error: Failed to fetch"` — API completely unreachable (timeout/network block)
- Button shows `[ ... ]` (disabled) — request in flight or cooldown after send

## Account Info
- Email: you@example.com (primary, cookie obtained May 8 2026, PC mining active)
- Email: user@example.com (magic link requested but token expired before verify)
- Automated accounts: 2+ via tuyul_v2.py (mail.tm temp emails @wshu.net)
- Balance: 0 (as of May 9 — PC miner actively mining)
- Minted: 0 on VPS (challenge expiry issue with Python), PC miner producing blocks (2-7s each)
