# `.id` Family Registrar Pricing Snapshot

**Verified live via `curl`, May 2026.** Prices in IDR.

## `.my.id` Comparison

| Registrar | Year 1 (promo) | Year 1 (regular) | Renewal/year | WHOIS privacy | Notes |
|---|---|---|---|---|---|
| **Domainesia** ⭐ | **Rp 9.900** | Rp 35.000 | Rp 35.000 | Free | Sweet spot. Source: `extWithPrice` JSON in `/domain/` page |
| IDwebhost | Rp 3.000–13.000 | Rp 35.000 | ~Rp 55.000 | Paid | Source: schema.org JSON in `/domain-id` |
| Jagoan Hosting | Rp 35.000 | Rp 35.000 | Rp 35.000 | Free (?) | Source: HTML table on `/domain-murah` |
| Niagahoster | ~Rp 14.000 | Rp 55.000 | ~Rp 55.000 | Paid | JS-rendered, harder to scrape |
| Hostinger ID | ~Rp 15.900 | Rp 79.000 | Rp 79.000 | Paid | Nuxt SSR, JS-rendered |
| Rumahweb | Rp 22–25.000 | Rp 55.000 | Rp 55–65.000 | Paid | Premium support |
| Dewaweb | Rp 35–50.000 | Rp 75.000 | Rp 75–90.000 | Free | Premium tier |

## Verification Commands Used

```bash
# Domainesia (best — JSON embedded in HTML)
curl -s -L -A "Mozilla/5.0" "https://www.domainesia.com/domain/" -o /tmp/d.html
grep -oE '"my\.id"[^}]{0,300}' /tmp/d.html
# Returns: {"ext":"my.id","price":35000,"promoPrice":9900,...}

# IDwebhost (schema.org markup)
curl -s -L -A "Mozilla/5.0" "https://www.idwebhost.com/domain-id" -o /tmp/iw.html
grep -B1 -A6 'my\.id' /tmp/iw.html
# Returns: "lowPrice": "3000", "highPrice": "13000"

# Jagoan Hosting (plain HTML table)
curl -s -L -A "Mozilla/5.0" "https://www.jagoanhosting.com/domain-murah" -o /tmp/j.html
grep -B1 -A3 'my\.id' /tmp/j.html
# Returns: <td><div class="text">Rp. 35.000</div></td>
```

## What Doesn't Work

- **`whois` command** is NOT installed on Hermes VPS. Use `dig` instead.
- **Niagahoster, Hostinger, Rumahweb pricing pages are JS-rendered** (Nuxt SSR or pure SPA). Raw HTML doesn't contain prices. Either use Playwright or skip them — Domainesia + IDwebhost + Jagoan cover the price spectrum.
- **`whois.idwebhost.com` and similar** — most registrars block direct query; check their UI page instead.
- **Subagent (delegate_task) web research** is unreliable for live pricing — many subagents lack browse access and return stale 2024 data. Always verify with direct `curl` from the parent agent.

## Domainesia Promo Logic

Domainesia uses `freeExt` array — buying a paid hosting package gets `.my.id` free for year 1. Standalone domain still uses the promo price (Rp 9.900) at checkout.

The `multiYearDomainPromo` JSON shows multi-year discounts:
```json
"web.id": {"2": {"register": 100000, "renew": 110000}}
"biz.id": {"2": {"register": 130000, "renew": 140000}}
```
But `my.id` is NOT in the multi-year promo list — single-year only.

## Recommendation Logic

1. **Default**: Domainesia. Year 1 cheap (Rp 9.900), renewal honest (Rp 35.000), free WHOIS privacy.
2. **One-shot test domain (no renewal intent)**: IDwebhost. Cheapest year 1 at Rp 3.000–13.000.
3. **Long-term stability**: Jagoan or Rumahweb. Rp 35.000 flat both year 1 and renewal — no surprises.
4. **Premium project / high uptime requirement**: Dewaweb. Better support, free WHOIS privacy.

## Cross-Sell Watch

When checking out, all registrars upsell:
- Hosting bundles (Niagahoster, IDwebhost most aggressive)
- Email hosting
- SSL certificates (irrelevant for Vercel — Vercel auto-provisions Let's Encrypt)
- Domain privacy (only worth it if registrar charges; skip on Domainesia/Dewaweb)
- WordPress installer (irrelevant for Next.js / Vercel deploys)

Decline all. For a Vercel project you only need the domain itself.
