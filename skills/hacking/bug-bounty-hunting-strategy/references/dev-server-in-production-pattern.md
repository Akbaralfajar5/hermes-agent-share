# Dev Server in Production — Quick-Win Discovery Pattern

## What It Is

Web apps deployed with their development server (Vite, Webpack Dev Server, Next.js dev mode) running in production instead of a static/production build. This exposes:

- **Full source code** (raw `.jsx`, `.tsx`, `.vue` files)
- **Source maps** (inline or external)
- **HMR (Hot Module Replacement)** websocket endpoint
- **Server filesystem paths** (in source map `fileName` annotations)
- **Internal API endpoints** hardcoded in source
- **Environment variables** referenced via `import.meta.env.*` or `process.env.*`

## Severity

Typically **Critical** (Information Disclosure leading to further exploitation) or **High** depending on what the source reveals.

## Detection (30 seconds, curl only)

```bash
# Step 1: Check HTML for dev-server markers
curl -s "https://target.com/" | grep -i "vite\|@react-refresh\|webpack-dev\|__next.*development\|hot-update"

# Step 2: If Vite detected, try reading raw source
curl -s "https://target.com/src/main.jsx"       # or .tsx
curl -s "https://target.com/@vite/client"
curl -s "https://target.com/@react-refresh"

# Step 3: Check API health endpoint (often exposed alongside)
curl -s "https://target.com/api/health"

# Step 4: .env existence (403 ≠ 404 = file exists)
curl -sI "https://target.com/.env" | grep "HTTP"
```

## Fingerprints by Framework

| Framework | Dev-mode markers in HTML |
|-----------|--------------------------|
| **Vite** | `/@vite/client`, `/@react-refresh`, `<script type="module" src="/src/main.jsx">` |
| **Webpack Dev** | `__webpack_hmr`, `webpack-dev-server`, `/sockjs-node/` |
| **Next.js dev** | `/_next/static/development/`, `__NEXT_DATA__` with `"buildId":"development"` |
| **Nuxt dev** | `/_nuxt/hmr/`, `/__webpack_hmr` |
| **Create React App** | `webpackHotDevClient`, `react-dev-utils` |

## What to Extract Once Confirmed

1. **All source files** — spider `/src/` recursively (Vite serves them as-is)
2. **Source maps** — base64-decoded from `//# sourceMappingURL=data:...` in served files
3. **API endpoints** — grep source for `fetch(`, `axios.`, `/api/`, `baseURL`
4. **Contract addresses** — grep for `0x[a-fA-F0-9]{40}`
5. **Environment variable names** — grep for `import.meta.env.VITE_` or `process.env.`
6. **Internal paths** — `fileName` in source annotations reveals server directory structure

## Real-World Example: paddock.games (Jul 2026)

- `GET /src/main.jsx` → 200, full React source, reveals path `/var/www/js/HorseRaceRobinHood/frontend/src/main.jsx`
- `GET /@vite/client` → 200, HMR client running
- `GET /api/health` → 200, exposes 9 internal microservice names (wallet-manager, payment-manager, race-manager, etc.)
- `GET /.env` → 403 (exists but blocked by Cloudflare rule)
- Contract address from page: `0x845d...38b9`

## Report Template

**Title:** Production Environment Running Development Server — Full Source Code Exposure

**Impact:**
- Complete source code disclosure of frontend application
- Internal API endpoints and service architecture revealed
- Server filesystem path disclosure (`/var/www/...`)
- Potential extraction of hardcoded secrets/API keys from source
- Attacker can map full attack surface for further exploitation

**Steps to Reproduce:**
1. Navigate to `https://target.com/`
2. Observe `<script type="module" src="/src/main.jsx">` in page source
3. Access `https://target.com/src/main.jsx` — full source returned
4. Access `https://target.com/@vite/client` — Vite HMR client confirmed

**Recommendation:** Deploy a production build (`vite build`) behind a static file server or CDN. Never expose the Vite dev server to the internet.

## Pitfalls

- Some SPAs return 200 for ALL paths (client-side routing) — check the Content-Type and actual body, not just status code. A 200 returning `index.html` for `/src/main.jsx` is NOT a source leak; a 200 returning actual JavaScript IS.
- Cloudflare may block `.env` (403) but still serve everything else — the WAF rule is path-specific, not comprehensive.
- Dev-server uptime in `/api/health` resets on restart — small uptime = recently restarted = maybe they noticed.
