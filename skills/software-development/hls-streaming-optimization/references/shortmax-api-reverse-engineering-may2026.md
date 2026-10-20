# ShortMax API Reverse Engineering (May 2026)

Session: my-project optimization, May 19, 2026

## Problem
ShortMax (shorttv.live) API blocked from Vercel datacenter IPs. Need to scrape data directly.

## Discovery Process

### 1. API Encryption Found in JS Bundle
Downloaded `/_nuxt/Dc2...js` bundle and searched for encryption patterns:

```javascript
// Found in bundle:
const key = "shortwebapiaesen"  // AES-128 key (16 chars)
const iv = key                   // IV same as key
// Mode: CBC, Padding: PKCS7
```

**Search patterns that worked:**
```bash
grep -oE '"[a-zA-Z0-9]{16}"' bundle.js | head -20  # Find 16-char strings (AES keys)
grep -E 'encrypt|decrypt|AES|CBC' bundle.js        # Find crypto functions
grep -E 'X-Encrypted|X-Auth' bundle.js             # Find custom headers
```

### 2. API Structure (SSR - Server-Side Rendered)
ShortMax uses Nuxt 3 with SSR. API calls happen server-side, not in browser:
- `__NUXT__` data is encrypted in HTML
- No XHR/fetch visible in browser Network tab
- Data pre-rendered by server

**Implication:** Cannot intercept API calls from browser. Must scrape rendered HTML.

### 3. Working Scraper (Cheerio for Vercel)

```typescript
// src/lib/shortmax-scraper.ts
import * as cheerio from 'cheerio';

const BASE_URL = 'https://www.shorttv.live';
const HEADERS = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
  'Accept': 'text/html,application/xhtml+xml',
};

export async function getDramas(): Promise<Drama[]> {
  const html = await fetch(`${BASE_URL}/dramas`, {
    headers: HEADERS,
    next: { revalidate: 300 }
  }).then(r => r.text());
  
  const $ = cheerio.load(html);
  const dramas: Drama[] = [];
  
  $('a[href*="/drama/"]').each((_, el) => {
    const href = $(el).attr('href');
    // URL pattern: /drama/slug-name-12345
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

export async function getDramaDetail(slug: string): Promise<Detail | null> {
  const html = await fetch(`${BASE_URL}/drama/${slug}`, {
    headers: HEADERS,
    next: { revalidate: 300 }
  }).then(r => r.text());
  
  const $ = cheerio.load(html);
  const title = $('h1').first().text().trim();
  
  const episodes: Episode[] = [];
  $('a[href*="/episode/"]').each((_, el) => {
    const href = $(el).attr('href');
    // URL pattern: /episode/slug-name-12345-1
    const epMatch = href?.match(/episode\/[^/]+-(\d+)$/);
    if (epMatch) {
      const epNum = parseInt(epMatch[1]);
      if (!episodes.find(e => e.number === epNum)) {
        episodes.push({ number: epNum, url: href! });
      }
    }
  });
  
  episodes.sort((a, b) => a.number - b.number);
  return { id: slug.match(/-(\d+)$/)?.[1] || slug, title, episodes };
}
```

### 4. Video URLs (Require Playwright)
Video m3u8 URLs are NOT in HTML - they're loaded via JS after page render.

**Playwright approach (for VPS service):**
```python
async def get_video_url(slug: str, episode: int) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        captured = []
        page.on('request', lambda r: captured.append(r.url) if '.m3u8' in r.url else None)
        
        await page.goto(f"https://www.shorttv.live/episode/{slug}-{episode}")
        await asyncio.sleep(5)  # Wait for video player to init
        
        urls = {}
        for url in captured:
            if '_480/' in url: urls['480p'] = url
            elif '_720/' in url: urls['720p'] = url
            elif '_1080/' in url: urls['1080p'] = url
        
        await browser.close()
        return urls
```

**Video URL pattern:**
```
https://akamai-static.shorttv.live/hls-encrypted/{video_id}_{quality}/main.m3u8
```

### 5. CORS Bypass - HLS Proxy Required
CDN `akamai-static.shorttv.live` blocks cross-origin requests. Must proxy through API:

```typescript
// In episode API route:
function proxyUrl(url: string, request: NextRequest): string {
  const host = request.headers.get("host") || "my-project.vercel.app";
  const proto = request.headers.get("x-forwarded-proto") || "https";
  return `${proto}://${host}/api/shortmax/hls?url=${encodeURIComponent(url)}`;
}

// Return proxied URLs instead of direct CDN URLs
return {
  videoUrl: {
    video_480: proxyUrl(urls['480p'], request),
    video_720: proxyUrl(urls['720p'], request),
    video_1080: proxyUrl(urls['1080p'], request),
  }
};
```

### 6. HLS Proxy with Decryption
ShortMax uses custom encryption on .ts segments (not standard HLS encryption):

```typescript
// /api/shortmax/hls/route.ts
const AES_IV = Buffer.from('shortmax00000000', 'ascii');

function decryptSegment(buf: Buffer): Buffer {
  // Check for "shortmax" magic header
  if (buf.slice(0, 8).toString('ascii') !== 'shortmax') return buf;
  
  // Parse header: key position at bytes 16-20
  const keyPos = parseInt(buf.slice(16, 20).toString('ascii'), 10);
  const keyOffset = keyPos - 24;
  
  // Extract 16-byte AES key
  const aesKey = buf.slice(24 + keyOffset, 24 + keyOffset + 16);
  
  // Assemble ciphertext
  const tail16 = buf.slice(1024, 1040);
  const payload = buf.slice(1040);
  const ciphertext = Buffer.concat([tail16, payload.slice(0, 1024)]);
  
  // AES-128-CBC decrypt
  const decipher = crypto.createDecipheriv('aes-128-cbc', aesKey, AES_IV);
  const decrypted = Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  
  return Buffer.concat([decrypted, payload.slice(1024)]);
}
```

## Architecture Summary

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  my-project  │────▶│  Vercel API      │────▶│  shorttv.live   │
│  (Frontend)     │     │  Routes          │     │  (HTML scrape)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  HLS Proxy       │────▶│  Akamai CDN     │
                        │  /api/shortmax/  │     │  (video .ts)    │
                        │  hls             │     └─────────────────┘
                        └──────────────────┘
```

**Data flow:**
1. Drama list/detail: Cheerio scrapes shorttv.live HTML
2. Video URLs: Extracted from HTML (or Playwright for dynamic content)
3. Video playback: HLS.js → Vercel proxy → Akamai CDN (with decryption)

## Key Learnings

1. **SSR apps hide API calls** - Check `__NUXT__` / `__NEXT_DATA__` for pre-rendered data
2. **Encryption keys often in JS bundles** - Search for 16/32 char strings near crypto functions
3. **CORS requires proxy** - CDNs block cross-origin, proxy through your own API
4. **Custom encryption exists** - Not all HLS uses standard #EXT-X-KEY, some have custom headers
5. **Cheerio works on Vercel** - No Playwright needed for static HTML scraping
6. **Video URLs need Playwright** - Dynamic content loaded by JS requires browser automation

## Files Created

- `src/lib/shortmax-scraper.ts` - Cheerio-based scraper
- `src/app/api/shortmax/latest/route.ts` - Drama list API
- `src/app/api/shortmax/detail/route.ts` - Drama detail API  
- `src/app/api/shortmax/episode/route.ts` - Episode video URLs (proxied)
- `src/app/api/shortmax/hls/route.ts` - HLS proxy with decryption
