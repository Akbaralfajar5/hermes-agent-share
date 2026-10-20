---
name: proxy-operations
description: >
  Diagnose proxy connectivity for proxied browsers/bots.
---

# Proxy Operations & Connectivity Diagnosis

Recurring class for this user: proxied registration/deposit bots (example-target), CloakBrowser
workers, DataImpulse rotating proxies, web scrapers. When asked "cek proxy ini masih aktif
ga" or "kenapa tidak terhubung ke target", follow the ladder — do NOT trust the symptom; a
proxy that "can't reach target Y" is usually healthy and the failure is elsewhere.

## DataImpulse-specific facts (durable)

- Gateway: `gw.dataimpulse.com`. Port **823 = HTTP** (rotating bare, sticky with a
  `;sessid.<id>` param). Port **824 = SOCKS5** — Chromium/Playwright do NOT support
  SOCKS5 + auth → never use 824 at browser launch.
- **Sticky works TWO ways — port-based AND username-param. Do not tell the user "823 is
  rotating only".** The operator's claim *"udah pakai 823 aja, itu udah sticky kok"* is
  **CORRECT** — a corrected earlier version of this note was wrong and cost a debugging arc.
  | Mode | How | IP behaviour |
  |---|---|---|
  | Rotating | port **823**, no session param | changes every request |
  | Sticky (port) | ports **10000–20000** | IP bound to the PORT, 1–120 min (default 30) |
  | Sticky (param) | port **823** + `;sessid.<id>` | IP bound to the session id, ~30 min |
- **`sessid` suffix format — delimiter is a SEMICOLON, not a dot/underscore/hyphen**:
  `login__cr.id;sessid.1` (combine with country via `__cr.de;sessid.123`). Docs:
  `https://docs.dataimpulse.com/proxies/parameters/session-id.md` (append `.md` to any doc
  URL for markdown; full index at `https://docs.dataimpulse.com/llms.txt`).
- ⚠️ **Wrong-format suffixes FAIL SILENTLY as HTTP 000 / 407**, so a bad guess looks like
  "the account doesn't support sessions" — a **false conclusion**. Verified bad:
  `__cr.id.1`, `__cr.id-1`, `__cr.id.wid1` → all HTTP 000. Verified good:
  `__cr.id;sessid.1` → HTTP 200. **When a guessed format fails, read the provider docs
  before concluding the feature is unsupported.**
- **Per-worker IP on plain 823** — `<USER>;sessid.<wid>` gives each worker its own sticky IP
  without touching ports. Verified 4/4 distinct Indonesian IPs (`sessid.1` Bandar Seri
  Bentan, `.2` Jakarta, `.3` Makassar, `.4` Jakarta); `sessid.1` × 3 requests = same IP
  (genuinely sticky). Prefer this over 10000–20000 when the port-based sticky cap is unknown
  or small — it sidesteps the per-account cap problem.
- Credentials identical on every port. Port 823 accepts BOTH `http://` and `https://`
  schemes in curl/Playwright.
- `sessid` is the ONLY username param allowed in this format — but it composes with country
  using dots+semicolons (`__cr.de;sessid.123` = Germany + sticky).
- Username format: `{session_id}__cr.{cc}` — e.g. `bd8e6258848d97b0f51d__cr.id`.
  `cr` = country rotation; **NOT geo-strict**. The `__cr.id` pool mostly exits Indonesia but
  intermittently exits Brazil (`177.54.x`), Hong Kong (`158.140.x`), etc. Geo-sensitive
  targets intermittently reject → retry, don't swap credentials.
- Port 823 accepts BOTH `http://` and `https://` proxy schemes in curl/Playwright.

## Diagnosis ladder

### 1. Liveness — test BOTH schemes
```bash
curl -sS --max-time 25 -x 'http://USER:PASS@gw.dataimpulse.com:823' 'https://api.ipify.org?format=json' -w '\nHTTP:%{http_code} time:%{time_total}s\n'
curl -sS --max-time 25 -x 'https://USER:PASS@gw.dataimpulse.com:823' 'https://api.ipify.org?format=json' -w '\nHTTP:%{http_code} time:%{time_total}s\n'
```
200 + JSON IP = alive. One slow response (6s+) = gateway load, not death.

### 2. Rotating-pool geo consistency
Fire 5 consecutive ipify calls, list exit IPs, compare to expected country. Establishes
whether a geo-blocked target fails intermittently by design.

### 3. Target reachability — status code is NOT enough
curl the actual target through the proxy with a realistic UA, then inspect the body:
- Real page HTML (correct `<title>`, app markup) → proxy reaches target fine.
- Cloudflare / "Just a moment" / 403 shell → proxy IPs flagged at the edge.
- A target behind Cloudflare can return 200 to curl (plain HTML) while a full browser still
  hits an interstitial — grep body content, not just the code.

### 4. Reproduce with the EXACT failing config (decisive step)
If the report is "bot can't connect", run a minimal Playwright script mirroring the bot:
same proxy dict (scheme + creds), same mobile UA/device emulation, `goto(target)`, report
status/title/page length. Playwright chromium headless-shell install: `python3 -m playwright
install chromium` (~115 MB; delete `~/.cache/ms-playwright` after to keep VPS disk clean).

### 5. Verdict — isolate server vs local machine
- Proxy works from server AND full browser loads target → proxy is healthy. A bot failing on
  the user's Windows PC points LOCAL: (a) ISP blocking/throttling the proxy gateway
  (`gw.dataimpulse.com` is filtered by some Indonesian ISPs), (b) CloakBrowser executable
  path/version changed (`~/.cloakbrowser/chromium-<ver>/chrome.exe`), (c) **custom Chromium
  build breaks Playwright proxy-auth injection → `ERR_PROXY_AUTH_UNSUPPORTED`** (see below —
  NOT fixed by switching http:// ↔ https://; fix is a local no-auth relay).
- 407 = credentials wrong/expired, OR a relay/bot bug where the CONNECT request never carried
  auth (see relay pitfalls below). Connection refused = gateway down. Timeout on every
  request from one network = ISP/gateway filter → test from another network.
- **Before re-debugging launch args, check for a STALE RELAY holding the port.** Verified
  Oct 2026: a relay orphaned since a *previous month* sat on the bot's default local port
  with (a) an exhausted account and (b) a redacted `Proxy-Authorization: ***` header, while
  the new relay was never launched because `start()` short-circuited on
  `if self._port_open(): return`. Every launch arg was correct, so the whole cascade read as
  "the proxy flags don't work". **A `_port_open() → True` must never be trusted as "my relay
  is up".** Attribute the zombie by its argv, which still shows the old upstream user:
  ```bash
  ss -tlnp | grep ': <local_port> '        # get the pid holding the port
  ps aux | grep "_relay_\|asyncio, base64" # shows stale upstream user + mangled header
  pkill -9 -f "asyncio, base64, sys"       # matches relay argv, NOT your shell
  ```
  Kill **by port** (`fuser -k <port>/tcp`) or by that specific pattern — a generic
  `pkill -f python` can kill your own shell.

## Custom-Chromium proxy auth failure (ERR_PROXY_AUTH_UNSUPPORTED)

**Symptom:** CloakBrowser / patched Chromium + authenticated proxy at Playwright launch →
`net::ERR_PROXY_AUTH_UNSUPPORTED` on `page.goto`, while the SAME code with stock bundled
Chromium returns 200. Curl through the same proxy also works — curl does its own auth; this
is a Chromium-network-stack issue, not a credential issue.

**Not the cause:** proxy scheme. CloakBrowser fails with BOTH `http://` and `https://`
schemes. Do not burn time flipping the scheme.

**Working fix — local no-auth relay (works with any Chromium build):**
```
Browser → http://127.0.0.1:89xx   (proxy dict WITHOUT username/password)
        → relay subprocess (asyncio HTTP CONNECT proxy; adds Proxy-Authorization: Basic)
        → gw.dataimpulse.com:PORT
```
Browser never sees a 407, so Playwright's auth handler is never needed. Relay spawn per
worker: `subprocess.Popen([sys.executable, "-c", RELAY_SCRIPT, local_port, host, up_port,
user, pass])`, `CREATE_NO_WINDOW` on win32; kill on exit. Full script + pitfalls:
`references/relay-for-authenticated-proxy.md`.

## Pitfalls
- Testing only ipify proves the gateway, not target reachability — always test the real
  target.
- Don't rotate proxy credentials on a "can't connect" report until the ladder shows the
  gateway itself failing.
- Vision tools may be unavailable (401) on this setup — proxy/browser diagnostics must rely
  on status + body text + computed data, not screenshots.
