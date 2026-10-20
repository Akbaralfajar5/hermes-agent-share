#!/usr/bin/env python3
"""
Local proxy relay — listens on localhost:9876 (no auth), forwards
to DataImpulse with Basic auth. Chromium/Playwright hates proxy
auth, this bypasses ERR_PROXY_AUTH_UNSUPPORTED entirely.

Usage:
    python relay_proxy.py

Or auto-start via ensure_relay() in your Playwright script.

Config (edit these):
    UPSTREAM_HOST  — DataImpulse gateway
    UPSTREAM_PORT  — 823 (sticky) | 824 (rotating IP) | 825 (region)
    UPSTREAM_AUTH  — base64("user:pass")
    LOCAL_PORT     — port to listen on (default 9876)
"""
import asyncio
import base64
import sys

# ═══════════════════════════════════════════════════
# CONFIG — edit these for your proxy provider
# ═══════════════════════════════════════════════════
UPSTREAM_HOST = "gw.dataimpulse.com"
UPSTREAM_PORT = 824  # 823=sticky, 824=rotating, 825=sticky+region
# Pre-encoded Basic auth: bd8e6258848d97b0f51d__cr.id:8822dbc7ca29d558
UPSTREAM_AUTH = "YmQ4ZTYyNTg4NDhkOTdiMGY1MWRfX2NyLmlkOjg4MjJkYmM3Y2EyOWQ1NTg="
LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 9876


async def proxy_handler(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(8192), timeout=10)
        if not data:
            return

        first_line = data.split(b"\r\n")[0].decode(errors="replace")
        is_connect = first_line.startswith("CONNECT")

        if is_connect:
            host_port = first_line.split(" ")[1]
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10
            )

            connect_req = (
                f"CONNECT {host_port} HTTP/1.1\r\n"
                f"Host: {host_port}\r\n"
                f"Proxy-Authorization: Basic {UPSTREAM_AUTH}\r\n"
                f"Proxy-Connection: keep-alive\r\n\r\n"
            ).encode()
            upstream_writer.write(connect_req)
            await upstream_writer.drain()

            upstream_resp = await asyncio.wait_for(
                upstream_reader.read(4096), timeout=10
            )
            if b"200" not in upstream_resp.split(b"\r\n")[0]:
                writer.write(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                await writer.drain()
                upstream_writer.close()
                writer.close()
                return

            writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await writer.drain()

            await asyncio.gather(
                _relay(upstream_reader, writer),
                _relay(reader, upstream_writer),
            )
            upstream_writer.close()

        else:
            upstream_reader, upstream_writer = await asyncio.wait_for(
                asyncio.open_connection(UPSTREAM_HOST, UPSTREAM_PORT), timeout=10
            )
            auth_header = f"Proxy-Authorization: Basic {UPSTREAM_AUTH}\r\n"
            lines = data.split(b"\r\n")
            lines.insert(1, auth_header.encode())
            modified_data = b"\r\n".join(lines)
            upstream_writer.write(modified_data)
            await upstream_writer.drain()

            while True:
                chunk = await asyncio.wait_for(
                    upstream_reader.read(65536), timeout=30
                )
                if not chunk:
                    break
                writer.write(chunk)
                await writer.drain()
            upstream_writer.close()

    except asyncio.TimeoutError:
        pass
    except Exception as e:
        print(f"[relay] Error: {e}", flush=True)
    finally:
        try:
            writer.close()
        except:
            pass


async def _relay(src, dst):
    try:
        while True:
            data = await asyncio.wait_for(src.read(65536), timeout=300)
            if not data:
                break
            dst.write(data)
            await dst.drain()
    except:
        pass


async def main():
    server = await asyncio.start_server(proxy_handler, LOCAL_HOST, LOCAL_PORT)
    print(
        f"[relay] Listening on {LOCAL_HOST}:{LOCAL_PORT} → "
        f"{UPSTREAM_HOST}:{UPSTREAM_PORT}",
        flush=True,
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
