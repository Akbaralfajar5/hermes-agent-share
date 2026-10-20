# CUTAD API — Drama Streaming Aggregator

Source: https://www.cutad.web.id/docs  
Verified: May 2026

## Overview

Unified REST API aggregating 15 drama/film/anime providers. Single API key unlocks all providers. Handles upstream access, rate limiting, and HLS stream URL extraction.

## Pricing

| Paket | Harga | Durasi |
|-------|-------|--------|
| Testing | Rp 5.000 | 1 hari |
| Reguler | Rp 29.000 | 2 minggu |
| Populer ⭐ | Rp 58.000 | 1 bulan |
| Setia | Rp 175.000 | 3 bulan |

Payment: QRIS (GoPay, OVO, DANA, ShopeePay, BCA, semua bank QRIS). Key aktif langsung setelah bayar.

## Base URL & Auth

```
Base: https://www.cutad.web.id/api/public
Auth: Header x-api-key: cutad_xxx  (recommended)
   OR Query ?key=cutad_xxx
```

## 15 Providers

| Provider | Slug | Type |
|----------|------|------|
| ReelShort | `reelshort` | SHORT |
| MovieBox | `moviebox` | FILM |
| DotDrama | `dotdrama` | DRAMA |
| NetShort | `netshort` | SHORT |
| FreeReels | `freereels` | SHORT |
| Film Indonesia | `sfilmindo` | FILM |
| Drama Korea | `dramakorea` | DRAMA |
| Anime | `anime` | ANIME |
| Hollywood | `hollywood` | FILM |
| Box Office | `boxoffice` | FILM |
| StardustTV | `stardusttv` | SHORT |
| DramaWave | `dramawave` | SHORT |
| MeloShort | `meloshort` | SHORT |
| DramaBite | `dramabite` | SHORT |
| GoodShort | `goodshort` | SHORT |

## 5 Endpoints (same for all providers)

```
GET /api/public/{provider}?action=rank          # trending/populer
GET /api/public/{provider}?action=detail&id=X   # detail konten
GET /api/public/{provider}?action=episodes&id=X # list episode
GET /api/public/{provider}?action=stream&videoFakeId=X  # HLS URL + subtitle VTT
GET /api/public/{provider}?action=search&q=keyword      # search
```

## Response Format

```json
{
  "status": true,
  "provider": "reelshort",
  "data": [ ... ]
}
```

## Integration Flow (for my-project)

When migrating from sansekai API to CUTAD:

1. Store API key in `.env.local` as `CUTAD_API_KEY=cutad_xxx`
2. Replace per-platform upstream fetch URLs with CUTAD endpoints
3. Map CUTAD response fields to existing TypeScript interfaces
4. The `stream` action returns HLS URL directly — no need for separate decrypt/proxy for most providers
5. Rate limit: 100 req/min — sufficient for hundreds of concurrent users

## Endpoint call order for watch page

```
rank → (pick item) → detail → episodes → (pick episode) → stream → HLS URL → play
```

## Notes

- `stream` action returns `m3u8` URL + VTT subtitle URL ready to use
- For providers that already existed in sansekai (NetShort, ReelShort, FreeReels, GoodShort), field names may differ — check response shape before assuming 1:1 mapping
- Rate limit is per-key, not per-IP — safe to use from Vercel serverless
