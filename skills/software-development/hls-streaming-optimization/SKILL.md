---
name: hls-streaming-optimization
description: Diagnose and fix slow video playback in HLS-based web players (Next.js, Vercel, generic Node). Covers proxy edge caching, region pinning, HLS.js tuning, error recovery, and `<video>` tag hygiene. Use when users report slow loading, stalls, or buffering in video apps — especially short-drama / streaming sites that proxy CDN content through serverless routes.
when_to_use: |
  - User reports "loading lama / nggak jalan / buffer terus" on a video player
  - Designing a new HLS player and want it fast from day one
  - Auditing a streaming Next.js/Node app where videos are proxied through `/api/proxy/...`
  - Multi-platform drama/short-video sites where each platform has its own player page
version: 1.0.0
languages: [typescript, javascript]
dependencies: [hls.js, next.js]
---

# HLS Streaming Optimization

Slow video on the web is almost never one bug — it's a stack of small misconfigurations that compound. This skill covers the recurring root causes and the playbook to fix them in one pass.

## Trigger phrases (Indonesian + English)

- "loading lama" / "lambat banget" / "ketika di klik nggak jalan"
- "buffer terus" / "muter terus" / "stuck loading"
- "video lemot" / "slow playback" / "takes forever to start"
- "tolong percepat / optimize streaming"

## The five compounding root causes

When a user says "video is slow," 80% of the time it's a combination of these five. Address all five in one pass — don't ship piecemeal.

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | First-byte latency high | Vercel default region (US/iad1) for Asian users | Pin proxy routes to `sin1` / `hnd1` via `export const preferredRegion` |
| 2 | Replay / next episode is slow too | Proxy returns `Cache-Control: no-store` for binary segments | Set `s-maxage=86400, immutable` on `.ts`/`.mp4`/`.m4s` responses |
| 3 | Stalls under flaky network | HLS.js fatal-on-first-error, no recovery | Multi-stage recovery: NETWORK_ERROR → `startLoad()`, MEDIA_ERROR → `recoverMediaError()`, with retry counter |
| 4 | Click → wait → only THEN starts loading | Missing `preload="auto"` on `<video>` | Add it. Browsers wait for user gesture without it. |
| 5 | TLS handshake on every segment | Proxy creates fresh https.Agent per request | Module-level `new https.Agent({ keepAlive: true, maxSockets: 64 })` |

## The 6-step audit & fix workflow

Always run this full sweep — partial fixes leave latency on the table.

### 1. Map the streaming surface

```bash
# Find every HLS player page
grep -rn "import Hls\|new Hls(" src/app/watch/ src/components/ src/pages/

# Find every proxy / streaming route
find src/app/api -type d | grep -iE "proxy|stream|hls|ts-proxy"

# Find every <video> tag
grep -rn "<video" src/app/watch/ src/pages/watch/
```

Count player files and proxy routes. If you find ≥ 3 player pages with copy-pasted HLS init code, you have a duplication problem (see step 3).

### 2. Patch proxy routes — region + cache + keep-alive

For every Node-runtime proxy that serves video bytes:

```typescript
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';
export const preferredRegion = ['sin1', 'hnd1']; // SE Asia / Tokyo

// Module-scope, reused across requests
const httpsAgent = new https.Agent({ rejectUnauthorized: false, keepAlive: true, maxSockets: 64 });
const httpAgent  = new http.Agent({ keepAlive: true, maxSockets: 64 });
```

Set Cache-Control by content type:

| Content | Cache-Control |
|---------|---------------|
| Binary segment (`.ts`, `.mp4`, `.m4s`, `video/*`) | `public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800, immutable` |
| HLS manifest (`.m3u8`) | `public, max-age=60, s-maxage=300, stale-while-revalidate=1800` |
| Subtitles (`.vtt`, `.srt`) | `public, max-age=86400, s-maxage=604800, immutable` |
| JSON API responses | `no-store` (let React Query handle client cache) |

### 3. Replace per-page HLS init with a shared hook

If you find 3+ player pages each with their own `new Hls(...)` block, **stop fixing them individually**. Drop in `templates/use-hls-player.ts` (in this skill) at `src/hooks/use-hls-player.ts` and rewrite each page to:

```typescript
const videoUrl = useMemo(/* ... */, [...]);
const hlsRef = useHlsPlayer(videoRef, videoUrl, { onFatal: () => setUseProxy(true) });
```

Net reduction in our last sweep: 10 player pages, **-386 lines, +128 lines**, every player now identical and tunable from one place.

### 4. Patch every `<video>` tag

```jsx
<video
  ref={videoRef}
  controls
  autoPlay
  playsInline       // iOS inline play
  preload="auto"    // ← critical: starts buffering before user click
  crossOrigin="anonymous"
  onEnded={handleVideoEnded}
/>
```

Without `preload="auto"`, browsers may use `metadata` or `none` and not fetch any media until first play attempt — adding ~1-3s to perceived load time.

### 5. Update `next.config.ts` to NOT override proxy headers

Common foot-gun: blanket `Cache-Control: no-store` on `/api/:path*` overrides per-route headers in Vercel's edge layer. Use a negative-lookahead source pattern:

```typescript
{
  // Keep no-store for JSON APIs but exclude streaming/proxy routes that set their own
  source: "/api/((?!proxy/video|goodshort/ts-proxy|goodshort/stream-proxy|shortmax/hls|streaming-service/decrypt-stream).*)",
  headers: [{ key: "Cache-Control", value: "no-store" }],
},
```

When adding a new streaming route, add it to this exclusion list. Forgetting this is silent — headers look right in route code, look wrong in browser dev tools.

### 6. Verify

```bash
# Type check
npx tsc --noEmit -p tsconfig.json

# Build
npm run build

# After deploy, confirm region pinning + cache headers
curl -sI "https://<host>/api/proxy/video?url=<encoded-test-url>" | grep -iE "x-vercel-id|cache-control"
# Expect:  x-vercel-id: sin1::...   AND   cache-control: public, max-age=3600, s-maxage=86400, ...
```

`x-vercel-id` first segment shows which region handled the request. Should be `sin1` (Singapore) or `hnd1` (Tokyo) for SE Asian users.

## Pitfalls

- **Don't set `Cache-Control` on partial-content (HTTP 206) responses naively.** Range requests for video scrubbing must keep `Accept-Ranges: bytes` and not be cached as the full asset. Our pattern caches the chunked binary URL, not the byte range — Vercel handles this correctly because the URL itself is the cache key including range hints from upstream.
- **`new Hls()` with no config = bad defaults.** Default `maxBufferLength` is 30s but other knobs (retry policy, ABR seed, `capLevelToPlayerSize`) are unset and will cause flakiness on mobile. Always pass the tuned config from `templates/use-hls-player.ts`.
- **`startLevel: -1` causes 1-3s delay before first frame.** This is the #1 root cause of "click → nothing happens for 2 seconds". With `-1`, HLS.js must download the manifest, parse all quality levels, run the ABR algorithm, then pick a level — all before fetching the first segment. For short drama (2-5 min episodes), set `startLevel: 0` (lowest quality first). ABR will upgrade after a few segments once bandwidth is measured. The quality difference in the first 3 seconds is imperceptible; the speed difference is not.
- **`maxBufferLength: 30` delays playback start.** HLS.js won't fire `MANIFEST_PARSED` and start play until it has buffered `maxBufferLength` seconds. 30s means it tries to pre-buffer 30 seconds before the video starts — on a proxied route this is 3-5 seconds of dead time. Use `maxBufferLength: 8` for fast start. Set `maxMaxBufferLength: 60` so it grows the buffer once playing. This is the correct split: start fast, buffer deep.
- **`abrEwmaDefaultEstimate: 1_500_000` (1.5 Mbps) causes quality stalls.** An optimistic seed makes HLS.js request a high-quality level first. If the proxied route can't deliver that fast enough, it stalls and downgrades — visible as a freeze right after the video starts. Use `500_000` (500 Kbps) as the seed. ABR upgrades quickly once real bandwidth is measured.
- **Don't forget `playsInline` on iOS.** Without it, Safari forces fullscreen on play, breaking the in-page player UX.
- **HLS.js error recovery is mandatory, not optional.** Default `hls.destroy()` on first fatal error means one packet loss kills the session. Track recovery attempts (`MAX_RECOVERY = 3`) and try `startLoad()` for network, `recoverMediaError()` for media before giving up.
- **`withCredentials = false` in xhrSetup.** Some CDNs reject requests with credentials. Forcing it false avoids this.
- **`crossOrigin="anonymous"` on `<video>` is required for subtitle tracks** to render when served from a different origin (or via your own proxy).
- **Don't send `Origin` header from the proxy to upstream CDN** — many video CDNs whitelist Origin and return 403 if it doesn't match. Pass `Referer` only.
- **Don't attach raw `Hls.Events` listeners outside the hook.** When you have a `useHlsPlayer` hook that returns `hlsRef`, it's tempting to do `hlsRef.current.on(Hls.Events.MANIFEST_PARSED, ...)` in a separate `useEffect` for subtitle injection. This leaks listeners that are never cleaned up and fires after the hook has already destroyed the instance. Use video element events (`loadeddata`, `canplay`, `playing`) + a short polling interval instead — they cover the same race conditions without touching the HLS instance directly.
- **`next/font` migration is part of the same performance pass.** If the app uses `<link href="fonts.googleapis.com/...">` in layout, that's a render-blocking request. Migrate to `next/font/google` (Poppins, Bebas_Neue, etc.) at the same time as the video optimizations — it eliminates the external CSS request and preloads only the weights actually used. Also remove any `@import url(fonts.googleapis.com)` from `globals.css` — having both is double-loading.

## Upstream API blacklist — the silent killer

When video stops loading entirely (not slow, but broken — `success: false, error: Internal server error` from all API routes), the root cause may not be in your code at all.

**Symptom:** All API routes return errors. Episode count shows `1/0`. Video never loads. Decrypt reveals `{"success":false,"error":"Internal server error"}`.

**Diagnosis:**
```bash
# Test upstream API directly from Vercel's perspective
curl -s "https://api.upstream.com/endpoint?id=1"
# If you see: {"error":"Forbidden","message":"IP Anda telah diblacklist..."}
# → The upstream API has blacklisted Vercel's datacenter IPs
```

**Why it happens:** Vercel serverless functions run from AWS/Cloudflare datacenter IPs. Upstream APIs that track "suspicious activity" (many requests from same IP range) will blacklist entire datacenter CIDR blocks. This is common with Indonesian drama/short-video APIs.

**Fix options (in order of preference):**
1. **Use api.anichin.bio (free trial)** — 15 platforms, works from Vercel, episodes 1-5 unlocked. See `references/anichin-api.md`. Best for free streaming sites that only need first few episodes.
2. **Switch to a paid API aggregator** that handles upstream access themselves (e.g. CUTAD API at `cutad.web.id` — covers 15 providers, Rp 5.000–175.000/period). See `references/cutad-api.md`. Best for full episode access.
3. **Proxy through your own VPS** — Vercel → VPS (residential/cloud IP not yet blacklisted) → upstream. Adds ~50-100ms but bypasses the block.
4. **Contact upstream** to whitelist your Vercel IPs. Rarely works for free-tier APIs.
5. **Self-host the upstream API** if source code is available for purchase.

- **Don't waste time debugging your code** when the upstream returns 403/blacklist. Always test the upstream directly first before auditing route handlers.

## Drama platform API protection landscape (May 2026)

All major short-drama platforms protect their APIs with WAF that blocks datacenter IPs:

| Platform | API Base | Protection | Datacenter blocked? | Scrapeable? |
|----------|----------|------------|---------------------|-------------|
| ShortMax | `shorttv.live` | Custom segment encryption | ✅ API blocked | ✅ HTML scrape works |
| ReelShort | `api.reelshort.com` | Client-side + encryption | ✅ Yes | ❌ No |
| NetShort | `netshort.com/prod-web-api` | RSA-encrypted requests | ✅ Yes | ❌ No |
| GoodShort | `goodshort.com` | Client-side rendered | ✅ Yes | ❌ No |
| PineDrama | `pinedrama.com` | Client-side rendered | ✅ Yes | ❌ No |
| Melolo | `melolo.com` | DRM/iframe embed | N/A | ❌ No (DRM) |
| Sansekai (aggregator) | `api.sansekai.my.id` | IP blacklist | ✅ Yes (all server IPs) | ❌ No |
| Anichin (aggregator) | `api.anichin.bio` | None | ❌ No — works! | ✅ Yes (ep 1-5) |
| CUTAD (aggregator) | `cutad.web.id` | API key | ❌ No — paid | ✅ Yes (paid) |
| **Dobda (aggregator)** | `api-drama.dobda.id` | API key | ❌ No — paid | ✅ Yes (22+ platforms, Rp50K best value) |

**Practical implication:** For free streaming sites, only ShortMax can be self-scraped from Vercel. Use Anichin API for other platforms (limited to episodes 1-5). For full access, buy CUTAD API.

See `references/drama-platform-protection-research-may2026.md` for detailed analysis of each platform's protection.

**Error signatures:**
- Akamai: `<H1>Access Denied</H1>` with `Reference #18.xxxxx`
- Sansekai blacklist: `{"error":"Forbidden","message":"IP Anda telah diblacklist karena aktivitas mencurigakan..."}`
- CloudFront: `403 ERROR - Request blocked`

## Indonesian / SE Asia specifics

- Region pin: `['sin1', 'hnd1']` (Singapore primary, Tokyo fallback). Don't use `iad1` (Virginia) or `cdg1` (Paris) — adds 200-400ms RTT.
- Vercel free tier supports `preferredRegion` on Pro+. On Hobby, the directive is silently ignored but harmless.
- Cloudflare R2 / Tencent COS / Alibaba OSS as origin is common in this space; all support `Range` and respond well to keep-alive.

## Files

- `templates/use-hls-player.ts` — drop-in shared HLS hook with tuned config and 3-stage error recovery. Copy to `src/hooks/` and import. Battle-tested across 5 player pages on my-project. Returns `hlsRef` so callers can attach additional listeners if needed.
- `templates/proxy-video-route.ts` — complete Next.js `/api/proxy/video` route with all fixes: keep-alive agents, region pin, per-content-type Cache-Control, m3u8 URL rewriting, subtitle injection, VTT/SRT conversion. Copy and adapt the URL rewriting logic for your manifest format.
- `references/diagnosis-checklist.md` — quick-reference checklist for "video is slow" tickets — what to grep, what to measure, what to ship.
- `references/cutad-api.md` — CUTAD API docs (cutad.web.id): 15-provider drama aggregator, pricing (Rp 5k–175k), endpoints, and migration notes for my-project. Use when upstream API is blacklisting Vercel IPs.
- `references/dobda-api.md` — api-drama.dobda.id: 22+ platform aggregator, cheapest at Rp10K trial / Rp50K Starter (best value). More platforms than CUTAD, works from Vercel. Contact @hplssmnct on Telegram.
- `references/anichin-api.md` — Anichin API (api.anichin.bio): FREE 15-platform drama API with trial token. Episodes 1-5 unlocked. Works from Vercel. Discovered May 2026 as sansekai alternative.
- `references/shortmax-api-reverse-engineering-may2026.md` — ShortMax (shorttv.live) reverse engineering: AES encryption key discovery, Cheerio scraping for Vercel, HLS proxy with custom decryption, CORS bypass pattern. Complete working implementation.

## Fallback: HTML scraping when API is blocked

When all API approaches fail (datacenter blocked, signature validation, SSR-only), scrape rendered HTML:

**Cheerio for Vercel (no Playwright needed):**
```typescript
import * as cheerio from 'cheerio';

async function getDramas(): Promise<Drama[]> {
  const html = await fetch('https://www.shorttv.live/dramas', {
    headers: { 'User-Agent': 'Mozilla/5.0 ...' },
    next: { revalidate: 300 }
  }).then(r => r.text());
  
  const $ = cheerio.load(html);
  const dramas: Drama[] = [];
  
  $('a[href*="/drama/"]').each((_, el) => {
    const href = $(el).attr('href');
    const match = href?.match(/drama\/([^/]+)-(\d+)$/);
    if (match) {
      dramas.push({
        id: match[2],
        slug: href!.replace('/drama/', ''),
        title: $(el).find('img').attr('alt') || $(el).text().trim(),
        cover: $(el).find('img').attr('src') || null
      });
    }
  });
  
  return dramas;
}
```

**Playwright for video URLs (need to capture network):**
```python
async def get_video_url(slug, episode):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        captured = []
        page.on('request', lambda r: captured.append(r.url) if '.m3u8' in r.url else None)
        
        await page.goto(f"https://www.shorttv.live/episode/{slug}-{episode}")
        await asyncio.sleep(5)
        
        urls = {}
        for url in captured:
            if '_480/' in url: urls['480p'] = url
            elif '_720/' in url: urls['720p'] = url
            elif '_1080/' in url: urls['1080p'] = url
        
        await browser.close()
        return urls
```

**When to use scraping vs API:**
- **Cheerio:** Drama list, detail pages (static content in HTML)
- **Playwright:** Video URLs (only in network requests, not HTML)
- **API:** When available and not blocked (fastest, most reliable)

**Limitations:**
- Scraping is slower than API (1-3s vs 100-300ms)
- HTML structure can change without notice
- Video URLs require Playwright (can't run on Vercel serverless)
- Cache aggressively (1+ hours) to reduce scraping load

**Architecture for Vercel + scraping:**
1. Cheerio scraper in API routes for drama list/detail
2. Separate VPS service with Playwright for video URLs
3. Vercel calls VPS service when video URL needed
4. VPS caches video URLs for 1 hour

See `references/shortmax-api-reverse-engineering-may2026.md` for full implementation details including:
- AES encryption key discovery from JS bundles
- Cheerio scraping patterns for Nuxt/Next.js SSR apps
- HLS proxy with custom segment decryption
- CORS bypass via API proxy

## Related skills

- `nextjs-react-typescript` — general Next.js / React patterns, but does not cover video specifics
- `vps-app-deployment` — alternative when Vercel's serverless cost or region constraints aren't a fit; you'd run the proxy on a SG/JP VPS instead
