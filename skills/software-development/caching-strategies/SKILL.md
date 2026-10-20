---
name: caching-strategies
description: Caching at every layer — CDN, ISR/SSG, React Query, in-memory, Redis, database query caching. Use when pages are slow, API costs are high, or you're hitting rate limits. Covers Next.js caching (App Router), Supabase caching, and cache invalidation patterns.
---

# Caching Strategies

## Overview

Caching is the highest-ROI performance optimization. One well-placed cache can eliminate thousands of redundant computations, API calls, or database queries. The hard part is never setting cache — it's invalidation (knowing when to clear it).

## Caching Layers

```
Browser Cache → CDN → Edge/ISR → Server Memory → Redis → Database
  (fastest)                                              (slowest)
```

Each layer has different trade-offs:

| Layer | Latency | Invalidation | Best For |
|-------|---------|-------------|----------|
| Browser | 0ms | User clears cache | Static assets, API responses |
| CDN (Vercel) | ~10ms | Purge API / revalidate | Pages, images, API |
| Next.js ISR/SSG | ~10ms | on-demand / time-based | Dynamic pages |
| React Query | 0ms | invalidateQueries | Client-side API data |
| In-memory (Map) | 0ms | TTL / manual | Server-side hot data |
| Redis | ~1ms | TTL / pub/sub | Shared server state |
| Database | ~10ms | Native | Persistent data |

## Next.js Caching (App Router)

### Static Generation (SSG)

```typescript
// Static page — generated at build time, served from CDN
export default async function AboutPage() {
  const data = await getData(); // runs at build time
  return <div>{data.content}</div>;
}
```

### Incremental Static Regeneration (ISR)

```typescript
// Re-generates every 60 seconds, serves stale while revalidating
export const revalidate = 60; // seconds

export default async function ProductPage({ params }: { params: { id: string } }) {
  const product = await getProduct(params.id); // cached, revalidated
  return <ProductCard product={product} />;
}
```

### On-Demand Revalidation

```typescript
// src/app/api/revalidate/route.ts
import { revalidatePath, revalidateTag } from 'next/cache';
import { NextRequest } from 'next/server';

export async function POST(request: NextRequest) {
  const { path, tag, secret } = await request.json();

  if (secret !== process.env.REVALIDATE_SECRET) {
    return Response.json({ error: 'Invalid secret' }, { status: 401 });
  }

  if (path) revalidatePath(path);     // revalidate specific page
  if (tag) revalidateTag(tag);        // revalidate by tag

  return Response.json({ revalidated: true });
}

// Usage in data fetching:
async function getProduct(id: string) {
  const res = await fetch(`https://api.example.com/products/${id}`, {
    next: { tags: [`product-${id}`] },  // tag for targeted revalidation
  });
  return res.json();
}
```

### fetch() Cache Options

```typescript
// Cached (default in App Router)
const data = await fetch('https://api.example.com/data');

// Force no-cache
const data = await fetch('https://api.example.com/data', {
  cache: 'no-store'
});

// Revalidate every 10 minutes
const data = await fetch('https://api.example.com/data', {
  next: { revalidate: 600 }
});

// Tag for on-demand revalidation
const data = await fetch('https://api.example.com/data', {
  next: { tags: ['products'] }
});
```

## React Query (Client-Side)

```typescript
import { useQuery, useQueryClient } from '@tanstack/react-query';

// Global defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 min before considered stale
      gcTime: 10 * 60 * 1000,       // 10 min before garbage collected
      refetchOnWindowFocus: true,    // refetch when user returns
    },
  },
});

// Per-query configuration
const { data } = useQuery({
  queryKey: ['products', category],
  queryFn: () => fetchProducts(category),
  staleTime: 10 * 60 * 1000,  // 10 min — category data changes rarely
});

// Prefetch (warm the cache)
queryClient.prefetchQuery({
  queryKey: ['product', id],
  queryFn: () => fetchProduct(id),
});

// Invalidate (force refetch)
queryClient.invalidateQueries({ queryKey: ['products'] });

// Optimistic update
useMutation({
  mutationFn: updateProduct,
  onMutate: async (newData) => {
    await queryClient.cancelQueries({ queryKey: ['product', id] });
    const previous = queryClient.getQueryData(['product', id]);
    queryClient.setQueryData(['product', id], newData);
    return { previous };
  },
  onError: (err, newData, context) => {
    queryClient.setQueryData(['product', id], context?.previous);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['product', id] });
  },
});
```

### Stale-While-Revalidate Pattern

```
Request → Cache Hit (stale data) → Return immediately
              │
              └→ Background refetch → Update cache → Re-render with fresh data

User sees: instant response + eventual freshness
```

## Redis Caching

For server-side shared state across requests/servers.

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

// Basic cache-aside pattern
async function getProduct(id: string) {
  const cacheKey = `product:${id}`;

  // 1. Check cache
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  // 2. Cache miss → fetch from DB
  const product = await db.products.findById(id);

  // 3. Store in cache (TTL: 1 hour)
  await redis.setex(cacheKey, 3600, JSON.stringify(product));

  return product;
}

// Cache invalidation
async function updateProduct(id: string, data: Partial<Product>) {
  await db.products.update(id, data);
  await redis.del(`product:${id}`);  // invalidate cache
}
```

### Cache Patterns

**Cache-Aside (Lazy Loading):**
```
Read: Check cache → Miss? → Fetch DB → Store in cache → Return
Write: Update DB → Delete cache (not update!)
```

**Write-Through:**
```
Write: Update cache AND DB simultaneously
Read: Always from cache
```

**Write-Behind (Async):**
```
Write: Update cache → Async write to DB
Read: Always from cache
⚠️ Risk: data loss if cache dies before DB write
```

## In-Memory Cache (No Redis)

For single-server setups or when Redis is overkill.

```typescript
const cache = new Map<string, { data: any; expiry: number }>();

function getCached<T>(key: string, ttlMs: number, fetcher: () => Promise<T>): Promise<T> {
  const entry = cache.get(key);
  if (entry && entry.expiry > Date.now()) return entry.data;

  return fetcher().then(data => {
    cache.set(key, { data, expiry: Date.now() + ttlMs });
    return data;
  });
}

// Usage
const config = await getCached('app-config', 5 * 60 * 1000, () =>
  db.config.findFirst()
);
```

## Cache Invalidation Strategies

### Time-Based (TTL)

```typescript
// Simple and predictable
await redis.setex(key, 3600, value); // expires in 1 hour
```

### Event-Based

```typescript
// Invalidate when data changes
async function onProductUpdate(id: string) {
  await redis.del(`product:${id}`);
  // Or use pub/sub for multi-server
  await redis.publish('cache-invalidate', JSON.stringify({ type: 'product', id }));
}
```

### Tag-Based

```typescript
// Next.js tag-based revalidation
fetch('/api/products', { next: { tags: ['products', `product-${id}`] } });

// Revalidate all products
revalidateTag('products');

// Revalidate specific product
revalidateTag(`product-${id}`);
```

## Supabase Caching

```typescript
// Supabase has built-in caching via PostgREST
// But for frequent queries, add application-level caching

// React Query wrapper for Supabase
function useSupabaseQuery<T>(
  table: string,
  query: string,
  options?: { staleTime?: number }
) {
  return useQuery({
    queryKey: [table, query],
    queryFn: async () => {
      const { data, error } = await supabase.rpc(query);
      if (error) throw error;
      return data as T;
    },
    staleTime: options?.staleTime ?? 5 * 60 * 1000,
  });
}
```

## CDN Caching (Vercel)

```typescript
// API route with CDN caching
export async function GET() {
  const data = await fetchExpensiveData();

  return Response.json(data, {
    headers: {
      'Cache-Control': 'public, s-maxage=3600, stale-while-revalidate=86400',
      // CDN caches for 1 hour, serves stale for up to 24 hours while revalidating
    },
  });
}
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "We don't need caching yet" | Caching is easiest to add at the start. Retrofitting is painful |
| "Just add Redis" | Redis adds complexity. Start with Next.js ISR/SSG + React Query |
| "Cache invalidation is too hard" | TTL is trivial. Event-based is straightforward. Only complex patterns need thought |
| "Users always need fresh data" | Define "fresh." 30 seconds? 5 minutes? Most data has acceptable staleness |
| "In-memory cache is fine" | Only for single-server. Multi-server = need shared cache (Redis) |

## Red Flags

- Same API called multiple times per page load
- No staleTime set on React Query (defaults to 0 = always stale)
- Cache updated directly instead of invalidated (leads to inconsistency)
- Cache keys not including all query parameters
- No TTL on cached data (memory leak / stale forever)
- CDN cache headers missing on static API responses

## Verification

- [ ] Static pages use SSG/ISR with appropriate revalidation
- [ ] React Query staleTime set per query (not always 0)
- [ ] API responses have Cache-Control headers
- [ ] Cache invalidation triggered on write operations
- [ ] Cache keys are unique and include relevant parameters
- [ ] TTL set on all cached data
- [ ] No cache stampede (concurrent miss → thundering herd)
