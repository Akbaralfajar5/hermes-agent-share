---
name: vercel-operations
description: Operate Vercel projects from the terminal — list projects, restore source from a deployed app when the local copy is missing, deploy via CLI with a token, and handle common quirks. Use when working with any *.vercel.app project.
---

# Vercel Operations

Class-level skill for Vercel-hosted projects. The user runs many sites on Vercel (seminar-deck, my-app, my-project, my-project, my-site, etc.) and the local source is not always present, so most workflows start with "find the project, find the deployment, then either edit locally and redeploy, or recover the source first."

## When to load
- User asks to modify, audit, or redeploy any `*.vercel.app` site.
- A change is requested for a project whose source is not in `~`.
- Need to inspect what's actually live in production vs. local.

## Auth
Token lives in memory (`Vercel token: vcp_...`). Always set it as `VERCEL_TOKEN` env var for the call only — never echo it back to chat.

```bash
export VERCEL_TOKEN="vcp_..."  # from memory
```

CLI auth: `vercel deploy --token "$VERCEL_TOKEN"` works without `vercel login`. The CLI is already installed globally on this VPS — call `vercel` directly, NOT `npx vercel@latest` (npx cold-start regularly exceeds the 60s tool timeout).

## Common API endpoints
All require `Authorization: Bearer $VERCEL_TOKEN`.

- `GET /v9/projects?limit=100` — list projects (name + latestDeployments).
- `GET /v9/projects/<name>` — project metadata (id, aliases, framework, ssoProtection, latest production deploy id).
- `GET /v6/deployments?projectId=<id>&limit=N&target=production` — recent deployments.
- `GET /v6/deployments/<dpl_id>/files` — file tree of a deployment (returns names + uids).
- `GET /v7/deployments/<dpl_id>/files/<uid>` — raw contents of one file. **Returns JSON wrapping a base64 blob in `.data`** even when `encoding` field is null. Always base64-decode.

## Restore source from a deployed Vercel app
Critical workflow when the user wants to edit a site whose source isn't on disk. See `references/restore-from-deployment.md` for the full recipe and a reproducible Python decoder. Summary:

1. Find project: `GET /v9/projects?limit=100` → grep by name.
2. Get latest production deploy id: `GET /v6/deployments?projectId=<id>&target=production`.
3. Walk file tree: `GET /v6/deployments/<dpl_id>/files`.
4. For each file uid, fetch and base64-decode `.data` from `GET /v7/deployments/<dpl_id>/files/<uid>`.
5. Write to a fresh local dir (e.g. `~/<project-name>/`).

Pitfall: even if the response has `"encoding": null`, the body is still base64. Always decode.

## Add a custom domain to a project

```bash
PROJECT_ID="prj_..."  # from GET /v9/projects
curl -s -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "yourdomain.com"}' | python3 -m json.tool
```

If `"verified": true` comes back immediately, Vercel already confirmed ownership (common for apex domains with correct DNS). Then set DNS at the registrar:

- Apex domain (`@`): A record → `76.76.21.21`
- `www` subdomain: CNAME → `cname.vercel-dns.com`

Verify propagation: `dig yourdomain.com A +short` should return `76.76.21.21`. Then `curl -sI https://yourdomain.com` should show `server: Vercel` and HTTP 200.

After adding the domain, redeploy once — Vercel will auto-alias the new domain in the deploy output (`▲ Aliased https://yourdomain.com`).

## Deploy a Next.js project

Two modes — pick based on whether the VPS `~/.npmrc` Tencent mirror is active:

**Full deploy (Vercel builds in cloud — safe when npmrc is clean):**
```bash
cd ~/<project>
export VERCEL_TOKEN="vcp_..."
timeout 240 vercel deploy --prod --yes --no-wait --token "$VERCEL_TOKEN"
```
> Always use `--no-wait` on VPS — without it, CLI blocks until cloud build completes (can hang 10+ min).

**Prebuilt deploy (build locally, upload output — required when npmrc breaks cloud build):**
```bash
cd ~/<project>
export VERCEL_TOKEN="vcp_..."
vercel build --prod          # produces .vercel/output/, NOT just .next/
vercel deploy --prebuilt --prod --token "$VERCEL_TOKEN"
```

⚠️ `--prebuilt` requires `.vercel/output/` from `vercel build`, NOT the `.next/` folder from `npm run build`. Running `npm run build` then `vercel deploy --prebuilt` will fail with "File does not exist" errors.

### Non-blocking deploy with `--no-wait`

The default `vercel deploy --prod` **blocks until the build completes** (or times out at 600s). On Vercel free tier, builds can stay QUEUED for minutes, causing the CLI to hang indefinitely.

**`--no-wait` uploads code and returns immediately** without waiting for the build:
```bash
vercel --token "$VERCEL_TOKEN" --prod --yes --no-wait
```
Output includes the inspect URL and deploy URL. The build continues server-side. Use this when:
- Deploying multiple projects (avoids timeout cascades)
- You don't need to verify the build result in the same command
- Build takes > 2 minutes (common on free tier)

### Parallel deploys cause QUEUE deadlock

**Never deploy > 2 projects simultaneously to the same Vercel account.** The free tier serializes builds — deploying 6 projects at once causes ALL of them to stay QUEUED indefinitely. Deploy sequentially or max 2 at a time with `--no-wait`:
```bash
# Sequential with --no-wait (recommended)
for proj in project-a project-b project-c; do
  cd ~/projects/$proj
  vercel --token "$VERCEL_TOKEN" --prod --yes --no-wait
  sleep 5  # small buffer between deploys
done
```

### Check deployment status via API

```bash
export VERCEL_TOKEN="vcp_..."

# Get project ID
pid=$(curl -s "https://api.vercel.com/v9/projects/<name>" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")

# Get latest deployment state
curl -s "https://api.vercel.com/v6/deployments?projectId=$pid&limit=1" \
  -H "Authorization: Bearer $VERCEL_TOKEN" | python3 -c "
import sys,json
d=json.load(sys.stdin)
dep=d['deployments'][0]
print('State:', dep.get('readyState'))
print('URL:', dep.get('url'))
"
```

States: `QUEUED` → `BUILDING` → `READY` | `ERROR`

When the project is already linked (it usually is after first deploy), the CLI auto-detects `your-team/<name>` and skips the setup prompts.

## Adding a custom domain via API

```bash
curl -s -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "yourdomain.com"}'
```

- Apex domains (`yourdomain.com`) need an **A record → 76.76.21.21** at the registrar.
- `www` subdomain needs **CNAME → cname.vercel-dns.com**.
- If DNS is already correct, the response will include `"verified": true` immediately.
- After adding, Vercel auto-aliases the domain on the next production deploy.
- Verify propagation: `dig yourdomain.com A +short` should return `76.76.21.21`.

## Deploy a Next.js project (source available)

When source is available locally, build and deploy directly:

```bash
cd ~/<project>
export VERCEL_TOKEN="vcp_..."
timeout 240 vercel deploy --prod --yes --token "$VERCEL_TOKEN"
```

`--yes` skips all interactive prompts. CLI auto-detects linked project from `.vercel/project.json`.

> ⚠️ **my-app exception**: `~/.npmrc` Tencent mirror breaks Vercel's remote build for that project — use `--prebuilt` for my-app only. Other projects (my-site, etc.) use direct deploy.

## Deploy a static project
For single-file or static asset projects, drop a `vercel.json` with route fallback to `index.html`, then deploy. Template: `templates/static-vercel.json`.

## Add a custom domain via API

```bash
curl -s -X POST "https://api.vercel.com/v10/projects/$PROJECT_ID/domains" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "yourdomain.com"}'
```

After adding, set DNS at registrar: A record `@` → `76.76.21.21`, CNAME `www` → `cname.vercel-dns.com`. Verify propagation with `dig yourdomain.com A +short`.

## Verify a deploy
After `Ready`, curl the production alias and grep for the change:
curl -s "https://<name>.vercel.app/" | grep -A1 "<expected new content>"
```

If the project has `ssoProtection.deploymentType = "all_except_custom_domains"`, preview URLs (`<name>-<hash>-your-team.vercel.app`) require login but the production alias `<name>.vercel.app` is public. Always verify against the production alias, not the deploy hash URL.

## Pitfalls
- **Content/text changes — always grep full source tree**: When translating, renaming text, or doing bulk content updates, grep the ENTIRE `src/` directory for common words from the old content. Don't rely on checking only "main" component files. Missed strings hide in section subtitles, CTA headings, contact taglines, and inline JSX text. Pattern: after editing, run `grep -rn "keyword1\|keyword2\|keyword3" src/` for every distinctive word from the old language/content. This caught 4 missed Indonesian strings in a portfolio translation pass that would have shipped to production.
- `npx vercel@latest` cold-start > 60s on this VPS — use the installed `vercel` binary directly.
- `vercel deploy --token "$VERCEL_TOKEN"` fails with "No existing credentials found" if the env var isn't exported first. Always `export VERCEL_TOKEN="..."` before calling `vercel`. The `--token` flag alone is not sufficient on this VPS setup.
- **write_file over patch for TSX/TS with JSX**: patch is fragile on files with complex JSX structure. Multiple sequential patches on the same file almost always corrupt it (missing closing braces, merged blocks, orphaned JSX). Rule of thumb: if a file needs more than 2 patch calls in one session, switch to `write_file` with full content. This fired on `layout.tsx`, `products.ts`, and `ProductCard.tsx` in the same session — all required full rewrites to recover.
- **siteSettings.ts duplicate-block bug**: when patching a large object literal like `defaultSettings` with an `old_string` that starts at the object declaration (`export const defaultSettings: SiteSettings = {`), the patch tool can append the new block while leaving the old content intact — resulting in two `defaultSettings` objects in the same file (the second one is orphaned code outside any export, causing TS errors). Detection: build fails with `';' expected` errors on lines that look like valid object keys. Fix: read the full file, find the orphaned block (starts right after the first `};`), delete it with a targeted patch. Prevention: use `write_file` for full rewrites of large config objects instead of patching the opening line.
- **patch on partial-read files is dangerous**: if a file was read with `offset/limit` pagination (not full view), do NOT use `patch` — the tool warns `"was last read with offset/limit pagination"`. Re-read the full file first or use `write_file` with complete content. Ignoring this warning causes silent corruption where closing braces get merged or blocks disappear.
- **patch + old_string containing closing braces/brackets is fragile**: when old_string ends with `}` or `],` that also appears elsewhere in the file, the match is ambiguous. Add 2–3 lines of surrounding context to make it unique, or switch to `write_file`. This fired multiple times in the my-site session (layout.tsx, products.ts both required full rewrites after patch corruption).
- **Escape-drift in patch strings**: when old_string/new_string contain quote characters, do NOT backslash-escape them — pass raw `"` characters. Backslash-escaped quotes (`\"`) cause "escape-drift detected" errors and the patch is rejected.
- Vercel files API returns base64 even when `encoding` is null/missing. Don't trust the field.
- **Tencent npm mirror in `~/.npmrc` breaks Vercel cloud build** — three fixes (pick one):
  1. **Prebuilt deploy** (legacy): `vercel build --prod` locally then `vercel deploy --prebuilt --prod`.
  2. **Lockfile fix** (preferred): Create `.npmrc` in project root with `registry=https://registry.npmjs.org/`, then replace Tencent URLs in `package-lock.json`:
     ```bash
     cd ~/<project>
     echo 'registry=https://registry.npmjs.org/' > .npmrc
     sed -i 's|http://mirrors.tencentyun.com/npm/|https://registry.npmjs.org/|g' package-lock.json
     ```
     Then normal `vercel deploy --prod --yes --token "$VERCEL_TOKEN"` works. The lockfile fix is permanent as long as `npm install` is run with the local `.npmrc` present. If `npm install` is run without it, Tencent URLs reappear from the global `~/.npmrc`.
  3. **Global registry reset + lockfile regen** (nuclear): Fix the global npm config, delete lock files, and regenerate:
     ```bash
     npm config set registry https://registry.npmjs.org
     cd ~/<project>
     rm -rf node_modules package-lock.json yarn.lock
     npm install
     ```
     This permanently fixes the global config. Use when the Tencent mirror was set via `npm config` (not just `~/.npmrc` file).
  - **`yarn.lock` also contains Tencent mirror URLs**: If `yarn.lock` exists alongside or instead of `package-lock.json`, Vercel will use yarn — and yarn lock files generated on a Tencent-mirror machine will have `mirrors.tencentyun.com` in the `resolved` fields. Vercel's yarn install fails with `getaddrinfo ENOTFOUND mirrors.tencentyun.com`. **Always delete `yarn.lock` too** when fixing Tencent mirror issues, or regenerate it after fixing the registry. If the project doesn't strictly need yarn, removing `yarn.lock` forces Vercel to use npm.
- `ssoProtection` blocks deploy hash URLs but not the production alias. Test against the alias.
- **Vercel token expiry**: `vercel deploy` fails with *"The specified token is not valid. Use `vercel login` to generate a new token."* when the stored token expires. On headless VPS, `vercel login` is interactive (opens browser) and hangs/timeout. Fix: user must generate a new token from https://vercel.com/account/tokens and update the memory entry. Alternatively, run `vercel login` from a local machine with a browser and copy the resulting `~/.vercel/auth.json` to the VPS. When deploying for the user, detect this error early and report it — don't retry.
- Tokens never go into chat verbatim — reference by memory entry, set as env var inline.
- **`sharp` as devDependency breaks Vercel cloud build**: if `sharp` (or any native module) is installed via `npm install sharp --save-dev`, Vercel's remote build will fail with `npm error network` during `npm install`. Fix: use `vercel build --prod` locally then `vercel deploy --prebuilt --prod`. Remove `sharp` from `package.json` after use if it was only needed for one-off image processing.
- **`favicon.ico` cached aggressively by Vercel edge**: Even with `cache-control: public, max-age=0, must-revalidate`, Vercel's CDN serves stale `favicon.ico` after deploy. The file on the server is correct but the CDN returns the old one. **Fix: rename the file** (e.g. `favicon-v2.ico`) and update all references in `layout.tsx` (metadata `icons` + `<link>` tags). A new filename bypasses the edge cache since Vercel treats it as a distinct asset. This fired on my-site (Jun 2026) — local favicon.ico was the correct logo but CDN served old Vercel default (256x256, 89% dark pixels). After rename to `favicon-v2.ico` + `git push`, new file served immediately. Old `favicon.ico` still cached — leave it or replace with identical content. Browser cache is a separate layer — user also needs hard refresh (`Ctrl+Shift+R`) or incognito to see new favicon.
- **ESLint `<img>` warnings block Vercel build**: Next.js ESLint rules treat `<img>` as an error by default. If you use `<img>` tags (e.g. for logo images in Navbar/Footer), add `eslint: { ignoreDuringBuilds: true }` to `next.config.mjs` to prevent build failure. Alternatively, switch to `next/image` — but for simple logo/favicon use cases, ignoring is faster.
- **`--no-wait` flag for low-RAM VPS**: `vercel --prod --yes` without `--no-wait` hangs indefinitely on low-RAM VPS because the CLI blocks waiting for cloud build completion. Always use `vercel --token "$TOKEN" --prod --yes --no-wait` — uploads code and returns instantly.
- **Free tier concurrent build queue**: Vercel free tier limits concurrent builds. Deploying 6+ projects simultaneously causes ALL to sit in QUEUED state indefinitely. **Deploy in batches of 2-3, wait 2-3 minutes between batches.** If builds get stuck QUEUED, cancel them via API and redeploy sequentially:
  ```bash
  # Check state
  curl -s "https://api.vercel.com/v6/deployments?projectId=$PID&limit=1" -H "Authorization: Bearer $TOKEN"
  # readyState: QUEUED | BUILDING | READY | ERROR
  ```
- **Prebuilt is the fastest path**: When local build succeeds, `vercel build --yes` + `vercel --prebuilt --prod --yes` is always faster than cloud deploy. Use it by default for projects that build locally.
- **npm "Exit handler never called" on Vercel cloud build**: Distinct from the Tencent mirror issue. Vercel's npm install fails with `npm error Exit handler never called!` and `npm error This is an error with npm itself`. This is a generic npm/Vercel infra race condition — NOT a code problem. Local `npm run build` succeeds fine. Fix: use prebuilt deploy:
  ```bash
  rm -rf .vercel/output .next   # clean BOTH — stale .next chunks cause "File does not exist" errors
  vercel build --prod --yes
  vercel deploy --prebuilt --prod --yes --no-wait
  ```
  **Critical:** Only deleting `.vercel/output` is not enough — `vercel build` reuses the existing `.next` directory, which may contain stale chunk references from a previous build with different dynamic imports or code-splitting. Always `rm -rf .next` too. Happened on portfolio-site project (May 2026) with no Tencent mirror involvement.

## Manually alias a domain to a deployment

When a deploy succeeds but the domain still points to an old deployment:

```bash
VERCEL_TOKEN="..." vercel alias set <deploy-url> <domain>
# Example:
VERCEL_TOKEN="..." vercel alias set https://portfolio-site-m98zq6md1-your-team.vercel.app portfolio.example.id
```

Note: the first arg must be a deployment URL (not a domain). The second arg is the target domain. The alias command fails if you pass a deployment URL as the target ("chosen alias is a deployment URL").
- **Next.js context providers must NOT throw during SSR**: `createContext(undefined)` + `if (!ctx) throw new Error(...)` breaks static prerendering. Always use `createContext({defaultValue})` with a real default object. This is the #1 cause of "Export encountered errors" in Next.js 14 App Router projects.
- **Tailwind v3 vs v4 CSS syntax**: v3 uses `@tailwind base; @tailwind components; @tailwind utilities;`. v4 uses `@import "tailwindcss";`. `create-next-app@14` generates v3 — don't mix v4 syntax.
- **`vercel build` without `--prod` builds for preview env**: Running `vercel build` (no flag) produces `.vercel/output` targeting "preview". Then `vercel --prebuilt --prod` fails with `"--prebuilt" option was used with the target environment "production", but the prebuilt output found in ".vercel/output" was built with target environment "preview"`. Fix: always use `vercel build --prod --yes` before `vercel --prebuilt --prod`.

## Support files
- `references/restore-from-deployment.md` — full source-restore recipe, Python decoder snippet, walking file trees with subdirectories.
- `references/instagram-video-download.md` — download IG Reels via yt-dlp, copy to `public/videos/`, embed with HTML5 `<video>` in Next.js.
- `references/nextjs-14-build-fixes.md` — common Next.js 14 build failures: context provider SSR crashes, Tailwind v3/v4 syntax mismatch, ESLint blocks, TypeScript strict errors, SIGBUS on low-RAM VPS, bulk scaffolding pattern, lucide-react missing icons, subagent file corruption, dark/light mode ThemeProvider pattern.
- `templates/static-vercel.json` — minimal `vercel.json` for static single-file deploys with cleanUrls + SPA fallback.
