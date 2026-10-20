# Fresh Install Patches (2026-05-12)

When cloning fresh from `https://github.com/yunus-0x/charon`, apply these modifications in order. All patches assume working directory is the repo root.

## Prerequisites
- Node.js v20+
- Python 3 with `curl_cffi` installed
- Residential proxy credentials (DataImpulse or equivalent)
- PM2 globally installed

## 1. Install & .env

```bash
git clone https://github.com/yunus-0x/charon && cd charon && npm install
```

Create `.env` with all required vars (see main skill doc).

## 2. Patches (in order)

### 2a. src/config.js
- Change `POSITION_CHECK_MS` default from 10000 to 5000
- Change GMGN validation to accept `GMGN_BRIDGE_URL` as alternative to `GMGN_API_KEY`

### 2b. src/enrichment/gmgn.js
- Remove `GMGN_API_KEY` from import
- Add `BRIDGE_BASE` constant from env
- Replace `openapi.gmgn.ai` URL with `${BRIDGE_BASE}${pathname}`
- Remove `X-APIKEY` header
- Remove `timestamp` and `client_id` params (bridge doesn't need them)
- Add response validation: `payload.code === 0 || payload.message === 'success' || payload.data`
- Add 502 bridge error handling
- Add 502 to backoff status codes

### 2c. src/db/connection.js
- Change default strategy_id column from 'sniper' to 'profit_lock'
- Replace sniper seed strategy with profit_lock (full config with tiers)

### 2d. src/db/settings.js
- Change fallback `strategyById('sniper')` → `strategyById('profit_lock')`
- Replace `defaultStrategy()` return with profit_lock config

### 2e. src/db/positions.js
- Change TP calculation: `strat.profit_lock_tiers?.length ? 9999 : Number(...)` (both createDryRunPosition and createLivePosition)

### 2f. src/execution/positions.js
- Add `const profitLockTimers = new Map();` after imports
- Add profit lock logic block between MAX_HOLD check and Partial TP check

### 2g. src/pipeline/orchestrator.js
- Add `setting` to imports from `'../db/settings.js'`
- Add `if (setting('bot_paused') === 'true') return;` at top of `processCandidateFromSignals()`

### 2h. src/pipeline/llm.js
- Replace English system prompt with Indonesian strict-timing version
- Replace task instruction with Indonesian version
- Change output_schema reason/risks to "string dalam Bahasa Indonesia"

### 2i. src/pipeline/candidateBuilder.js
- Add hard filters between Anti-ATH block and Trending filters:
  - Dead token: `vol1h === 0 && dexAgeMs > 600000`
  - Parabolic pump: `priceChange5m > 100`
  - topBlastRisk: `chart?.topBlastRisk === true`

### 2j. src/telegram/commands.js
- Add `fmtUsd` to format.js import
- Add `/stop` and `/start` command routing (before `/positions`)
- Change valid strategies from `['sniper', ...]` to `['profit_lock', ...]`
- Replace `sendPositions()` with compact version (open + recent closed, 1-line each)
- Add `stopBot()` and `startBot()` functions
- Replace `sendPnl()` with DB-based dry run stats version (export it)

### 2k. src/telegram/callbacks.js
- Change `import('./send.js')` to `import('./commands.js')` for sendPnl

### 2l. src/telegram/menus.js (optional, for menu callback)
- Add `import { db } from '../db/connection.js';`
- Replace `positionsText()` with compact DB query version

### 2m. Delete src/enrichment/dexscreener.js
- Remove file entirely (GMGN covers all data)

## 3. Create gmgn_bridge.py

```python
"""GMGN Bridge — proxies to gmgn.ai via residential proxy + TLS spoofing."""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from curl_cffi import requests as cffi_requests

PROXY = "http://<user>:<pass>@gw.dataimpulse.com:823"
BASE = "https://gmgn.ai"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        target = f"{BASE}{parsed.path}"
        if parsed.query:
            target += f"?{parsed.query}"
        try:
            r = cffi_requests.get(target, impersonate="chrome", proxies={"http": PROXY, "https": PROXY}, timeout=15)
            self.send_response(r.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(r.content)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9876), Handler)
    print("[gmgn-bridge] listening on :9876")
    server.serve_forever()
```

## 4. Start

```bash
pm2 start gmgn_bridge.py --name gmgn-bridge --interpreter python3
pm2 start index.js --name charon
pm2 save
```

## 5. Verify

```bash
# Bridge health
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9876/defi/quotation/v1/rank/sol/swaps/1h?limit=1
# Should return 200

# Bot running
pm2 logs charon --lines 10 --nostream
# Should show [server] or [bot] started messages

# Syntax check all modified files
node --check index.js && node --check src/app.js && node --check src/config.js && \
node --check src/pipeline/orchestrator.js && node --check src/pipeline/candidateBuilder.js && \
node --check src/pipeline/llm.js && node --check src/telegram/commands.js && \
node --check src/telegram/callbacks.js && node --check src/telegram/menus.js && \
node --check src/execution/positions.js && node --check src/db/connection.js && \
node --check src/db/settings.js && node --check src/db/positions.js
```

## Known Issues

- **Proxy 407 error:** DataImpulse credentials expire. When bridge returns 502 with "CONNECT tunnel failed, response 407", proxy credentials need renewal. Bot still runs but GMGN enrichment fails — falls back to Jupiter-only data.
- **PM2 entry point:** MUST be `index.js`, NOT `src/app.js`. The latter exports `startCharon()` but never calls it.
- **Telegram 409 conflict:** After killing old process, new instance may show polling conflict for ~30s. This resolves automatically.
- **Hard filters disappearing:** After patching `candidateBuilder.js`, always verify with `grep -n "dead token\|parabolic\|topBlastRisk" src/pipeline/candidateBuilder.js` — must show 6 lines.
