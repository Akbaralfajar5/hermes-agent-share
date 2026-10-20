---
name: id-domain-registration
description: "Research, compare, and register Indonesian ccTLD domains (.id, .my.id, .web.id, .biz.id, .sch.id, .ac.id) — registrar pricing, availability checks, renewal traps, and DNS setup for Vercel/VPS."
tags: [domain, registrar, indonesia, my.id, dns, vercel, niagahoster, idwebhost, domainesia]
---

# Indonesian ccTLD Domain Registration

When the user wants to buy or compare `.id` family domains (`.my.id`, `.web.id`, `.biz.id`, `.sch.id`, `.ac.id`, `.or.id`, `.id`), this skill covers registrar selection, availability checking, and pitfalls.

## When to Use

- User asks about cheap/best `.my.id` (or any `.id` ccTLD) domain
- User wants to register a custom domain for a Vercel/VPS project
- Need to check if a domain name is available without `whois`
- Need to compare Indonesian registrar pricing
- User wants suggestions for domain naming

## Step 1: Check Availability (No `whois` Needed)

Hermes VPS doesn't have `whois` installed. Use DNS lookup as a proxy — `NXDOMAIN` or no NS records means likely available:

```bash
for d in candidate1 candidate2 candidate3; do
  ns=$(dig +short NS "${d}.my.id" 2>/dev/null | head -1)
  status=$(dig "${d}.my.id" 2>/dev/null | grep -oE "NXDOMAIN|NOERROR" | head -1)
  if [ "$status" = "NXDOMAIN" ]; then
    echo "✅ AVAILABLE: ${d}.my.id"
  elif [ -n "$ns" ]; then
    echo "❌ TAKEN:     ${d}.my.id  (NS: $ns)"
  else
    echo "✅ AVAILABLE: ${d}.my.id  (no NS)"
  fi
done
```

> ⚠️ DNS check is heuristic — domain could be registered but parked without NS. For final confirmation, search on the registrar's checkout page.

## Step 2: Compare Registrar Prices

Don't trust subagent web research — many subagents lack live web access and will return stale 2024 data. Always `curl` registrar pricing pages directly. Pricing data is usually embedded in JSON inside the HTML:

```bash
curl -s -L -A "Mozilla/5.0" "https://www.domainesia.com/domain/" -o /tmp/d.html
grep -oE '"my\.id"[^}]{0,300}' /tmp/d.html
# Look for "extWithPrice" array — has price (regular) + promoPrice
```

For Niagahoster/Hostinger (Nuxt SSR JS-rendered), pricing isn't in raw HTML. Check IDwebhost's `/domain-id` page and Jagoan's `/domain-murah` — both render server-side.

## Registrar Pricing Snapshot (`.my.id`, May 2026)

See `references/id-registrar-pricing-snapshot.md` for the full comparison table verified live. TL;DR:

| Registrar | Year 1 | Renewal | Notes |
|---|---|---|---|
| **Domainesia** ⭐ | Rp 9.900 | **Rp 35.000** | Sweet spot. Free WHOIS privacy. Renewal stable. |
| IDwebhost | Rp 3.000 | ~Rp 55.000 | Cheapest year 1 BUT auto-renew default ON, 18x markup |
| Jagoan Hosting | Rp 35.000 | Rp 35.000 | Fair pricing, transparent |
| Niagahoster | ~Rp 14.000 | ~Rp 55.000 | Promo year 1, 4x renewal hike |
| Rumahweb / Dewaweb | Rp 25–50.000 | Rp 55–90.000 | Premium support, stable pricing |

**Default recommendation: Domainesia** — best year-1-to-renewal ratio, no nasty surprises.

**Bonus domain bundle (verified May 2026):** Domainesia frequently throws in a free `.web.id` when you register a `.my.id`, and vice versa. The bonus is for the FIRST year only — renewal of the bonus follows its own TLD's standard rate (`.web.id` renewal ≈ Rp 55.000). Treat the second domain as a chance to split brand vs. project (e.g. `myapp.example.id` for one app, `myapp.example.id` for a sibling app) — both can live on Vercel with identical DNS records, routing is decided per-project on Vercel's side. Don't waste the bonus on a 301-redirect domain unless you genuinely want one; better to assign each to a different deployable.

## Multi-Year Registration Strategy

Most registrars allow registering 2/3/5 years upfront, BUT the discount picture is nuanced:

- **`.my.id` has NO multi-year promo** at any major registrar checked. Total = year 1 promo price + (subsequent years × renewal price). E.g. Domainesia 2-year: Rp 9.900 + Rp 35.000 = **Rp 44.900**.
- **Other `.id` family TLDs DO have multi-year bundles** at Domainesia (verified in `multiYearDomainPromo` JS object on the domain page):
  - `.id`: 2 years = Rp 298.000 (vs Rp 498.000 without bundle)
  - `.web.id`, `.sch.id`, `.ac.id`, `.or.id`, `.ponpes.id`: 2 years = Rp 100.000
  - `.biz.id`: 2 years = Rp 130.000
- **Per-year price doesn't change with cycle length** at Niagahoster/IDwebhost/Jagoan — checkout just lets you prepay.

**When to suggest multi-year for `.my.id`:** even without discount, it's worth recommending 2-year register upfront for two reasons:
1. **Predictable cost** — user knows total commitment without worrying about renewal price changes.
2. **No annual renewal admin** — avoids forgetting to renew or getting caught by auto-renew traps.

**How to detect multi-year promos in registrar HTML:**

```bash
# Domainesia embeds multi-year deals in JS — grep for the object
grep -oE 'multiYearDomainPromo[^;]*' /tmp/domainesia.html
# Or look for tooltip text:
grep -B2 -A5 "untuk 2 tahun\|2 tahun sekaligus" /tmp/domainesia.html
```

If the TLD doesn't appear in `multiYearDomainPromo`, there's no bundled discount — selling user "2-year package" just means prepaying year 1 + year 2 at standard rates.

## Common Pitfalls

- **Bait-and-switch renewals.** Year 1 promo prices are subsidized; renewals jump 3–18x. Always quote BOTH year 1 AND renewal to user before purchase.
- **Auto-renew default ON.** Niagahoster, IDwebhost, Hostinger toggle this on by default. User must manually opt-out in dashboard or get charged surprise renewal.
- **WHOIS privacy as paid upsell.** Domainesia/Dewaweb include free; Niagahoster/IDwebhost charge separately.
- **PANDI registry cost is ~Rp 50.000/year wholesale** — anyone selling year 1 below this is subsidizing to lock you in. Domainesia at Rp 35.000 renewal is genuinely fair (close to wholesale).

## International Registrars (for .com)

User asked about **domain.com** — it IS ICANN-accredited (legitimate, founded 2000), BUT:
- Year 1: $5.20 (cheap)
- Renewal: **$33.19/year** (among highest of 136 registrars tracked)
- Aggressive upselling, hidden auto-renewal charges

**Better alternatives for .com:**

| Registrar | Year 1 | Renewal | Notes |
|---|---|---|---|
| Cloudflare | $10.46 | $10.46 | Flat pricing, no markup, free WHOIS |
| Porkbun | $10.08 | $11.08 | Transparent, free WHOIS |
| Namecheap | $6.99 | $14.98 | Good UI, frequent promos |
| Spaceship | $2.90 | $10.18 | Cheapest year 1 |

**Rule**: For `.com`, use Cloudflare or Porkbun. For `.my.id`, use Domainesia. Never domain.com or GoDaddy (both have predatory renewals).

## Naming Suggestions

For project domains, prefer:
- **Short** (≤8 chars before `.my.id`) — easy to type on mobile
- **Pronounceable** — works in spoken context (presentation, demo)
- **Avoids hyphens** — hyphens fail when read aloud
- **Memorable acronym** if matches existing brand (e.g. `myapp.example.id` for Pengawasan Mutu Hasil Pertanian)

Length sweet spot: 4–7 characters. Anything over 12 chars + `.my.id` is uncomfortable on mobile.

## Connect Custom Domain to Vercel

After purchase, point domain to Vercel via DNS:

```
# At registrar DNS panel:
Type   Name    Value                    TTL
A      @       76.76.21.21              3600
CNAME  www     cname.vercel-dns.com.    3600
```

Then in Vercel project: **Settings → Domains → Add → enter `yourdomain.my.id`** → Vercel auto-verifies. CLI equivalent:

```bash
cd ~/<project> && npx vercel domains add yourdomain.my.id --token <VERCEL_TOKEN>
```

**Verify at three layers** when troubleshooting:

```bash
dig +short NS yourdomain.my.id @b.dns.id              # TLD knows authoritative NS?
dig +short yourdomain.my.id @nsx1.domainesia.com      # records actually saved?
dig +short yourdomain.my.id @8.8.8.8                  # public resolver caught up?
```

If layer 2 is empty/`REFUSED`, records weren't saved at registrar — fix there first; public resolver will never have anything to cache.

DNS propagation: usually 5–30 min for `.my.id` (PANDI is fast). SSL auto-provisioned by Vercel within 1 minute after DNS verifies.

**Key pitfalls when helping user with DNS panel:**

- **Don't trust verbal "sudah saya save"** — ask for screenshot of the DNS records list. Users often fill the form but miss the final Apply/Save button outside the form, or hit a Domainesia error like "An issue was encountered while updating the DNS records."
- **Domainesia "Host Name" field**: `@` for root, `www` for subdomain. If panel rejects `@`, leave blank (same effect).
- **Priority column**: leave blank for A and CNAME (only used by MX). If form forces a value, put `0`.
- **DNSSEC**: don't touch it. Not needed for Vercel and breaks things if misconfigured.
- **Delete old parking records** at root (`@`) before adding the Vercel A record, or Domainesia rejects with conflict.

For the full field-by-field walkthrough (saved error messages, layer-1/2/3 dig recipe, REFUSED diagnosis, background cron monitor pattern, bonus-domain bundle handling, "two domains same DNS → different Vercel projects" mechanics, **client-side DNS cache fixes when server is live but user's device can't open**, **post-deploy end-to-end QA recipe**, **`vercel domains verify` doesn't exist**), see `references/dns-setup-vercel-domainesia.md`.

## ccTLD Family Quick Reference

| TLD | Use case | Requirements | Domainesia Promo / Renewal |
|---|---|---|---|
| `.my.id` | Personal, hobby, freelancer | None (KTP optional) | Rp 9.900 / Rp 35.000 |
| `.web.id` | Personal/komunitas | KTP scan | Rp 9.900 / Rp 55.000 |
| `.biz.id` | Bisnis kecil/UMKM | KTP + NPWP | Rp 9.900 / Rp 70.000 |
| `.sch.id` | Sekolah resmi | SK Kepsek + surat resmi | Rp 48.900 / Rp 55.000 |
| `.ac.id` | Perguruan tinggi | SK Rektor | Rp 48.900 / Rp 55.000 |
| `.or.id` | Organisasi nirlaba | Akta organisasi | Rp 48.900 / Rp 55.000 |
| `.id` | Premium / komersial | None | Rp 219.900 / Rp 249.000 |

`.my.id` is the easiest entry point — no documents required, anyone can register.

## Linked References & Scripts

- `references/id-registrar-pricing-snapshot.md` — full pricing table snapshot (May 2026) with sources
- `references/dns-setup-vercel-domainesia.md` — Domainesia DNS panel field-by-field, three-layer dig diagnosis, common error messages ("An issue was encountered..."), background cron monitor pattern, bonus-domain bundle handling, **client-side last-mile DNS cache fixes**, **end-to-end post-deploy QA recipe**
- `references/post-deploy-branding-checklist.md` — favicon detection (default-Next.js fingerprinting), PIL-generated multi-size ICO, PWA manifest setup, "icon nya bisa di home screen?" follow-up handling
- `scripts/gen_favicon_flask.py` — runnable PIL script that emits favicon.ico (multi-size) + apple-touch-icon.png + icon-192.png + 512px preview. Customize colors and shape at top.
