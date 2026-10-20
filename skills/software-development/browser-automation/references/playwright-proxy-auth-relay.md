# Playwright Proxy Authentication - ERR_PROXY_AUTH_UNSUPPORTED Fix

## Problem

Chromium/Playwright raises `net::ERR_PROXY_AUTH_UNSUPPORTED` when using HTTP proxies that require authentication (username/password). This happens with residential proxy providers like DataImpulse, BrightData, Oxylabs, etc.

**The error persists even with:**
- `browser.new_context(proxy={'server': 'http://host:port', 'username': '...', 'password': '...'})`
- `--proxy-server` CLI flag + credentials in context
- Both `http://` and `https://` proxy schemes

## Root Cause

Chromium's internal proxy stack has inconsistent support for `Proxy-Authorization` headers. Some proxy implementations (especially residential rotating proxies) send non-standard `Proxy-Authenticate` challenges that Chrome rejects at the network layer before Playwright can handle them.

**Note:** The proxy scheme MUST be `http://` not `https://` — DataImpulse et al. are HTTP proxies. Using `https://` scheme guarantees `ERR_PROXY_AUTH_UNSUPPORTED`.

## Solution: Local Auth Relay Proxy

Run a tiny proxy on `localhost` that handles the upstream authentication, so Chromium connects to a proxy without auth.

### Architecture

```
Chromium → localhost:9876 (no auth) → relay_proxy.py → DataImpulse:823/824 (with auth)
```

### DataImpulse Port Options

| Port | Behavior | Use Case |
|------|----------|----------|
| 823 | Sticky IP (same IP per session) | Default, predictable |
| 824 | **Rotating IP** (changes per request) | Avoid blacklisting, bypass rate limits |
| 825 | Sticky + region-specific | Location targeting |

Switch port 823 → 824 when websites start blocking after repeated use. The relay handles both transparently — just change `UPSTREAM_PORT` in the config.

### relay_proxy.py Implementation

A Python asyncio forward proxy that:
1. Listens on `127.0.0.1:PORT` - no authentication required
2. Handles **CONNECT** (HTTPS) - opens tunnel to upstream proxy, sends CONNECT with Proxy-Authorization header
3. Handles **HTTP** - injects Proxy-Authorization header into request
4. Bidirectional relay - streams data both ways

Full script at `scripts/relay_proxy.py` in this skill (or recreate with pattern below).

### Integration with Playwright

Two files needed in the same directory:

**relay_proxy.py:**
```python
#!/usr/bin/env python3
import asyncio, base64, sys

UPSTREAM_HOST = "gw.dataimpulse.com"
UPSTREAM_PORT = 824  # 823=sticky, 824=rotating
UPSTREAM_AUTH = base64.b64encode(b"user:pass").decode()
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 9876

async def proxy_handler(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(8192), timeout=10)
        if not data: return
        first = data.split(b"\r\n")[0].decode(errors="replace")
        is_connect = first.startswith("CONNECT")
        if is_connect:
            hp = first.split(" ")[1]
            r,w = await asyncio.wait_for(asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10)
            w.write(f"CONNECT {hp} HTTP/1.1\r\nHost: {hp}\r\nProxy-Authorization: Basic {UPSTREAM_AUTH}\r\nProxy-Connection: keep-alive\r\n\r\n".encode()); await w.drain()
            if b"200" not in (await asyncio.wait_for(r.read(4096), timeout=10)).split(b"\r\n")[0]:
                writer.write(b"HTTP/1.1 502\r\n\r\n"); await writer.drain(); w.close(); writer.close(); return
            writer.write(b"HTTP/1.1 200\r\n\r\n"); await writer.drain()
            await asyncio.gather(_relay(r,writer), _relay(reader,w)); w.close()
        else:
            r,w = await asyncio.wait_for(asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10)
            lines = data.split(b"\r\n"); lines.insert(1, f"Proxy-Authorization: Basic {UPSTREAM_AUTH}\r\n".encode())
            w.write(b"\r\n".join(lines)); await w.drain()
            while True:
                c = await asyncio.wait_for(r.read(65536), timeout=30)
                if not c: break; writer.write(c); await writer.drain()
            w.close()
    except: pass
    finally:
        try: writer.close()
        except: pass

async def _relay(s,d):
    try:
        while True:
            c = await asyncio.wait_for(s.read(65536), timeout=300)
            if not c: break; d.write(c); await d.drain()
    except: pass

async def main():
    s = await asyncio.start_server(proxy_handler, LOCAL_HOST, LOCAL_PORT)
    print(f"[relay] {LOCAL_HOST}:{LOCAL_PORT} → {UPSTREAM_HOST}:{UPSTREAM_PORT}")
    async with s: await s.serve_forever()
asyncio.run(main())
```

**In the Playwright script (reg.py / klaim.py / any automation script):**
```python
import os, subprocess, socket, sys

RELAY_SCRIPT = os.path.join(os.path.dirname(__file__), "relay_proxy.py")
RELAY_PORT = 9876

def ensure_relay():
    """Start relay if not already running. Safe to call multiple times."""
    s = socket.socket(); s.settimeout(1)
    try:
        s.connect(("127.0.0.1", RELAY_PORT)); s.close()
        return  # Already running
    except: pass
    finally:
        try: s.close()
        except: pass
    subprocess.Popen([sys.executable, RELAY_SCRIPT],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Call once before launching browsers
ensure_relay()

# Then use in browser context or launch — NO auth credentials
proxy_config = {"server": f"http://127.0.0.1:{RELAY_PORT}"}

# For context-level proxy:
context = await browser.new_context(proxy=proxy_config)

# For browser-level proxy (launch args):
browser = await playwright.chromium.launch(proxy=proxy_config, ...)
```

### Key Points

- **Only ONE relay process** needed — handles all workers/browsers
- **Auto-start**: `ensure_relay()` checks if port is up before starting
- **No auth in Playwright**: Chromium connects to localhost without credentials
- **Both proxy levels**: Works with `browser.new_context(proxy=...)` AND `browser.launch(proxy=...)`
- **Same relay for all scripts**: reg.py, klaim.py, deposit.py can share one relay.py

### Pitfalls

1. **Port mismatch**: If you change `LOCAL_PORT` in relay_proxy.py, you MUST update BOTH the port in the relay AND `RELAY_PORT` in the script + `proxy_config` server URL. A mismatch causes cryptic connection refused errors.
2. **Two copies of relay**: If `reg.py` already started relay on port 9876, then `klaim.py` calls `ensure_relay()` — the socket check detects port 9876 is occupied and skips starting another. Safe by design.
3. **Firewall/antivirus**: Some Windows AV blocks local proxy servers. Add `127.0.0.1:9876` to the exclusion list.
4. **Kill leftover relay**: If relay crashes, port stays occupied. Use `netstat -ano | findstr :9876` then `taskkill /PID <pid> /F` on Windows, or `kill $(lsof -ti:9876)` on Linux.
5. **Relay must be started BEFORE browser launch**: Call `ensure_relay()` early in the worker function, not after `page.goto()`.
6. **PORT ISOLATION**: Keep the default relay port (9876) unique per user/project. If two users run on the same machine with conflicting ports, relays will fight for the port.

## When to use

- ERR_PROXY_AUTH_UNSUPPORTED persists after changing scheme to http://
- Any authenticated HTTP proxy with residential IP providers
- Chromium on Windows or Linux — both affected
- Need IP rotation via DataImpulse port 824

## Limitations

- Adds ~2-5ms latency per request (local loopback)
- Only Basic auth supported (not NTLM/Digest)
- One relay handles all workers (shared upstream proxy)
