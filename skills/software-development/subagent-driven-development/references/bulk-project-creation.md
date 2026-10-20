# Bulk Project Creation with Subagents

When creating multiple full projects in one session (e.g., 7 portfolio apps), subagents timeout at 600s because building a full Next.js app requires 20-30+ tool calls (scaffold → write 15+ files → install deps → fix build errors → verify).

## The Problem

- Each full project build = 20-30 tool calls = 400-600s
- Subagent timeout = 600s → most projects time out mid-build
- Timed-out subagents leave partial code (scaffolded but incomplete)
- 3 parallel subagents × 600s = 30 minutes wasted on timeouts

## The Solution: Hybrid Controller + Subagent Pattern

### Phase 1: Scaffold ALL projects in controller (fast, mechanical)
Use `execute_code` for repetitive scaffolding — it's faster than subagents for mechanical work:

```python
for name in projects:
    terminal(f"npx create-next-app@14 {name} --typescript --tailwind --eslint --app --src-dir --import-alias '@/*' --use-npm")
    terminal(f"echo 'registry=https://registry.npmjs.org/' > {name}/.npmrc")
    terminal(f"cd {name} && npm install lucide-react framer-motion")
    # Write next.config.mjs with eslint: { ignoreDuringBuilds: true }
```

### Phase 2: Delegate code writing to subagents (max 3 concurrent)
Each subagent gets ONE project to write source files. Provide:
- Exact project directory path
- All feature requirements
- Known pitfalls to avoid (context providers, Tailwind syntax)
- Build verification command

```
goal: "Write ALL source files for [project]. Project dir: ~/projects/[name] (already scaffolded)."
context: "CRITICAL: All hooks must have 'use client'. Context providers must use createContext with default values..."
```

### Phase 3: Fix build errors in controller
Subagents introduce predictable bugs. Fix them in controller:
1. Context providers throwing during SSR → add default values
2. Tailwind v4 syntax in v3 project → replace `@import "tailwindcss"` with `@tailwind` directives
3. TypeScript type errors → fix `as const` to union types
4. ESLint errors → ensure `ignoreDuringBuilds: true`

### Phase 4: Deploy in controller
Use prebuilt approach for reliable deploys:
```bash
vercel build --prod --yes
vercel --prebuilt --prod --yes
```

## Key Rules

1. **Never delegate scaffolding** — it's mechanical, controller does it faster
2. **Never delegate deployment** — it's sequential, controller does it reliably
3. **Delegate code writing** — it's creative, subagents do it better
4. **Max 3 concurrent subagents** — more causes RAM pressure on VPS
5. **Always verify build after subagent** — subagents don't catch their own errors
6. **Fix build errors in controller** — it's faster than re-delegating

## Error Patterns (subagent-introduced)

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `useX must be used within XProvider` | `createContext(undefined)` + throw | Use `createContext({default})` |
| `Can't resolve 'tailwindcss'` | `@import "tailwindcss"` (v4 syntax) | Replace with `@tailwind base/components/utilities` |
| `Type 'X' not assignable to 'Y'` | `as const` narrowing | Use explicit union type |
| `Syntax Error` in build | Missing operator (e.g., `Date.now() new Date()`) | Read file, fix syntax |
