# api-drama.dobda.id — Drama API Aggregator

Discovered: May 2026
Status: Active, production-ready
Contact: Telegram @hplssmnct

## Overview

Premium drama API aggregator supporting **22+ platforms** in one unified endpoint. More platforms and cheaper than CUTAD. Works from Vercel (no IP blacklist issues).

## Pricing (May 2026)

| Tier | Price | Requests/day | Platforms | Proxy | Notes |
|------|-------|--------------|-----------|-------|-------|
| Trial | Rp10K (~$0.59) | 200 | 3 | ❌ | 7 days only |
| Nano | Rp17K (~$1) | 500 | 5 | ❌ | Dev/sandbox |
| Lite | Rp35K (~$2) | 1,500 | 10 | ❌ | Side projects |
| **Starter** | Rp50K (~$3) | 4,000 | 25 | ✅ | **Best value for small sites** |
| Streamer | Rp120K (~$7) | 10,000 | All | ✅ | + Subtitle proxy |
| Professional | Rp170K (~$10) | 25,000 | All | ✅ | High traffic |
| Business | Rp250K (~$15) | 50,000 | All | ✅ | |
| Enterprise | Rp500K (~$30) | 100,000 | All | ✅ | |

## Recommendation

**Starter (Rp50K/month)** is the sweet spot for my-project-scale sites:
- 4,000 req/day handles moderate traffic
- 25 platforms covers all major short-drama apps
- Proxy included (bypasses CORS)
- ~$3/month is negligible

## API Access

Base URL: `https://api-drama.dobda.id/api/v1`

Without API key:
```bash
curl -s "https://api-drama.dobda.id/api" -H "User-Agent: okhttp/4.12.0"
# Returns: {"success":false,"message":"Access denied."}
```

API key required for all endpoints. Contact @hplssmnct on Telegram to purchase.

## Supported Platforms (22+)

Based on their landing page, includes:
- ShortMax
- ReelShort
- NetShort
- GoodShort
- PineDrama
- Melolo
- FlexTV
- MoboReels
- ShortTV
- DramaShort
- TopShort
- And 10+ more regional platforms

## Why Choose Over Alternatives

| Feature | dobda.id | CUTAD | Sansekai | Anichin |
|---------|----------|-------|----------|---------|
| Platforms | 22+ | 15 | 9 | 15 |
| Cheapest paid | Rp10K | Rp5K | N/A | Free |
| Best value | Rp50K/4K req | Rp25K/2K req | Blacklisted | Ep 1-5 only |
| Works from Vercel | ✅ | ✅ | ❌ | ✅ |
| Proxy included | ✅ (Starter+) | ❌ | N/A | ❌ |

## Integration Notes

1. **User-Agent**: Use mobile app UA for best compatibility
   ```
   User-Agent: okhttp/4.12.0
   ```

2. **Caching**: Cache responses aggressively (drama metadata rarely changes)
   - Drama list: 1 hour
   - Drama detail: 6 hours
   - Episode list: 1 hour
   - Video URLs: 30 minutes (may expire)

3. **Error handling**: API returns consistent format
   ```json
   {"success": false, "message": "Access denied."}
   {"success": true, "data": {...}}
   ```

## Migration from Sansekai

If currently using `api.sansekai.my.id` (which blacklists Vercel IPs):

1. Purchase Starter tier from @hplssmnct
2. Replace base URL: `api.sansekai.my.id` → `api-drama.dobda.id/api/v1`
3. Add API key header (format TBD after purchase)
4. Response format should be similar (both are Indonesian aggregators)

## Source

Found via GitHub search for drama streaming APIs:
- `irwanx/quickplay-download` — Flutter app using this API
- Landing page: https://api-drama.dobda.id/
