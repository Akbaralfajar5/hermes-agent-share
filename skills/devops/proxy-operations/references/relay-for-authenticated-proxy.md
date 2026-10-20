# Local no-auth relay for authenticated proxies (Chromium/CloakBrowser fix)

Fix for `ERR_PROXY_AUTH_UNSUPPORTED` with custom Chromium builds + authenticated proxies.
Verified live Sep 2026 on DataImpulse (`gw.dataimpulse.com`, both rotating 823 and sticky
10000+). Architecture:

```
Browser proxy={'server': 'http://127.0.0.1:89xx'}   ← NO username/password
   → relay subprocess (asyncio HTTP CONNECT proxy)
   → upstream PROXY:PORT with Proxy-Authorization: Basic base64(user:pass)
```

## Relay implementation pitfalls (each one was hit & fixed live)

1. **bytes vs str compare**: `method, target, _ = line.split(b" ", 2)` returns bytes.
   `if method.upper() == "CONNECT":` never matches (str compare) → CONNECT silently falls
   into the plain-HTTP forward path → upstream answers `407 NO_USER`. Compare `b"CONNECT"`.
2. **target is bytes already** — do NOT call `target.encode()` (AttributeError swallowed by
   try/except → connection silently closed → client sees "Remote end closed connection").
3. **CONNECT must chain THROUGH the upstream proxy**, never open a direct socket to the
   target. A direct-connect relay "works" for connectivity (VPS reaches target directly) but
   bypasses the proxy entirely → traffic exits the local machine's IP. Easy to miss — check
   the exit IP (`api.ipify.org`) actually matches the proxy pool, not the machine.
4. Forward leftover bytes both ways after the CONNECT handshake: `rest` = client bytes read
   past `\r\n\r\n` (pipelined TLS ClientHello) → send to upstream; `leftover` = upstream
   bytes past its `200 OK` → send to client. Dropping either kills the tunnel.
5. Python string-surgery trap: building the relay source as a `'''…'''` replacement string in
   a patch script mangles `\r\n` escapes inside it (`b"\r\n\r\n"` becomes literal newlines →
   `SyntaxError: unterminated string literal`). Copy known-good embedded code by RAW TEXT
   slicing between markers, never through Python string-literal processing.

## Known-good relay core (asyncio, Python 3.8+)

```python
import asyncio, base64, sys
LISTEN = ("127.0.0.1", int(sys.argv[1]))
UH, UP, UU, UPW = sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
AH = "Proxy-Authorization: Basic " + base64.b64encode(f"{UU}:{UPW}".encode()).decode()

async def pipe(r, w):
    try:
        while True:
            d = await r.read(65536)
            if not d: break
            w.write(d); await w.drain()
    except Exception: pass
    finally:
        try: w.close()
        except Exception: pass

async def handle(reader, writer):
    try:
        data = b""
        while b"\r\n\r\n" not in data:
            c = await reader.read(4096)
            if not c: return
            data += c
            if len(data) > 65536: return
        head, _, rest = data.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        if not lines: return
        method, target, _ = lines[0].split(b" ", 2)
        # ALWAYS connect to upstream proxy first — never direct to target
        try: ur, uw = await asyncio.open_connection(UH, UP)
        except Exception:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n"); await writer.drain(); return
        if method.upper() == b"CONNECT":
            uw.write(b"CONNECT " + target + b" HTTP/1.1\r\nHost: " + target +
                     b"\r\n" + AH.encode() + b"\r\n\r\n")
            await uw.drain()
            resp = b""
            while b"\r\n\r\n" not in resp:
                c = await ur.read(4096)
                if not c: break
                resp += c
            if b" 200" not in resp.split(b"\r\n", 1)[0]:
                writer.write(resp or b"HTTP/1.1 502 Bad Gateway\r\n\r\n"); await writer.drain()
                try: ur.close()
                except Exception: pass
                try: uw.close()
                except Exception: pass
                return
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n"); await writer.drain()
            if rest:                    # client TLS early bytes → upstream
                uw.write(rest); await uw.drain()
            leftover = resp.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in resp else b""
            if leftover:                # upstream extra bytes → client
                writer.write(leftover); await writer.drain()
            await asyncio.gather(pipe(reader, uw), pipe(ur, writer)); return
        # plain HTTP: forward absolute-URI to upstream with auth header
        nh = lines[0] + b"\r\n" + b"\r\n".join(
            l for l in lines[1:] if not l.lower().startswith(b"proxy-authorization")
        ) + b"\r\n" + AH.encode() + b"\r\n\r\n"
        uw.write(nh + rest); await uw.drain()
        await asyncio.gather(pipe(ur, writer), pipe(reader, uw))
    except Exception:
        try: writer.close()
        except Exception: pass

async def main():
    s = await asyncio.start_server(handle, LISTEN[0], LISTEN[1])
    async with s: await s.serve_forever()

asyncio.run(main())
```

## Verification sequence

1. Start relay; `curl -x http://127.0.0.1:PORT https://api.ipify.org` twice → same IP
   (sticky) and the IP belongs to the proxy pool country (NOT the local machine's IP).
2. Full browser (stock chromium headless is fine) through relay → target loads 200.
3. Test with the ACTUAL custom Chromium (CloakBrowser) on the user's machine — relay makes
   auth invisible so the custom build behaves like stock.

## Per-worker layout used in production bots

- Worker N relay local port `RELAY_BASE+N`, upstream sticky port `BASE+N`
  (DataImpulse sticky range 10000–20000). reg.py: RELAY_BASE=8900, BASE=10000.
  klaim bot: RELAY_BASE=8930, BASE=10200 (offset avoids port collisions if both run).
- Spawn: `subprocess.Popen([sys.executable, "-c", RELAY_SCRIPT, str(port), host, str(up), user, pw],
  creationflags=CREATE_NO_WINDOW if win32)`. Stop: terminate → wait(3) → kill → poll local
  port closed before returning.

## Sibling isolation layer: device fingerprints (same per-worker split)

Sticky IP per worker fixes IP rotation; identical fingerprints across concurrent workers are
an independent detectable pattern. Rules verified building 10-worker registration/deposit
bots:

- **Pool ≥ worker count.** 10 workers + 8-device pool → workers 9–10 repeat; the isolation
  silently fails. 32 realistic Android profiles used in production (Pixel/Galaxy/
  Xiaomi-POCO/Redmi/Oppo/Vivo/Realme/ASUS/Infinix/Tecno/Nokia).
- **Shuffle assignment per run**, never `worker_id % pool` (worker 1 always Pixel = pattern):
  `_order = list(range(len(DEVICES))); random.shuffle(_order)` at import, then take
  `DEVICES[_order[(wid-1) % len]]`. Unique within a run, composition changes every run.
- **Profile = UA + viewport + deviceScaleFactor + WebGL `UNMASKED_VENDOR/RENDERER`**,
  internally consistent (Mali-class models must not report Qualcomm/Adreno).
- **WebGL override without editing the big stealth string**: second
  `context.add_init_script(webgl_override_js(vendor, renderer))` after the main stealth —
  later defineProperty wins.
- Honest limits: IP reputation, mid-session rotation, registration velocity, and phone
  patterns are detected independently; distinct fingerprints + sticky IPs raise the bar,
  they don't make a farm invisible.
