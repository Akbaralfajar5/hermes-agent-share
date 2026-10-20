# DNS Setup: Domainesia → Vercel — Field-by-Field & Troubleshooting

## IDWebHost-Specific Notes (member.idwebhost.com)

If the user bought from IDWebHost instead of Domainesia, these quirks apply:

**Nameserver change requires IP addresses.** When changing nameservers at IDWebHost, the UI demands IP addresses alongside hostnames:

| Nameserver | IP Address |
|---|---|
| ns1.vercel-dns.com | 198.51.44.13 |
| ns2.vercel-dns.com | 198.51.45.13 |

**Hostname field**: If `@` is rejected, try leaving blank or using `.` (dot). IDWebHost auto-converts `@` to the full domain on save — this is normal and not a bug.

---

Practical recipe for pointing a Domainesia-registered `.my.id` / `.web.id` (or any
ccTLD) to a Vercel project, plus diagnosing the 30+ minute "DNS not propagating"
class of issues.

---

## 1. Domainesia DNS Panel — Field Reference

After buying the domain, go to **my.domainesia.com → Domain → [domain] → Manage DNS** (sometimes labeled "DNS Management").

The form has these columns:

| Column | What to put | Notes |
|---|---|---|
| **Host Name** | `@` for root domain, or `www` for subdomain | If form rejects `@`, **leave it blank** — same effect. Some panels show literal `@` after save, some show empty. |
| **Record Type** | `A`, `CNAME`, `MX`, `TXT`, etc. | Pick from dropdown. |
| **Address** | The target value (IP for A, hostname for CNAME) | For Vercel: `76.76.21.21` (A) or `cname.vercel-dns.com` (CNAME). |
| **Priority** | **LEAVE BLANK** for A and CNAME | Priority is only used for MX records. If form forces a number, put `0`. |

**DNSSEC management** section: leave untouched. Not needed for Vercel-hosted apps and adds complications if misconfigured.

### Standard Vercel records (what to add)

```
Host Name   Record Type   Address                   Priority
(empty)     A             76.76.21.21               (empty)
www         CNAME         cname.vercel-dns.com      (empty)
```

Hapus dulu parking records bawaan Domainesia (biasanya A → IP server Domainesia) sebelum tambah yang baru, biar tidak konflik.

---

## 2. Vercel Side — Add Domain to Project

```bash
cd ~/<project-dir>
npx vercel domains add <domain.my.id> --token <VERCEL_TOKEN>
npx vercel domains add www.<domain.my.id> --token <VERCEL_TOKEN>
```

Expected output (DNS not propagated yet):

```
Success! Domain X added to project Y.
WARNING! This domain is not configured properly. To configure it...
  a) Set the following record on your DNS provider: A X 76.76.21.21
  b) Change nameservers to ns1/ns2.vercel-dns.com
  Intended Nameservers    Current Nameservers
  ns1.vercel-dns.com      nsx1.domainesia.com    ✘
```

The ✘ is normal at this stage. We're using **option (a)** — keep Domainesia nameservers, just add the A/CNAME records. Don't switch nameservers unless you really want Vercel managing DNS.

---

## 3. Verify Propagation

Always check **at three layers** before assuming DNS works:

```bash
# Layer 1 — TLD nameserver (knows who's authoritative)
dig +short NS yourdomain.my.id @b.dns.id
# Expected: nsx1.domainesia.com / nsx2.domainesia.com

# Layer 2 — Authoritative nameserver (the actual records you set)
dig +short yourdomain.my.id @nsx1.domainesia.com
dig +short www.yourdomain.my.id @nsx1.domainesia.com
# Expected: 76.76.21.21 and cname.vercel-dns.com

# Layer 3 — Public resolver (caches; slowest to update)
dig +short yourdomain.my.id @8.8.8.8
dig +short yourdomain.my.id @1.1.1.1
# Expected: 76.76.21.21
```

If layer 2 returns empty or `REFUSED`, **records weren't actually saved at the registrar** — the public resolver will never have anything to cache. Fix at registrar first.

If layer 2 has the records but layer 3 is empty, just wait — public propagation takes 5–30 min usually, occasionally up to 1–2 hours.

---

## 4. Vercel Domain Inspect

```bash
cd ~/<project-dir>
npx vercel domains inspect <domain.my.id> --token <VERCEL_TOKEN>
```

Shows whether Vercel sees the records yet. SSL provisioning starts automatically once Vercel detects correct A record at any public resolver.

> ⚠️ **`vercel domains verify` does NOT exist** in current Vercel CLI. Trying it returns `Error: Invalid number of arguments. Usage: vercel domains ls`. There is no manual re-verification — Vercel auto-polls in the background. Just `inspect` to read status, or wait. If you need to nudge it, remove and re-add the domain.

---

## 5. Common Failures & Fixes

### "An issue was encountered while updating the DNS records. Please contact support."

Domainesia panel error when saving DNS records. Causes:

- Conflicting record already present (e.g. existing A record at root). **Delete old parking records first.**
- Domain not fully provisioned yet — try again 5 minutes after purchase.
- KTP/identitas verification still pending in some `.id` family TLDs (`.web.id` requires KTP).

Workaround if it keeps failing:
1. Refresh page, re-login, retry.
2. Try one record at a time (some panels choke on bulk).
3. Submit support ticket via Domainesia chat (response < 30 min usually).

### "User says records are saved" but layer-2 dig shows empty

User might have entered records in form but **not clicked the final Save / Apply Changes** button outside the form. Common UX trap.

Diagnostic move: ask for screenshot of the DNS management page showing the saved records list. Don't trust verbal "sudah saya save" — verify visually.

**When `vision_analyze` / `browser_vision` errors out** (e.g. `invalid model 'claude-sonnet-4.5': use provider/model_id format`), fall back to OCR:

```bash
# Tesseract is preinstalled at /usr/bin/tesseract
tesseract /home/ubuntu/.hermes/image_cache/img_<hash>.jpg /tmp/ocr_out -l eng
cat /tmp/ocr_out.txt
```

Tesseract reads the screenshot well enough to confirm whether the DNS records list is empty (form-only) or populated. In the May 2026 session, OCR revealed the user's panel still showed only headers + empty form — they hadn't actually saved anything yet, despite saying they had.

### REFUSED status from authoritative NS

```
;; ->>HEADER<<- opcode: QUERY, status: REFUSED
```

Means the nameserver doesn't recognize the zone yet. Either:
- Domain is brand new (< 5 min after purchase) — registrar hasn't pushed zone to NS yet.
- Records weren't saved in panel.

Wait 10 min then re-test. If still REFUSED after 30 min with records visible in panel, ticket support.

### PANDI RDAP returns 404

```bash
curl -s "https://rdap.pandi.id/domain/yourdomain.my.id" | python3 -m json.tool
# {"errorCode": 404, ...}
```

Brand-new `.my.id` domains take up to 1 hour to appear in PANDI's RDAP. Doesn't block DNS from working — just means whois lookup is delayed.

---

## 6. Background DNS Monitor Cron Pattern

Useful when user is buying domain and goes offline — fire a cron that checks every 5 min and notifies when DNS is live + SSL ready.

```python
# cronjob action=create
{
  "action": "create",
  "name": "DNS Monitor <domain>",
  "schedule": "every 5m",
  "repeat": 12,
  "enabled_toolsets": ["terminal"],
  "prompt": """
Check if DNS records for <domain> propagated.

1. dig +short <domain> @8.8.8.8  → must return 76.76.21.21
2. dig +short www.<domain> CNAME @8.8.8.8  → must return cname.vercel-dns.com
3. curl -sI https://<domain>  → check HTTPS

If A record returns 76.76.21.21:
- Run: cd ~/<project> && npx vercel domains inspect <domain> --token <TOKEN>
- Send ONE message: "✅ <domain> live, SSL active. HTTP code: <code>"

If NOT propagated:
- Don't message user. Wait next cron tick.
"""
}
```

`repeat: 12` × 5min = 1 hour max polling, plenty for typical Domainesia → public propagation.

---

## 7. Bonus Domain Trap (`.web.id` Free with `.my.id`)

Domainesia and other Indonesian registrars sometimes bundle a free `.web.id`
with `.my.id` purchases. Keep these straight:

- The bonus `.web.id` is **not auto-renewed for free** — user gets one year free,
  then full renewal price (~Rp 55.000/year at Domainesia).
- Both domains can be pointed to **different Vercel projects** — DNS records are
  identical (`A → 76.76.21.21`, CNAME → `cname.vercel-dns.com`); routing happens
  at Vercel based on which project each domain is added to.
- Recommend user use bonus for a secondary brand (e.g. main `.my.id` for app A,
  bonus `.web.id` for app B), not as a redirect dummy unless they really want it.

---

## 8. Vercel Routing With Identical DNS for Multiple Domains

A common confusion: "How can DNS be the same on two domains but route to different apps?"

Answer: Vercel's edge routes based on the **Host header** of the incoming HTTP request, not based on DNS-level routing. Both domains resolve to the same Vercel IP (`76.76.21.21`), but each Vercel project's `Settings → Domains` config says "I own host X." When request arrives, Vercel reads `Host: app1.my.id`, looks up which project claims that host, and serves it.

So the workflow for two domains → two projects is:
1. Both domains: same A + CNAME records pointing to Vercel.
2. Project A: `vercel domains add app1.my.id`.
3. Project B: `vercel domains add app2.web.id`.
4. Done. Each domain serves its own project.

If you accidentally add the same domain to two projects, the second `add` fails with conflict — Vercel enforces uniqueness.

---

## 9. "Server Is Live But User Can't Open On Their Device"

Classic last-mile case: dig from your VPS shows the A record everywhere, HTTPS returns 200, SSL is valid — but the user reports the URL doesn't load on their phone. Don't assume it's broken; **server-side and client-side are independent**.

**Server-side checklist (you do this once):**

```bash
# All three must pass before blaming the client
dig +short <domain> @8.8.8.8                            # 76.76.21.21
dig +short <domain> @1.1.1.1                            # 76.76.21.21
curl -sIL --max-time 10 https://<domain>/ 2>&1 | head -3  # HTTP/2 200
echo Q | timeout 10 openssl s_client -connect <domain>:443 -servername <domain> 2>&1 | grep -E "subject=|issuer=|Verify"
# subject=CN = www.<domain>
# issuer=...Let's Encrypt...
# Verify return code: 0 (ok)
```

If all green → **issue is on the user's device, not your stack.**

**Client-side fixes to suggest, in order of effort:**

1. **Toggle airplane mode 5 sec** → on/off. Resets device DNS cache cheapest.
2. **Switch network**: if on WiFi, use mobile data (or vice versa). Some Indonesian ISPs cache DNS aggressively.
3. **Open in Incognito/Private tab** → bypasses browser cache + service worker.
4. **Type full URL with `https://`** explicitly — autocomplete may surface a stale entry.
5. **Visit https://1.1.1.1/help** → confirms whether device is using Cloudflare DNS (which propagates fast).
6. **Try `https://www.<domain>`** → both `@` and `www` resolve, sometimes one works first.
7. **Test from another device / network** to isolate device vs network.

**Curl quirk** (caught me in this session): `curl --max-time 10 https://<domain>` sometimes hangs with `error:0A000126:SSL routines::unexpected eof while reading` even though the server is fine. Cause: TLS handshake mid-flight when SSL cert is provisioning OR a transient edge issue. **Use `wget --spider -S` or `curl -sIL` (with `-L`)** as a fallback — they recover where bare `curl -sI` chokes.

---

## 10. End-to-End Post-Deploy QA Recipe

When user says "test dulu sendiri sama kamu" / "tes semuanya dulu" before they trust the deploy, run this systematically. Don't just open homepage and call it done.

**Phase 1: Network/protocol layer**

```bash
# Performance budget (TTFB < 1s for SSR Next.js page is acceptable)
curl -w 'DNS: %{time_namelookup}s | TLS: %{time_appconnect}s | TTFB: %{time_starttransfer}s | Total: %{time_total}s | Code: %{http_code}\n' -o /dev/null -s https://<domain>
curl -w '...same...' -o /dev/null -s https://<domain>/login
curl -w '...same...' -o /dev/null -s https://<domain>/<deepest-page>

# Security headers
curl -sI https://<domain> | grep -iE "strict-transport|x-frame|content-security|x-content-type"

# www subdomain
curl -sIL --max-time 10 https://www.<domain> | head -8
```

**Phase 2: Auth + protected routes via browser**

For apps with auth, do this dance:

1. Browser → `<domain>/login` → snapshot
2. `browser_type` (NOT `browser_press`) into email + password fields. **Camoufox is unreliable for keypress on password inputs** — use `browser_type` or set value via JS:

   ```javascript
   const pw = document.querySelector('input[type=password]');
   const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
   setter.call(pw, 'thePassword');
   pw.dispatchEvent(new Event('input', {bubbles: true}));
   ```

3. Click submit, then `browser_console` to check `location.pathname` and `document.cookie.includes('sb-access-token')`.
4. If browser submit fails despite form being right, **fall back to API call directly** to confirm the auth flow itself works (eliminates frontend-vs-backend ambiguity):

   ```bash
   curl -s -X POST https://<domain>/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"...","password":"..."}' | python3 -m json.tool
   ```

   If API returns `success: true` but browser submit fails → frontend issue (likely camoufox-only). User on real device won't hit it. Note the discrepancy in your report so user knows.

5. With session cookie set (either via successful submit or manually), navigate every protected route and dump `document.body.innerText.substring(0, 500)` per route to verify content loads, not just status code.

**Phase 3: Route inventory**

Match `~/<project>/src/app/` directory listing against sidebar nav text. Common pitfall: nav says "Pakai Bahan" but the actual folder is `pakai/` not `pakai-bahan/`. Don't guess paths from labels — list the directory:

```bash
ls ~/<project>/src/app/
```

**Phase 4: Report shape**

User who says "tes dulu sendiri" expects a comprehensive checklist response, not a casual "all good." Use a status table covering:

- DNS (root, www, both resolvers)
- SSL cert (issuer, validity)
- HTTPS response code per route
- Auth flow (both user roles if applicable)
- Each protected page renders expected content
- Performance numbers (TTFB)
- Sidebar navigation completeness
- Compared against pre-existing `*.vercel.app` URL: feature parity verified

End with a single-line verdict: "Semua jalan normal, [domain] siap dipakai."
