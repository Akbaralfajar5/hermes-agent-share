# Anichin API — Free Drama Streaming API

**Base URL:** `https://api.anichin.bio`
**Trial Token:** `TRIAL-ANICHIN-2026` (free, 50 req/min, 1 day validity — but appears to keep working)
**Docs:** https://github.com/NingRong2/anichin-api

## When to use

When upstream drama APIs (e.g. `api.sansekai.my.id`) blacklist Vercel/datacenter IPs, this is a free alternative that works from serverless functions. Discovered May 2026 when sansekai started returning:
```json
{"error":"Forbidden","message":"IP Anda telah diblacklist karena aktivitas mencurigakan..."}
```

## Supported platforms (15 sources)

| Source slug | Platform | Example ID | Extra endpoints |
|-------------|----------|------------|-----------------|
| `reelshort` | ReelShort | `699d1eefa3a7262cff05534b` | `homepage` |
| `shortmax` | ShortMax | `18854` | `recommended`, `homepage` |
| `netshort` | NetShort | `2034157133506805762` | `recommended` |
| `goodshort` | GoodShort | `31001188126` | `homepage` |
| `dramawave` | DramaWave | `LeMYdgoXZM` | `recommended` |
| `flickreels` | FlickReels | `5672` | `hotrank` |
| `freereels` | FreeReels | `51bAUXzvfP` | `homepage`, `hotrank` |
| `stardusttv` | StardustTV | `146` | — |
| `idrama` | iDrama | `160000641712` | — |
| `my-project` | my-project | `102062` | `hot`, `new`, `hot+`, `drama18`, `romance` |
| `starshort` | StarShort | `j0NM` | `hotrank`, `latest` |
| `dramabite` | DramaBite | `15384` | `hotrank`, `latest` |
| `melolo` | Melolo | `7522723499182394385` | `latest` |
| `moboreels` | MoboReels | `41896322` | — |

## Core endpoints (all sources)

All endpoints require headers:
```
X-API-Key: TRIAL-ANICHIN-2026
User-Agent: Mozilla/5.0
```

### 1. Trending
```
GET /{source}/trending
```

### 2. For You / Recommended
```
GET /{source}/foryou
```

### 3. Search
```
GET /{source}/search?query=love
```

### 4. Detail + Episodes
```
GET /{source}/detail?id={dramaId}
```
Returns drama metadata + full episode list with `locked` boolean per episode.

### 5. Episode stream URL
```
GET /{source}/episode?id={dramaId}&ep={episodeNumber}
```
Returns:
```json
{
  "code": 200,
  "episodeNumber": 1,
  "locked": false,
  "videoUrl": "https://priv-api.anichin.bio/api/streaming-service/hls?id=...&ts=...&sig=..."
}
```

## Limitations

- **Episodes 1-5 are free (unlocked)**, episodes 6+ are locked (require premium)
- Rate limit: 50 requests/minute
- Trial token validity: stated as 1 day, but observed to keep working
- For production/unlimited access: contact @Anichin_Premium_Bot on Telegram

## Example: curl test

```bash
curl -s "https://api.anichin.bio/streaming-service/trending" \
  -H "X-API-Key: TRIAL-ANICHIN-2026" \
  -H "User-Agent: Mozilla/5.0" | jq '.items[:2]'

# Get episode stream URL
curl -s "https://api.anichin.bio/streaming-service/episode?id=42000008521&ep=1" \
  -H "X-API-Key: TRIAL-ANICHIN-2026" \
  -H "User-Agent: Mozilla/5.0" | jq '.videoUrl'
```

## Migration from sansekai API

The response schema is similar but not identical:

| sansekai field | anichin field |
|----------------|---------------|
| `data.list` | `items` or `rows` |
| `data.drama` | `data` |
| `data.episodes[].video_url` | `data.episodes[].videoUrl` |
| `data.episodes[].is_free` | `data.episodes[].locked` (inverted!) |

Key difference: sansekai uses `is_free: true`, anichin uses `locked: false`. Invert the boolean when migrating.

## Video URL format

The `videoUrl` from episode endpoint is a signed HLS URL:
```
https://priv-api.anichin.bio/api/{source}/hls?id={dramaId}&ep={ep}&ts={timestamp}&sig={signature}
```

This URL can be passed directly to HLS.js. The signature expires, so fetch fresh URLs when user clicks play rather than caching them.

## Comparison with alternatives

| API | Cost | Platforms | Episode limit | Vercel-friendly |
|-----|------|-----------|---------------|-----------------|
| api.sansekai.my.id | Free | 9 | All free | ❌ Blacklists DC IPs |
| cutad.web.id | Rp 5k-175k | 15 | All | ✅ |
| **api.anichin.bio** | Free (trial) | 15 | Ep 1-5 | ✅ |

For a free streaming site showing first 5 episodes, anichin is the best option. For full episodes, use cutad (paid) or self-host.
