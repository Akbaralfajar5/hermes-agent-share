# ShortMax/ShortTV API Reverse Engineering (May 2026)

## Platform Overview
- **Domain**: shorttv.live (redirects from shortmax.com)
- **Stack**: Nuxt 3 with SSR, encrypted payloads
- **Protection**: Akamai + server-side API validation
- **CDN**: Akamai for video delivery

## Key Findings

### 1. Encryption Discovery
Found in JS bundle `/_nuxt/Dc2*.js`:
```javascript
// AES-128-CBC encryption
key = "shortwebapiaesen"  // 16 chars
iv  = "shortwebapiaesen"  // same as key
mode = CBC
padding = PKCS7
```

**How to find encryption keys:**
```python
import httpcloak
import re

session = httpcloak.Session(preset='chrome-latest')
response = session.get("https://www.shorttv.live/_nuxt/Dc2*.js")

# Search patterns
patterns = [
    r'["\']([a-zA-Z0-9]{16})["\'].*?(?:key|secret|aes)',
    r'CryptoJS\.AES',
    r'crypto-js',
]
```

### 2. API Endpoints (Blocked)
```
POST https://shortweb.shorttv.live/app-api/app/cmsClassNew/queryList
POST https://shortweb.shorttv.live/app-api/app/cmsShortPlay/queryPage
POST https://shortweb.shorttv.live/app-api/app/cmsShortPlay/detail
```

**Why blocked:**
- Server validates request origin (SSR only)
- Even with correct encryption, returns `{"code": 500, "msg": "非法请求!!"}`
- Not IP-based — residential proxy doesn't help
- Nuxt server calls API, not browser

### 3. httpcloak for TLS Fingerprinting
```python
import httpcloak

# Available presets
presets = httpcloak.available_presets()
# ['chrome-latest', 'android-chrome-latest', 'firefox-latest', ...]

session = httpcloak.Session(
    preset='chrome-latest',  # or 'android-chrome-latest'
    timeout=30
)

# Test with proper headers
response = session.get(url, headers={
    "User-Agent": "Mozilla/5.0 ...",
    "Accept": "text/html,application/xhtml+xml",
})
```

**Note:** httpcloak helps with TLS fingerprint but doesn't bypass server-side origin validation.

### 4. Working Solution: HTML Scraping

Since API is SSR-only, scrape rendered HTML:

```python
# Drama list
from playwright.async_api import async_playwright
import asyncio

async def get_dramas():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.shorttv.live/dramas", wait_until='load')
        await asyncio.sleep(2)
        
        dramas = await page.evaluate('''
            () => {
                const items = [];
                document.querySelectorAll('a[href*="/drama/"]').forEach(link => {
                    const href = link.getAttribute('href');
                    const img = link.querySelector('img');
                    const match = href.match(/drama\/([^/]+)-(\d+)$/);
                    if (match) {
                        items.push({
                            id: match[2],
                            slug: href.replace('/drama/', ''),
                            title: img?.alt || link.textContent.trim(),
                            cover: img?.src
                        });
                    }
                });
                return items;
            }
        ''')
        await browser.close()
        return dramas
```

### 5. Video URL Extraction

Video URLs are in network requests, not HTML:

```python
async def get_video_url(slug, episode):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        captured = []
        page.on('request', lambda r: captured.append(r.url) if '.m3u8' in r.url else None)
        
        await page.goto(f"https://www.shorttv.live/episode/{slug}-{episode}")
        await asyncio.sleep(5)
        
        # Parse qualities
        urls = {}
        for url in captured:
            if '_480/' in url: urls['480p'] = url
            elif '_720/' in url: urls['720p'] = url
            elif '_1080/' in url: urls['1080p'] = url
        
        await browser.close()
        return urls
```

**Video URL format:**
```
https://akamai-static.shorttv.live/hls-encrypted/{content_id}_{quality}/main.m3u8
```

### 6. Cheerio Alternative (No Playwright)

For Vercel/serverless where Playwright isn't available:

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

**Limitation:** Can't get video URLs without Playwright (need to capture network requests).

## Platform Comparison (May 2026)

| Platform | API Status | Protection | Solution |
|----------|------------|------------|----------|
| ShortMax/ShortTV | SSR-only | Akamai | HTML scrape |
| ReelShort | 404 | Unknown | No public API |
| NetShort | Blocked | Cloudflare | - |
| FreeReels | Blocked | Cloudflare | - |
| GoodShort | Blocked | Unknown | - |
| Bilibili | ✅ Open | None | Direct API |
| iQIYI | ✅ Open | None | Direct API |

## Lessons Learned

1. **SSR apps hide APIs** — If `__NUXT__` data is encrypted and no XHR in Network tab, API is server-side only
2. **httpcloak preset matters** — Use `chrome-latest` for web, `android-chrome-latest` for mobile APIs
3. **Encryption keys in JS bundles** — Search for 16/32 char strings near `CryptoJS`, `AES`, `encrypt`
4. **Playwright for video URLs** — m3u8 URLs only appear in network requests, not HTML
5. **Cheerio for static content** — Works on Vercel, but limited to what's in HTML
6. **Cache aggressively** — Scraping is slow; cache results for 1+ hours
