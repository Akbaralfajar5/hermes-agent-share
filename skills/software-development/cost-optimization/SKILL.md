---
name: cost-optimization
description: Manage and reduce costs across VPS, APIs, serverless, and SaaS. Use when free tier limits are near, when API costs are growing, when choosing between services, or when optimizing resource usage. Covers Vercel, Supabase, VPS, AI APIs, and Helius/Infura free tiers.
---

# Cost Optimization

## Overview

Costs grow silently. A VPS running idle, an API key hitting rate limits, a database with unoptimized queries — all drain money without visible symptoms. The goal: maximize value per dollar, exploit free tiers fully, and eliminate waste.

## Free Tier Cheat Sheet

### Vercel
```
Free (Hobby):
- 100GB bandwidth/month
- Serverless: 100GB-hrs
- 1000 build minutes/month
- 1 concurrent build
- Automatic HTTPS + CDN

Pro ($20/mo):
- 1TB bandwidth
- 6000 build minutes
- 3 concurrent builds
- Password protection, preview URLs
```

**Optimization:**
- Use ISR/SSG to reduce serverless invocations
- Optimize images (next/image) to reduce bandwidth
- Don't run dev builds on Vercel — use VPS for staging
- `--no-wait` on deploy to not block CI minutes

### Supabase
```
Free:
- 500MB database
- 1GB file storage
- 50,000 monthly active users
- 2GB bandwidth
- 7-day log retention

Pro ($25/mo):
- 8GB database
- 100GB file storage
- 250GB bandwidth
- 28-day log retention
```

**Optimization:**
- Monitor database size in dashboard
- Clean up old data regularly
- Use RLS efficiently (expensive policies = more CPU)
- Connection pooling (Supabase uses PgBouncer — always use port 6543)
- Don't store large blobs in DB — use Storage

### Helius (Solana)
```
Free:
- 100,000 credits/day
- 1 RPC endpoint
- WebSocket support

Paid (from $50/mo):
- More credits, faster, priority
```

**Optimization:**
- Cache RPC responses when possible
- Batch requests (getMultipleAccountsInfo vs individual calls)
- Don't poll — use WebSocket subscriptions
- Rate limit bot requests

### AI APIs (OpenAI, Anthropic, etc.)
```
Cost per 1M tokens (approximate):
- GPT-4o-mini: $0.15 input / $0.60 output
- GPT-4o: $2.50 input / $10.00 output
- Claude Sonnet: $3.00 input / $15.00 output
- DeepSeek V3: $0.27 input / $1.10 output
```

**Optimization:**
- Use cheaper models for simple tasks (mini/haiku)
- Cache prompts with system message reuse
- Compress context — don't send unnecessary history
- Use structured output (JSON mode) to reduce tokens
- Set max_tokens to avoid runaway responses

## VPS Cost Management

### Right-Sizing

```
Typical workloads:
- Bot (PM2, light API): 1 vCPU, 1GB RAM ($3-5/mo)
- Web app (Next.js dev/staging): 2 vCPU, 2GB RAM ($10-15/mo)
- Mining/compute: 2+ vCPU, 2GB+ RAM ($10+/mo)
- Database (self-hosted): 2 vCPU, 4GB RAM ($20/mo)
```

### Spot/Preemptible Instances

```
- 60-90% cheaper than on-demand
- Can be terminated with short notice
- Good for: batch jobs, mining, non-critical workloads
- Bad for: production databases, user-facing services
```

### Resource Monitoring

```bash
# Check actual usage vs provisioned
htop                    # CPU and memory
df -h                   # disk
vnstat                  # network bandwidth
pm2 monit               # process-level resources

# If consistently under 30% utilization → downsize
```

### Idle Resource Detection

```bash
# Find processes consuming resources for no reason
ps aux --sort=-%cpu | head -20
ps aux --sort=-%mem | head -20

# Check for zombie processes
ps aux | grep 'Z'

# Find large files eating disk
du -sh /* 2>/dev/null | sort -rh | head -10
du -sh ~/.pm2/logs/* 2>/dev/null | sort -rh
```

## API Cost Reduction

### Caching API Responses

```typescript
// Cache expensive API calls
const cache = new Map<string, { data: any; expiry: number }>();

async function cachedAPI<T>(key: string, fetcher: () => Promise<T>, ttlMs: number): Promise<T> {
  const cached = cache.get(key);
  if (cached && cached.expiry > Date.now()) return cached.data;

  const data = await fetcher();
  cache.set(key, { data, expiry: Date.now() + ttlMs });
  return data;
}

// Helius RPC — cache token metadata (changes rarely)
const metadata = await cachedAPI(
  `token:${mintAddress}`,
  () => helius.getTokenMetadata(mintAddress),
  24 * 60 * 60 * 1000 // 24 hours
);
```

### Batching Requests

```typescript
// BAD: 100 individual RPC calls
for (const address of addresses) {
  const balance = await connection.getBalance(new PublicKey(address));
}

// GOOD: 1 batched call
const keys = addresses.map(a => new PublicKey(a));
const balances = await connection.getMultipleAccountsInfo(keys);
```

### Rate Limiting

```typescript
import Bottleneck from 'bottleneck';

const limiter = new Bottleneck({
  maxConcurrent: 5,
  minTime: 200, // 5 requests per second
});

const limitedFetch = limiter.wrap(fetch);
// Now all calls through limitedFetch are rate-limited
```

## Database Cost Optimization

### Supabase Specific

```sql
-- Monitor database size
SELECT pg_size_pretty(pg_database_size(current_database()));

-- Find largest tables
SELECT
  schemaname || '.' || tablename AS table,
  pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;

-- Clean up old data
DELETE FROM logs WHERE created_at < now() - interval '30 days';
DELETE FROM sessions WHERE expires_at < now();

-- Vacuum to reclaim space
VACUUM FULL logs;
```

### Query Optimization = Cost Optimization

```sql
-- Slow query = more CPU = higher cost
-- Add indexes to reduce query time
CREATE INDEX idx_logs_created ON logs(created_at) WHERE created_at > '2025-01-01';

-- Use EXPLAIN ANALYZE to find expensive queries
EXPLAIN ANALYZE SELECT * FROM tasks WHERE user_id = 'abc';
```

## Build & Deploy Optimization

### Vercel Build Minutes

```bash
# Use Turbopack (faster builds)
next build --turbopack

# Cache node_modules
# Vercel auto-caches, but ensure package-lock.json is committed

# Skip builds for non-code changes
# Add to vercel.json:
{ "ignoreCommand": "git diff --quiet HEAD^ HEAD -- . ':!docs'" }
```

### Docker Image Size

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./
# Result: ~150MB instead of ~1GB
```

## Monitoring Costs

### Vercel

```bash
# Check usage
vercel usage --token "$VERCEL_TOKEN"

# Monitor in dashboard: vercel.com → Settings → Usage
```

### Supabase

```
Dashboard → Settings → Usage
- Database size
- Storage used
- Bandwidth
- MAU count
```

### AI API Spend

```bash
# OpenAI dashboard: platform.openai.com/usage
# Set hard limits: Settings → Limits → Hard limit

# Track per-session cost
const cost = (usage.prompt_tokens * 0.000003) + (usage.completion_tokens * 0.000015);
console.log(`Session cost: $${cost.toFixed(4)}`);
```

## Cost Decision Framework

```
When evaluating a service/tool:
1. What's the free tier? Can it last 6+ months?
2. What triggers the paid tier? (bandwidth, storage, users, API calls)
3. Can I optimize to stay free longer?
4. What's the cost per unit at scale?
5. Is there a cheaper alternative?
6. Is this a fixed cost or variable (usage-based)?
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It's only $5/month" | 10 services × $5 = $60/year. It adds up |
| "Free tier is enough forever" | Free tiers have limits. Know them before you hit them |
| "I'll optimize costs later" | Costs compound. A $50/month waste is $600/year |
| "I need the biggest VPS" | Check actual usage. Most bots run fine on 1GB RAM |
| "Paid = better" | Free tiers of Vercel, Supabase, and Railway are production-grade |

## Red Flags

- VPS CPU/memory consistently under 30% (downsize)
- API calls not cached (same data fetched repeatedly)
- Database queries returning large unfiltered datasets
- Build minutes wasted on non-code changes
- Logs growing without rotation
- Multiple services with overlapping functionality
- No spend alerts or hard limits set

## Verification

- [ ] Free tier limits known for all services
- [ ] Spend alerts configured (Vercel, Supabase, AI APIs)
- [ ] VPS right-sized (check actual usage vs provisioned)
- [ ] API responses cached where appropriate
- [ ] Database queries optimized (no full table scans)
- [ ] Log rotation configured
- [ ] Build minutes optimized (Turbopack, skip non-code)
- [ ] Hard limits set on AI API spend
