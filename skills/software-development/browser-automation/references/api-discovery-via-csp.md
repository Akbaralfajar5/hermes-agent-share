# API Discovery via CSP Headers

## Technique
Extract hidden API endpoints from Content-Security-Policy headers. CSP `connect-src` directives list all domains the SPA is allowed to connect to — including backend APIs.

## Example: Pioneer.ai (June 2026)
```bash
curl -sI "https://agent.pioneer.ai/" | grep content-security-policy
# → connect-src ... https://db.pioneer.ai wss://db.pioneer.ai ...
```
This revealed pioneer.ai's Supabase backend at `db.pioneer.ai` — not obvious from the frontend.

## Anon Key Extraction
1. Download SPA JS bundle: `curl -s "https://SITE/assets/index-*.js"`
2. Search for `createClient` calls: `grep -oP 'createClient.*?["\'](.+?)["\']'`
3. Look for non-JWT publishable keys (Supabase v2): `sb_publishable_[A-Za-z0-9_-]+`
4. Alternative: search for `supabaseUrl` and `supabaseKey` assignments near each other

## When to Use
- SPA with no visible API calls in Network tab
- Supabase-backed apps hiding their project reference
- Finding auth endpoints for headless automation
