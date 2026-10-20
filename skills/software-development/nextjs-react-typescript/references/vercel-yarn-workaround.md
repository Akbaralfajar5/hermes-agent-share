# Vercel Yarn Workaround for npm Install Timeouts

## Problem

When deploying Next.js to Vercel, `npm install` can timeout with:
```
npm error Exit handler never called!
npm error This is an error with npm itself.
Error: Command "npm install" exited with 1
```

This happens even with:
- `--legacy-peer-deps` flag
- Simplified dependencies (removing wagmi/RainbowKit)
- Clean lockfile regeneration

## Root Cause

Vercel's build servers have npm timeout issues with certain dependency graphs, especially:
- Large dependency trees (wagmi + viem + RainbowKit = 400+ packages)
- Peer dependency conflicts
- Slow upstream registry responses

## Solution: Switch to Yarn

Create `vercel.json` to force Yarn instead of npm:

```json
{
  "installCommand": "yarn install",
  "buildCommand": "yarn build",
  "devCommand": "yarn dev",
  "framework": "nextjs"
}
```

**Why this works:**
- Yarn has better timeout handling than npm on Vercel's infra
- Yarn's lockfile resolution is more deterministic
- Vercel's build servers have Yarn pre-installed and optimized

## Deployment Flow

```bash
# 1. Add vercel.json with yarn config
cat > vercel.json << 'EOF'
{
  "installCommand": "yarn install",
  "buildCommand": "yarn build",
  "devCommand": "yarn dev",
  "framework": "nextjs"
}
EOF

# 2. Commit and deploy
git add vercel.json
git commit -m "Switch to yarn for Vercel"
vercel --token YOUR_TOKEN --yes --prod
```

## When to Use This vs Pre-built Deploy

| Scenario | Solution |
|----------|----------|
| npm install times out on Vercel | Try yarn workaround first (faster) |
| Yarn also fails | Fall back to pre-built deploy |
| Need to debug build issues locally | Use pre-built deploy |
| CI/CD pipeline | Pre-built deploy (more control) |

## Tested Configuration (May 2026)

**Working setup:**
- Next.js 14.2.18
- React 18.3.1
- Node.js 18.20.8 (local) / 20.x (Vercel)
- Yarn via vercel.json
- Simple dependencies (no wagmi/RainbowKit)

**Failed with npm:**
- Same setup but npm install (timeout after 60s)
- With `--legacy-peer-deps` flag (still timeout)
- With wagmi + RainbowKit (400+ packages, timeout)

## Alternative: Simplify Dependencies First

If yarn workaround doesn't work, try removing heavy dependencies:

```bash
# Remove wagmi/RainbowKit (adds 50+ packages)
npm uninstall wagmi viem @rainbow-me/rainbowkit @tanstack/react-query

# Use vanilla Next.js for MVP
# Add Web3 integration later via separate microservice or API route
```

## Pitfall: Don't Mix npm and yarn

If you switch to yarn in vercel.json, **delete package-lock.json** to avoid conflicts:

```bash
rm package-lock.json
git add -A
git commit -m "Remove npm lockfile, using yarn"
```

Vercel will generate `yarn.lock` automatically on first build.

## Session Context

This workaround emerged from deploying a Base chain airdrop hunter dashboard where:
1. npm install timed out 3+ times on Vercel
2. Pre-built deploy was attempted but complicated by Node version mismatch
3. Switching to yarn in vercel.json succeeded on first try
4. Build completed in 45s (vs 60s+ timeout with npm)

**Key insight:** Yarn is more reliable than npm on Vercel's build infrastructure as of 2026, especially for projects with complex dependency graphs.
