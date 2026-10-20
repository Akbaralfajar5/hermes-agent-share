---
name: error-handling-resilience
description: Production-grade error handling — try/catch patterns, error boundaries, retry with backoff, graceful degradation, fallback UI. Use when building features that call APIs, handle user input, or interact with external services. Covers React error boundaries, API error handling, and resilience patterns.
---

# Error Handling & Resilience

## Overview

Errors are not exceptional — they're expected. The question is never "will this fail?" but "what happens when it fails?" Good error handling means users see helpful messages, not stack traces. Systems degrade gracefully, not catastrophically.

## When to Use

- Building features that call APIs or external services
- Handling user input that could be invalid
- Processing data that might be missing or malformed
- Features that need to work offline or with poor connectivity
- Any code path where failure is possible

**When NOT to use:** Truly impossible states (compiler-verified), throwaway scripts.

## Error Classification

```
┌─────────────────────────────────────────────┐
│ Recoverable          │ Unrecoverable         │
│──────────────────────│───────────────────────│
│ API timeout          │ Out of memory         │
│ Network error        │ Corrupted state       │
│ Validation failure   │ Missing critical env  │
│ Rate limit           │ Database corruption   │
│ 404 / not found      │                       │
│ Permission denied    │                       │
├──────────────────────┴───────────────────────┤
│ Strategy:                                    │
│ Recoverable → show error, retry, fallback    │
│ Unrecoverable → crash boundary, alert, log   │
└─────────────────────────────────────────────┘
```

## Pattern 1: Try/Catch with Typed Errors

```typescript
// Define error types
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number = 500,
    public isOperational: boolean = true
  ) {
    super(message);
    this.name = 'AppError';
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} ${id} not found`, 'NOT_FOUND', 404);
  }
}

class ValidationError extends AppError {
  constructor(public fields: Record<string, string>) {
    super('Validation failed', 'VALIDATION_ERROR', 400);
  }
}

// Usage
async function getUser(id: string) {
  const user = await db.users.findById(id);
  if (!user) throw new NotFoundError('User', id);
  return user;
}

// Handler
try {
  const user = await getUser(id);
} catch (error) {
  if (error instanceof NotFoundError) {
    return Response.json({ error: error.message }, { status: 404 });
  }
  if (error instanceof ValidationError) {
    return Response.json({ error: error.message, fields: error.fields }, { status: 400 });
  }
  // Unexpected error — log and return generic message
  console.error('Unexpected error:', error);
  return Response.json({ error: 'Internal server error' }, { status: 500 });
}
```

## Pattern 2: Result Type (No Throws)

```typescript
type Result<T, E = Error> =
  | { ok: true; data: T }
  | { ok: false; error: E };

async function safeFetch<T>(url: string): Promise<Result<T>> {
  try {
    const res = await fetch(url);
    if (!res.ok) return { ok: false, error: new Error(`HTTP ${res.status}`) };
    return { ok: true, data: await res.json() };
  } catch (error) {
    return { ok: false, error: error as Error };
  }
}

// Usage — explicit error handling, no try/catch
const result = await safeFetch<User>('/api/user');
if (!result.ok) {
  showError(result.error.message);
  return;
}
renderUser(result.data);
```

## Pattern 3: React Error Boundaries

```tsx
// components/ErrorBoundary.tsx
'use client';

import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, info: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    this.props.onError?.(error, info);
    // Log to error reporting service
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="p-4 bg-red-50 border border-red-200 rounded">
          <h2 className="text-red-800 font-semibold">Something went wrong</h2>
          <p className="text-red-600 text-sm">{this.state.error?.message}</p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="mt-2 text-sm text-red-700 underline"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Usage — wrap risky sections
<ErrorBoundary fallback={<p>Failed to load chart</p>}>
  <ExpensiveChart data={data} />
</ErrorBoundary>
```

### Next.js App Router Error Boundary

```tsx
// app/dashboard/error.tsx
'use client';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="p-8 text-center">
      <h2 className="text-xl font-bold">Something went wrong</h2>
      <p className="text-gray-600 mt-2">{error.message}</p>
      <button onClick={reset} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">
        Try again
      </button>
    </div>
  );
}
```

## Pattern 4: Retry with Exponential Backoff

```typescript
async function retry<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; baseDelay?: number; maxDelay?: number } = {}
): Promise<T> {
  const { maxAttempts = 3, baseDelay = 1000, maxDelay = 30000 } = options;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      if (attempt === maxAttempts) throw error;

      // Exponential backoff with jitter
      const delay = Math.min(baseDelay * 2 ** (attempt - 1), maxDelay);
      const jitter = delay * 0.5 * Math.random();
      await new Promise(r => setTimeout(r, delay + jitter));

      console.log(`Retry ${attempt}/${maxAttempts} after ${Math.round(delay + jitter)}ms`);
    }
  }
  throw new Error('Unreachable');
}

// Usage
const data = await retry(() => fetch('/api/data'), { maxAttempts: 3 });
```

### When to Retry

```
Retry:     408, 429, 500, 502, 503, 504, network errors, timeouts
Don't retry: 400, 401, 403, 404, 422 (client errors — fix the request)
```

## Pattern 5: Graceful Degradation

```typescript
// Feature with fallback
async function getRecommendations(userId: string): Promise<Product[]> {
  try {
    // Primary: personalized recommendations
    return await fetch(`/api/recommendations/${userId}`).then(r => r.json());
  } catch {
    try {
      // Fallback: popular products
      return await fetch('/api/products/popular').then(r => r.json());
    } catch {
      // Last resort: static defaults
      return DEFAULT_PRODUCTS;
    }
  }
}

// UI with loading states
function ProductPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
    retry: 2,
  });

  if (isLoading) return <ProductSkeleton />;
  if (error) return <ErrorState message="Failed to load products" onRetry={refetch} />;
  if (!data?.length) return <EmptyState message="No products found" />;
  return <ProductGrid products={data} />;
}
```

## Pattern 6: API Route Error Handling

```typescript
// src/app/api/tasks/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Validation
    const parsed = TaskSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json(
        { error: 'Validation failed', fields: parsed.error.flatten().fieldErrors },
        { status: 400 }
      );
    }

    // Auth check
    const session = await getServerSession();
    if (!session) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Business logic
    const task = await createTask(parsed.data, session.user.id);
    return NextResponse.json(task, { status: 201 });

  } catch (error) {
    // Log full error internally
    console.error('POST /api/tasks error:', error);

    // Return safe message to client
    if (error instanceof AppError) {
      return NextResponse.json({ error: error.message }, { status: error.statusCode });
    }
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}
```

## Pattern 7: Circuit Breaker

For external services that might be down.

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold: number = 5,
    private timeout: number = 60000 // 1 minute
  ) {}

  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }
}

// Usage
const breaker = new CircuitBreaker(5, 60000);
const data = await breaker.call(() => fetchExternalAPI());
```

## Error Logging

```typescript
// Structured error logging
function logError(error: Error, context: Record<string, any> = {}) {
  console.error(JSON.stringify({
    timestamp: new Date().toISOString(),
    level: 'error',
    message: error.message,
    code: error instanceof AppError ? error.code : 'UNKNOWN',
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    ...context,
  }));
}

// Usage
logError(error, { userId, endpoint: '/api/tasks', method: 'POST' });
```

## Anti-Rationalization

| Excuse | Reality |
|--------|---------|
| "It works, errors won't happen" | Network fails, APIs timeout, users input garbage. Always handle errors |
| "I'll add error handling later" | Later never comes. Handle errors at write time |
| "Just catch everything at the top" | Top-level catch can't provide context-specific recovery |
| "Console.log is enough for errors" | Users see nothing. Structured logging + user-facing messages |
| "Retry will fix it" | Retry without backoff creates thundering herd. Retry without limit creates infinite loops |

## Red Flags

- Empty catch blocks `catch (e) {}` — errors silently swallowed
- Generic "Something went wrong" for every error — not helpful
- Stack traces shown to users — security risk
- No retry on transient failures (network, 503)
- No loading/error states in UI — blank screen on failure
- All errors treated the same (validation vs server error vs not found)

## Verification

- [ ] All API calls wrapped in try/catch or safeFetch
- [ ] Error boundaries wrap major UI sections
- [ ] Retry with backoff on transient failures
- [ ] Typed errors with appropriate HTTP status codes
- [ ] User-friendly error messages (no stack traces)
- [ ] Errors logged with context (user, endpoint, params)
- [ ] Loading and error states in all data-fetching components
- [ ] Circuit breaker on unreliable external services
