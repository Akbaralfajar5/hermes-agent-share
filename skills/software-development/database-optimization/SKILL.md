---
name: database-optimization
description: Query performance tuning, indexing strategies, connection pooling, and Supabase/PostgreSQL optimization. Use when queries are slow, when designing schemas, when scaling read/write patterns, or when Supabase RLS policies need optimization. Covers EXPLAIN ANALYZE, index types, N+1 detection, and Supabase-specific patterns.
---

# Database Optimization

## Overview

Most database performance problems come from a few root causes: missing indexes, N+1 queries, unoptimized joins, and poor schema design. Measure first with EXPLAIN ANALYZE, then fix the actual bottleneck.

## When to Use

- Queries taking >100ms that should be fast
- Building new features that add database queries
- Schema design for new tables
- Supabase RLS policies slowing down reads
- Scaling from prototype to production
- "It works locally but is slow in production"

**When NOT to use:** Simple CRUD with <1000 rows, prototype phase where speed matters more than performance.

## Quick Diagnostics

### Step 1: Find Slow Queries

**PostgreSQL/Supabase:**
```sql
-- Enable query logging (Supabase dashboard → Database → Query Logs)
-- Or use pg_stat_statements extension
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 20;
```

**Supabase Dashboard:**
- Database → Query Performance (shows slow queries)
- Database → Indexes (shows unused/missing indexes)

### Step 2: EXPLAIN ANALYZE

```sql
-- Always wrap with ANALYZE to get actual timings
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM tasks WHERE user_id = 'abc' AND status = 'pending';

-- Look for:
-- Seq Scan → missing index
-- Nested Loop with high row count → N+1
-- Sort → consider index on ORDER BY columns
-- Hash Join on large tables → check join columns indexed
```

### Step 3: Check Index Usage

```sql
-- Find unused indexes (wasting write performance)
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
WHERE idx_scan = 0 AND indexname NOT LIKE '%pkey%'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Find missing indexes (table scans on large tables)
SELECT relname, seq_scan, idx_scan,
       seq_scan::float / NULLIF(idx_scan + seq_scan, 0) AS seq_scan_ratio
FROM pg_stat_user_tables
WHERE seq_scan > 100
ORDER BY seq_scan_ratio DESC;
```

## Indexing Strategies

### B-tree (Default)

Best for: equality, range, sorting, LIKE 'prefix%'

```sql
-- Single column
CREATE INDEX idx_tasks_user_id ON tasks(user_id);

-- Composite (order matters: most selective first, or match query WHERE)
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);

-- Covering index (includes extra columns to avoid table lookup)
CREATE INDEX idx_tasks_covering ON tasks(user_id, status) INCLUDE (title, created_at);
```

### GIN (Generalized Inverted Index)

Best for: full-text search, JSONB containment, arrays

```sql
-- JSONB containment
CREATE INDEX idx_metadata ON items USING GIN(metadata);
-- Then: SELECT * FROM items WHERE metadata @> '{"type": "premium"}';

-- Full text search
CREATE INDEX idx_search ON articles USING GIN(to_tsvector('english', title || ' ' || body));
```

### Partial Index

Best for: queries that always filter on same condition

```sql
-- Only index active tasks (smaller, faster)
CREATE INDEX idx_active_tasks ON tasks(user_id) WHERE status = 'pending';

-- Only index recent data
CREATE INDEX idx_recent_orders ON orders(created_at) WHERE created_at > '2025-01-01';
```

### Index Anti-Patterns

```
DON'T:
- Index every column (slows writes, wastes storage)
- Index small tables (<1000 rows, seq scan is faster)
- Use indexes on columns with very low cardinality (boolean)
- Create redundant indexes (A,B covers A alone)
```

## N+1 Query Detection

### The Pattern

```typescript
// BAD: N+1 — 1 query for users, N queries for tasks
const users = await db.query('SELECT * FROM users');
for (const user of users) {
  user.tasks = await db.query('SELECT * FROM tasks WHERE user_id = $1', [user.id]);
}
// 100 users = 101 queries!
```

### The Fix

```typescript
// GOOD: JOIN or IN clause — 1-2 queries total
const usersWithTasks = await db.query(`
  SELECT u.*, json_agg(t.*) as tasks
  FROM users u
  LEFT JOIN tasks t ON t.user_id = u.id
  GROUP BY u.id
`);

// Or batch with IN clause
const userIds = users.map(u => u.id);
const tasks = await db.query(
  'SELECT * FROM tasks WHERE user_id = ANY($1)', [userIds]
);
```

### Supabase Specific

```typescript
// BAD: N+1 with Supabase client
const { data: users } = await supabase.from('users').select('*');
for (const user of users) {
  const { data } = await supabase.from('tasks').select('*').eq('user_id', user.id);
}

// GOOD: Use Supabase joins
const { data } = await supabase
  .from('users')
  .select('*, tasks(*)')  // automatic join!
```

## Supabase RLS Optimization

RLS policies run on every query. Slow policies = slow app.

```sql
-- BAD: RLS with subquery (runs per row)
CREATE POLICY "users see own tasks" ON tasks
  FOR SELECT USING (
    user_id IN (SELECT id FROM users WHERE auth.uid() = users.auth_id)
  );

-- GOOD: Direct auth check (fast)
CREATE POLICY "users see own tasks" ON tasks
  FOR SELECT USING (auth.uid() = user_id);

-- GOOD: Use security definer function for complex checks
CREATE OR REPLACE FUNCTION is_org_member(org_id UUID)
RETURNS BOOLEAN AS $$
  SELECT EXISTS (
    SELECT 1 FROM org_members
    WHERE org_id = $1 AND user_id = auth.uid()
  );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

CREATE POLICY "org members see org data" ON projects
  FOR SELECT USING (is_org_member(org_id));
```

### RLS Performance Checklist

- [ ] No correlated subqueries in RLS policies
- [ ] auth.uid() calls are direct, not wrapped in functions (unless SECURITY DEFINER)
- [ ] Columns used in RLS are indexed
- [ ] RLS policies tested with EXPLAIN ANALYZE
- [ ] Consider SECURITY DEFINER functions for complex auth checks

## Schema Design Patterns

### Soft Delete

```sql
-- Add deleted_at instead of hard delete
ALTER TABLE tasks ADD COLUMN deleted_at TIMESTAMPTZ;

-- Partial index for active queries (most common)
CREATE INDEX idx_tasks_active ON tasks(user_id) WHERE deleted_at IS NULL;

-- Query pattern
SELECT * FROM tasks WHERE user_id = $1 AND deleted_at IS NULL;
```

### Timestamps

```sql
-- Always add these
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

### UUID vs BigSerial

```
UUID (v4): Good for distributed systems, public-facing IDs, no sequential leak
BigSerial: Good for internal IDs, smaller storage, faster joins

Recommendation: UUID for public IDs, BigSerial for internal FKs
```

## Connection Pooling

**Supabase built-in:** Supabase uses PgBouncer on port 6543 (transaction mode).

**Self-hosted PostgreSQL:**
```bash
# PgBouncer config
[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

**Node.js (pg pool):**
```typescript
import { Pool } from 'pg';

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,           // max connections in pool
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It's fast now, no need to optimize" | Performance degrades with data growth. Index now while it's easy |
| "Just add more RAM" | RAM masks bad queries, doesn't fix them. Query optimization is free |
| "ORM handles optimization" | ORMs generate N+1 queries by default. You must configure eager loading |
| "We'll optimize later" | Schema changes in production are 10x harder than in development |
| "Indexes slow down writes" | True, but 10ms slower writes vs 100x faster reads is the right trade-off |

## Verification

- [ ] All queries on tables >1000 rows use indexes
- [ ] No N+1 patterns in hot paths
- [ ] RLS policies have no correlated subqueries
- [ ] EXPLAIN ANALYZE shows no sequential scans on large tables
- [ ] Connection pool sized appropriately (not default unlimited)
- [ ] Slow query logging enabled
