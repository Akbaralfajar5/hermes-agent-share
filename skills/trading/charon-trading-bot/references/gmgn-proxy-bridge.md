# GMGN Proxy Bridge

Python HTTP server that proxies GMGN requests via residential proxy + TLS spoofing.
Charon's Node.js code calls `http://127.0.0.1:9876/...` instead of `gmgn.ai` directly.

## Requirements

```bash
pip install curl_cffi
```

## Bridge Script (`gmgn_bridge.py`) — v2 (2026-05-12)

**CRITICAL CHANGE:** Direct token info endpoints (`/api/v1/token_info/sol/{mint}`, `/v1/token/info`) are now fully blocked by Cloudflare (403). The bridge now routes token lookups through the rank endpoint which still works.

**How it works:**
1. Charon calls bridge at `/v1/token/info?chain=sol&address=MINT`
2. Bridge internally routes to `/defi/quotation/v1/rank/sol/swaps/1h?limit=50&token=MINT`
3. If token found in swaps rank → return full data
4. If not found → try pump rank as fallback
5. Response wrapped as `{"code":0,"data":{"data": tokenObj}}` so charon's `payload?.data?.data` parsing works

```python
#!/usr/bin/env python3
"""GMGN Bridge — proxies requests to gmgn.ai via residential proxy + TLS spoofing.

Routes /v1/token/info?chain=sol&address=MINT to the working endpoint:
/defi/quotation/v1/rank/sol/swaps/1h?limit=50&token=MINT
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from curl_cffi import requests as cffi_requests

PROXY = "http://<user>:<pass>@gw.dataimpulse.com:823"
BASE = "https://gmgn.ai"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://gmgn.ai/",
    "Origin": "https://gmgn.ai",
}

session = cffi_requests.Session(impersonate="chrome120")
session.proxies = {"http": PROXY, "https": PROXY}
session.headers = HEADERS


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        # Route /v1/token/info?chain=sol&address=MINT → rank endpoint
        if parsed.path == "/v1/token/info":
            mint = params.get("address", [None])[0]
            if not mint:
                self._json(400, {"error": "missing address param"})
                return
            self._token_info(mint)
            return

        # Fallback: proxy as-is to gmgn.ai/defi/quotation/v1/...
        target = f"{BASE}{parsed.path}"
        if parsed.query:
            target += f"?{parsed.query}"
        try:
            r = session.get(target, timeout=15)
            self.send_response(r.status_code)
            self.send_header("Content-Type", r.headers.get("content-type", "application/json"))
            self.end_headers()
            self.wfile.write(r.content)
        except Exception as e:
            self._json(502, {"error": str(e)})

    def _token_info(self, mint):
        """Fetch token data via the rank endpoint (bypasses Cloudflare)."""
        url = f"{BASE}/defi/quotation/v1/rank/sol/swaps/1h?limit=50&token={mint}"
        try:
            r = session.get(url, timeout=15)
            if r.status_code != 200:
                self._json(r.status_code, {"error": f"upstream {r.status_code}"})
                return

            payload = r.json()
            rank = payload.get("data", {}).get("rank", [])

            if rank:
                # Found in swaps rank — return first match
                token = rank[0]
                # Return as data.data so charon's `payload?.data?.data` picks it up directly
                self._json(200, {"code": 0, "msg": "success", "data": {"data": token}})
            else:
                # Token not in swaps rank — try pump rank as fallback
                url2 = f"{BASE}/defi/quotation/v1/rank/sol/pump?limit=100"
                r2 = session.get(url2, timeout=15)
                if r2.status_code == 200:
                    rank2 = r2.json().get("data", {}).get("rank", [])
                    match = next((t for t in rank2 if t.get("address") == mint), None)
                    if match:
                        self._json(200, {"code": 0, "msg": "success", "data": {"data": match}})
                        return

                # Not found in any rank — return empty (bot will skip enrichment)
                self._json(200, {"code": 0, "msg": "not_found", "data": {"data": None}})

        except Exception as e:
            self._json(502, {"error": str(e)})

    def _json(self, status, obj):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, format, *args):
        pass  # suppress logs


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9876), Handler)
    print("[gmgn-bridge] listening on :9876 (rank-based routing)")
    server.serve_forever()
```

## PM2 Setup

```bash
# Place gmgn_bridge.py in charon root
pm2 start /home/ubuntu/charon/gmgn_bridge.py --name gmgn-bridge --interpreter python3
pm2 save

# Verify token info (the main endpoint charon uses)
curl -s "http://127.0.0.1:9876/v1/token/info?chain=sol&address=HrBojR9H6CfZeV2GibKoMWQCAmCt3LqVPoL4CTaJgkK6" | python3 -m json.tool

# Verify trending (fallback path)
curl -s "http://127.0.0.1:9876/defi/quotation/v1/rank/sol/swaps/1h?limit=2" | python3 -m json.tool
```

## .env Addition

```env
GMGN_ENABLED=true
GMGN_API_KEY=bridge_mode
GMGN_BRIDGE_URL=http://127.0.0.1:9876
GMGN_REQUEST_DELAY_MS=3000
```

## Working GMGN Web Endpoints (as of 2026-05-12)

| Endpoint | Returns |
|----------|---------|
| `/defi/quotation/v1/rank/sol/swaps/{1h,5m,6h,24h}?limit=50&token={mint}` | **Single token lookup** — full data: price, market_cap, volume, holder_count, top_10_holder_rate, rug_ratio, bundler_rate, is_wash_trading, sniper_count, smart_degen_count, entrapment_ratio, creator_token_status, liquidity, etc. |
| `/defi/quotation/v1/rank/sol/swaps/{1h,5m,6h,24h}?orderby=marketcap&direction=desc&limit=100` | Trending tokens ranked by metric |
| `/defi/quotation/v1/rank/sol/pump?limit=100` | Pump.fun tokens (pre-graduation) |

## Endpoints That DON'T Work (as of 2026-05-12)

- `/api/v1/sol/token/{mint}` → 403 Cloudflare
- `/api/v1/token_info/sol/{mint}` → 403 Cloudflare
- `/v1/token/info?chain=sol&address={mint}` → 403 Cloudflare (old openapi path)
- `openapi.gmgn.ai/v1/token/info` → 401 (requires paid API key)
- `/defi/quotation/v1/tokens/sol/{mint}` → 200 but `{"code":40000300,"msg":"invalid argument"}`
- `/defi/quotation/v1/token/sol/{mint}/security` → 404
- `/defi/quotation/v1/token/sol/{mint}/info` → 404
- `/defi/quotation/v1/tokens/top_buyers/sol/{mint}` → untested, may still work

## Token Lookup Limitations

The rank-based approach has one limitation: **if a token is not actively traded in the last 1h (not in any rank), the lookup returns null.** This means:
- Very new tokens (< 5 min old) may not appear in ranks yet
- Dead/abandoned tokens with 0 recent volume won't be found
- This is actually a FEATURE — tokens not in any rank are likely dead/illiquid anyway

When bridge returns `{"data":{"data":null}}`, charon's `fetchGmgnTokenInfo()` returns null, and the pipeline falls through to Jupiter-only enrichment (price, mcap, holders from Jupiter API). The token can still be traded — just with less safety data.

## Proxy Providers Tested

- **DataImpulse** (`gw.dataimpulse.com:823`) — works, residential rotating, pay-per-GB
  - Format: `http://<user>:<pass>@gw.dataimpulse.com:823`
  - Credentials can expire without warning (407 error)
  - When expired: bridge returns 502, bot continues with Jupiter-only data
- Standard datacenter proxies → blocked (same ASN issue as VPS)
- Free proxy lists → unreliable, mostly blocked

## Key Architecture Notes

- Bridge MUST run on same machine as Charon (localhost only)
- Node.js `fetch`/`axios` cannot bypass Cloudflare even with proxy (TLS fingerprint)
- Python `curl_cffi` with `impersonate='chrome120'` spoofs Chrome's TLS fingerprint
- Residential proxy provides clean IP that Cloudflare doesn't block at ASN level
- Both are required together — either alone still gets 403
- Using `cffi_requests.Session()` (persistent session) is important — reuses cookies/connections
- The `?token=MINT` query param on rank endpoints acts as a server-side filter
- GMGN may occasionally return Cloudflare challenge even with proxy — the backoff logic in `gmgn.js` handles this gracefully (30min cooldown)

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Bridge returns 502 + "CONNECT tunnel failed, response 407" | Proxy credentials expired | Get new credentials from DataImpulse, update PROXY in bridge, `pm2 restart gmgn-bridge` |
| Bridge returns 200 but HTML content | Cloudflare challenge triggered | Try different `impersonate` value (chrome120, chrome116, safari17_0), or wait 30min |
| Bridge returns `{"code":0,"data":{"data":null}}` | Token not in any rank (not actively traded) | Normal — bot falls through to Jupiter enrichment |
| Charon logs `[gmgn] XXXXXXXX... 502` | Bridge is down or erroring | Check `pm2 logs gmgn-bridge`, restart if needed |
| `marketCapFromGmgn()` returns null despite bridge working | Response wrapped wrong (data.token instead of data.data) | Fix bridge to return `{"data":{"data": tokenObj}}` not `{"data":{"token": tokenObj}}` |
