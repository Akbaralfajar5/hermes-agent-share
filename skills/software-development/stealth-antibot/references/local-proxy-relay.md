# Local Proxy Relay — Bypass Chromium Proxy Auth Limitation

## Problem

`ERR_PROXY_AUTH_UNSUPPORTED` in Chromium/Playwright when using a proxy that requires username:password authentication. This happens because Chromium's network stack rejects certain proxy auth schemes or the proxy's `Proxy-Authenticate` response format.

**This is NOT the same as `407 Proxy Authentication Required`** (bad credentials). `ERR_PROXY_AUTH_UNSUPPORTED` means Chrome flat-out refuses to handle the auth at all.

## Solution: Local Relay Proxy

Run a tiny HTTP proxy on `localhost:PORT` that adds the auth header and forwards to the real proxy. Chrome connects to localhost with NO auth → relay adds the credentials.

## Implementation (Python + asyncio)

```python
#!/usr/bin/env python3
"""Local proxy relay — forwards to upstream proxy with Basic auth."""
import asyncio
import base64

UPSTREAM_HOST = "gw.dataimpulse.com"     # Real proxy host
UPSTREAM_PORT = 824                       # Real proxy port
UPSTREAM_AUTH=***"user:pass").encode()).decode()  # Pre-encoded
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 9876                        # Pick any free port

async def proxy_handler(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(8192), timeout=10)
        if not data:
            return
        first_line = data.split(b"\r\n")[0].decode(errors="replace")
        is_connect = first_line.startswith("CONNECT")

        if is_connect:
            # HTTPS tunnel
            host_port = first_line.split(" ")[1]
            up_r, up_w = await asyncio.wait_for(
                asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10
            )
            # Send CONNECT + auth to upstream
            up_w.write(
                f"CONNECT {host_port} HTTP/1.1\r\n"
                f"Host: {host_port}\r\n"
                f"Proxy-Authorization: Basic {UPSTREAM_AUTH}\r\n\r\n"
            ).encode())
            await up_w.drain()
            up_resp = await asyncio.wait_for(up_r.read(4096), timeout=10)
            if b"200" not in up_resp.split(b"\r\n")[0]:
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain(); up_w.close(); writer.close(); return
            writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await writer.drain()
            await asyncio.gather(_relay(up_r, writer), _relay(reader, up_w))
            up_w.close()
        else:
            # HTTP direct
            up_r, up_w = await asyncio.wait_for(
                asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10
            )
            lines = data.split(b"\r\n")
            lines.insert(1, f"Proxy-Authorization: Basic {UPSTREAM_AUTH}\r\n".encode())
            up_w.write(b"\r\n".join(lines))
            await up_w.drain()
            while True:
                chunk = await asyncio.wait_for(up_r.read(65536), timeout=30)
                if not chunk: break
                writer.write(chunk); await writer.drain()
            up_w.close()
    except: pass
    finally:
        try: writer.close()
        except: pass

async def _relay(src, dst):
    try:
        while True:
            data = await asyncio.wait_for(src.read(65536), timeout=300)
            if not data: break
            dst.write(data); await dst.drain()
    except: pass

async def main():
    server = await asyncio.start_server(proxy_handler, LOCAL_HOST, LOCAL_PORT)
    print(f"[relay] Listening on {LOCAL_HOST}:{LOCAL_PORT}", flush=True)
    async with server: await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
```

## Usage in Playwright

```python
# Launch relay as subprocess BEFORE starting browsers
import subprocess
subprocess.Popen([sys.executable, "relay_proxy.py"],
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
await asyncio.sleep(1)

# In Playwright — no auth needed, relay handles it
context = await browser.new_context(
    proxy={'server': 'http://127.0.0.1:9876'},
    # NO username/password
)
```

## Auto-start (check if already running)

```python
def ensure_relay(relay_script, port=9876):
    import socket
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(('127.0.0.1', port))
        s.close()
        return  # Already running
    except: pass
    finally:
        try: s.close()
        except: pass
    subprocess.Popen([sys.executable, relay_script],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

## DataImpulse Port Reference

| Port | Mode | Use Case |
|------|------|----------|
| 823 | Sticky/rotation | Same IP for session, rotates on reconnect |
| 824 | Full rotation | New IP every request |
| 825 | Sticky + region | Sticky IP filtered by country |
