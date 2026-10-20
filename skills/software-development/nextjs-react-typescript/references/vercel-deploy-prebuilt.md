# Vercel Pre-built Deployment Pattern

## Problem
As of 2026, Vercel's remote `npm install` frequently fails with:
```
npm error Exit handler never called!
npm error This is an error with npm itself.
Error: Command "npm install" exited with 1
```

This happens regardless of lockfile state, Node version, or package configuration.

## Solution: Local Pre-build + Deploy

```bash
# Prerequisites
npm install -g vercel  # Install Vercel CLI globally
export VERCEL_TOKEN=vcp_xxxxx  # From https://vercel.com/account/tokens

# Step 1: Link project (first time only)
cd /path/to/nextjs-project
vercel pull --yes

# Step 2: Ensure package.json has correct engine
# "engines": { "node": "20.x" }
# NOT "18.x" (discontinued) or ">=18.0.0" (auto-upgrade warning)

# Step 3: Build locally
vercel build --prod
# This runs next build and outputs to .vercel/output/

# Step 4: Deploy pre-built artifacts
vercel deploy --prebuilt --prod --yes
# This uploads .vercel/output/ directly — NO remote npm install!
```

## Key Points
- `vercel build --prod` uses YOUR local node_modules (already installed)
- `--prebuilt` flag tells Vercel to skip build step entirely
- Output goes to `.vercel/output/` directory
- The deploy uploads ~1-2MB of built artifacts (not source + node_modules)

## Common Errors

| Error | Fix |
|-------|-----|
| "Node.js Version 18.x is discontinued" | Change engines to "20.x" |
| "No Project Settings found locally" | Run `vercel pull --yes` first |
| "npm install exited with 1" | Use `--prebuilt` approach |
| "Detected engines >=18.0.0 will auto upgrade" | Pin to exact "20.x" |

## Full Working Example (from session)

```bash
cd /home/ubuntu/my-site

# package.json already has: "engines": { "node": "20.x" }

# Pull project config
VERCEL_TOKEN=xxx vercel pull --yes
# Output: Linked to your-team/my-site

# Build locally (takes ~30s)
VERCEL_TOKEN=xxx vercel build --prod
# Output: Build Completed in .vercel/output [31s]

# Deploy (takes ~20s)
VERCEL_TOKEN=xxx vercel deploy --prebuilt --prod --yes
# Output: Production: https://my-site.vercel.app
```

## delegate_task Pattern for Full Website Build + Deploy

When building a complete website from scratch, use `delegate_task` for the coding, then handle deployment yourself:

```
1. delegate_task → create all source files + verify with npm run build
2. vercel pull --yes → link project
3. vercel build --prod → local build
4. vercel deploy --prebuilt --prod --yes → ship it
```

This separates concerns: subagent handles code quality, main agent handles deployment (which needs token management and error recovery).
