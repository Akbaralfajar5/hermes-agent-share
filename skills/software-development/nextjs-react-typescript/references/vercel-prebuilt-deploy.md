# Vercel Pre-built Deployment Pattern

## When to Use
When Vercel's remote `npm install` fails with internal npm errors (common in 2025). This bypasses remote build entirely.

## Prerequisites
- Vercel CLI installed: `npm install -g vercel`
- Vercel token from https://vercel.com/account/tokens
- Node.js 20+ locally (or at least 18 for building, but set engines to 20.x for Vercel)

## Step-by-Step

```bash
# Set token (or pass inline with each command)
export VERCEL_TOKEN=vcp_xxxxx

# First time: link to Vercel project
cd my-project
vercel pull --yes
# This creates .vercel/ directory with project settings

# Build locally (generates .vercel/output/)
vercel build --prod
# This runs `next build` and packages output for Vercel

# Deploy pre-built (no remote npm install!)
vercel deploy --prebuilt --prod --yes
# Uploads .vercel/output/ directly — fast, reliable
```

## package.json Requirements

```json
{
  "engines": {
    "node": "20.x"
  }
}
```

- Do NOT use `">=18.0.0"` — Vercel warns about auto-upgrade
- Do NOT use `"18.x"` — discontinued on Vercel as of 2025
- `"20.x"` is the safe choice

## Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `npm error Exit handler never called!` | npm bug on Vercel build server | Use --prebuilt pattern |
| `Node.js Version "18.x" is discontinued` | Vercel dropped Node 18 | Set engines to "20.x" |
| `No Project Settings found locally` | Missing .vercel/ dir | Run `vercel pull --yes` |
| `Error: Command "npm install" exited with 1` | Same as first — remote npm broken | Use --prebuilt |

## Output Structure

After `vercel build --prod`, the `.vercel/output/` directory contains:
- `static/` — static assets (JS, CSS, images)
- `functions/` — serverless functions (if any SSR pages)
- `config.json` — routing configuration

## Notes
- The `--prebuilt` flag tells Vercel to skip build and use existing `.vercel/output/`
- Build time is local (uses your machine's npm/node), deploy is just upload
- Much faster than remote build for iterative deployments
- Works with any Next.js version (13, 14, 15)
