# "Video is slow" — diagnosis checklist

Run these in order. Stop at the first red flag — fix it, redeploy, retest. Most apps fail multiple checks.

## Cold-start vs replay

- **Cold (first time playing this video, ever):** dominated by upstream CDN + your proxy round trip
- **Warm (you played it before, hit refresh):** should be near-instant if Edge cache is on
- **Cross-user (someone else already played it):** should also be near-instant if `s-maxage` works

Test all three. If only cold is slow → look at region pin + keep-alive. If warm is slow too → cache headers are wrong or being overridden.

## 1. Region check (30 seconds)

```bash
curl -sI "https://<host>/api/proxy/video?url=<encoded-test-url>" | grep x-vercel-id
# Want: x-vercel-id: sin1::...   (or hnd1)
# Bad:  x-vercel-id: iad1::...   ← request hit Virginia, +200ms RTT for SEA users
```

If wrong region, check that the route file has:
```typescript
export const preferredRegion = ['sin1', 'hnd1'];
export const runtime = 'nodejs';
```

## 2. Cache header check

```bash
# Direct route
curl -sI "https://<host>/api/proxy/video?url=<encoded-real-segment>" | grep -i cache-control
# Binary: public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800, immutable
# Manifest: public, max-age=60, s-maxage=300, stale-while-revalidate=1800
# JSON API: no-store

# x-vercel-cache after 2 requests should be HIT for binary segments
curl -sI "..." | grep x-vercel-cache  # MISS first time, HIT second time
```

If you set the header in the route but see `no-store` in production: check `next.config.ts` `headers()` for a blanket override. Use a negative-lookahead source pattern.

## 3. HLS.js config check — the three most common killers

```bash
grep -rn "new Hls(\|startLevel\|maxBufferLength\|abrEwmaDefault" src/
```

For each match, check these three settings specifically:

**`startLevel`**
- ❌ `startLevel: -1` (or missing) — HLS.js probes all quality levels before fetching first segment. Adds 1-3s before first frame. This is the #1 cause of "click → nothing happens".
- ✅ `startLevel: 0` — start at lowest quality immediately. ABR upgrades after a few segments.

**`maxBufferLength`**
- ❌ `maxBufferLength: 30` (default) — HLS.js tries to pre-buffer 30s before starting play. On a proxied route this is 3-5s of dead time.
- ❌ `maxBufferLength: 10` — too low, will stall on any network blip.
- ✅ `maxBufferLength: 8` + `maxMaxBufferLength: 60` — fast start, grows buffer once playing.

**`abrEwmaDefaultEstimate`**
- ❌ `1_500_000` (1.5 Mbps) — optimistic seed causes HLS.js to request high quality first, stall, then downgrade. Visible as a freeze right after video starts.
- ✅ `500_000` (500 Kbps) — conservative seed. ABR upgrades quickly once real bandwidth is measured.

If you see ≥3 different ad-hoc configs across your player pages, you have drift. Consolidate via `useHlsPlayer` template.

## 4. `<video>` tag check

```bash
grep -rn "<video" src/app/watch/ | head
# Then for each, verify it has preload="auto" + playsInline
grep -rn "preload" src/app/watch/
```

Missing `preload="auto"` → 1-3s perceived delay before playback starts. Browsers wait for user gesture.

## 5. Error recovery check

```bash
grep -B2 -A10 "Hls.Events.ERROR" src/
```

For each handler:
- ❌ Just calls `hls.destroy()` on fatal — no recovery, one bad packet kills session
- ❌ Calls `startLoad()` unconditionally — infinite retry loop on permanent errors
- ✅ Switches on `data.type` (NETWORK / MEDIA / OTHER), with retry counter

## 6. Keep-alive check

```bash
grep -n "new https.Agent\|new http.Agent" src/app/api/
```

Module-scope `new https.Agent({ keepAlive: true })` is correct. Per-request `new https.Agent(...)` inside the handler defeats the purpose — every segment fetch does a fresh TLS handshake.

## 7. Vercel function logs

In Vercel dashboard → Functions → Logs, look for:
- `Cold start: <N>ms` — should be < 500ms; if higher, something is loading too much at module scope
- Repeated identical upstream URLs hitting the function — Edge cache isn't catching them, recheck headers
- `ECONNRESET` / `ETIMEDOUT` from upstream CDN — keep-alive may be re-using closed sockets, lower `maxSockets` or add socket timeout

## Red flags I've seen in the wild

- `startLevel: -1` with no comment — looks like "auto" but actually means "probe everything first"
- `maxBufferLength: 30` (default) — looks fine but delays playback start by 3-5s on proxied routes
- `abrEwmaDefaultEstimate: 1_500_000` — optimistic seed causes quality stall on first play
- "Cache-Control: no-cache" on `.ts` segments — author thought it meant "cache normally" but forces revalidation every time
- `xhr.withCredentials = true` in HLS.js xhrSetup — some CDNs reject this with 403
- Sending `Origin` header from proxy to upstream — same 403 issue
- `useEffect(() => { /* HLS init */ }, [])` with `[]` deps — never re-init when source URL changes
- HLS.js MP4 sources passed through HLS.js — MP4 should go to native `video.src`, not HLS.js
- Raw `Hls.Events` listeners attached outside the hook — leaks listeners, fires after instance is destroyed

## When to escalate from Vercel to a VPS

If after all of the above the latency is still bad for SEA users, the bottleneck is the upstream CDN itself or Vercel's serverless overhead at scale. Consider:
- Move the proxy to a SG/JP VPS (Tencent, Vultr, DigitalOcean) — fixed RTT, no cold starts
- Add Cloudflare in front for extra edge cache layer
- Negotiate direct CDN access if upstream allows it
