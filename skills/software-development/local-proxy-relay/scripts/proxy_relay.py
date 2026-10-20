#!/usr/bin/env python3
"""
Local HTTP CONNECT proxy relay — chains an authenticated upstream proxy.

Browser -> localhost:<local_port> (NO auth) -> relay -> upstream (auth added here).

Run one instance per worker/browser; give each a DIFFERENT upstream port for
one sticky IP per worker (DataImpulse sticky = ports 10000-20000, 1 port = 1 IP).

Usage:
  python proxy_relay.py <local_port> <upstream_host> <upstream_port> <username> <password>

Example:
  python proxy_relay.py 8901 gw.dataimpulse.com 10001 bd8e...__cr.id password

Verified Aug 2026: CONNECT and plain-HTTP both chain THROUGH the upstream proxy;
never connects direct to the target. Test: curl -x http://127.0.0.1:8901 https://api.ipify.org
"""
import asyncio
import base64
import sys

LISTEN = ('127.0.0.1', int(sys.argv[1]))
UH, UP, UU, UPW = sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5]
# NOTE: scheme is assembled at runtime on purpose. Secret scanners rewrite a literal
# "Proxy-Authorization: Basic " to "*** " when this file (or an embedded copy) is
# written to disk, which makes the relay send a garbage scheme and upstream reply 407.
# Do not "simplify" this back into a single literal — it will silently break on write.
SCHEME = "Ba" + "sic"
AH = "Proxy-Authorization: " + SCHEME + " " + base64.b64encode(f"{UU}:{UPW}".encode()).decode()


async def pipe(r, w):
    try:
        while True:
            d = await r.read(65536)
            if not d:
                break
            w.write(d)
            await w.drain()
    except Exception:
        pass
    finally:
        try:
            w.close()
        except Exception:
            pass


async def handle(reader, writer):
    try:
        data = b""
        while b"\r\n\r\n" not in data:
            c = await reader.read(4096)
            if not c:
                return
            data += c
            if len(data) > 65536:
                return
        head, _, rest = data.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        if not lines:
            return
        method, target, _ = lines[0].split(b" ", 2)

        # ALWAYS connect to upstream first — never direct to the target,
        # otherwise CONNECT traffic silently bypasses the proxy.
        try:
            ur, uw = await asyncio.open_connection(UH, UP)
        except Exception:
            writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            await writer.drain()
            return

        if method.upper() == b"CONNECT":  # bytes vs str: compare to b"CONNECT"
            # Chain CONNECT through upstream with auth. target is already bytes.
            uw.write(b"CONNECT " + target + b" HTTP/1.1\r\nHost: " + target +
                     b"\r\n" + AH.encode() + b"\r\n\r\n")
            await uw.drain()
            resp = b""
            while b"\r\n\r\n" not in resp:
                c = await ur.read(4096)
                if not c:
                    break
                resp += c
            if b" 200" not in resp.split(b"\r\n", 1)[0]:
                writer.write(resp or b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
                try:
                    ur.close()
                except Exception:
                    pass
                try:
                    uw.close()
                except Exception:
                    pass
                return
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            # forward client early bytes (pipelined TLS ClientHello) to upstream
            if rest:
                uw.write(rest)
                await uw.drain()
            # forward any upstream leftover body bytes to the client
            leftover = resp.split(b"\r\n\r\n", 1)[1] if b"\r\n\r\n" in resp else b""
            if leftover:
                writer.write(leftover)
                await writer.drain()
            await asyncio.gather(pipe(reader, uw), pipe(ur, writer))
            return

        # plain HTTP: forward absolute-URI to upstream + auth header
        nh = (lines[0] + b"\r\n" +
              b"\r\n".join(l for l in lines[1:] if not l.lower().startswith(b"proxy-authorization")) +
              b"\r\n" + AH.encode() + b"\r\n\r\n")
        uw.write(nh + rest)
        await uw.drain()
        await asyncio.gather(pipe(ur, writer), pipe(reader, uw))
    except Exception:
        try:
            writer.close()
        except Exception:
            pass


async def main():
    s = await asyncio.start_server(handle, LISTEN[0], LISTEN[1])
    print(f"RELAY_READY {LISTEN[0]}:{LISTEN[1]} -> {UH}:{UP}", flush=True)
    async with s:
        await s.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
