# Public Homepage + Login-Gated App Pattern

Reference for Next.js + Supabase apps where the public homepage and browse pages are open (no login), and only mutations/admin pages require auth. Captured from a school chemistry inventory app that started login-only and was refactored to public-by-default.

## Architecture Overview

```
Public (no login)
├── /              homepage with dashboard + featured items
├── /bahan         full browseable list
└── /login         login page (with ?redirect= support)

Protected (cookie-gated by middleware)
├── /pakai         siswa + guru can use
├── /riwayat       siswa + guru can view
├── /kelola-bahan  guru only (role check in client)
└── /admin         guru only (role check in client)
```

## Key Decisions

1. **Middleware whitelists protected routes** instead of blacklisting `/login`. New public pages don't accidentally become login-gated.
2. **Public pages fetch via service role on server**, not anon key. Anon is blocked by default RLS — adding public RLS policies is more work than just using service role server-side.
3. **Client components restore session from cookie at mount**, not just `getUser()`. Catches the case where localStorage was cleared but cookie persists.
4. **Mutations go through API routes** with cookie verification, not direct client `supabase.from(...).insert()`. Reliable regardless of client session state.
5. **Login redirects back to original URL** via `?redirect=` query param.
6. **Role check is client-side on protected pages** that need `guru` access. Middleware only checks "logged in" — finer-grained role enforcement happens in the page itself with a friendly "Access Denied" UI.

## Middleware

```ts
// src/middleware.ts
import { NextResponse, type NextRequest } from 'next/server';

const PROTECTED_ROUTES = ['/pakai', '/riwayat', '/kelola-bahan', '/admin'];

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) return NextResponse.next();

  const token = request.cookies.get('sb-access-token')?.value;
  const isProtected = PROTECTED_ROUTES.some(
    (r) => pathname === r || pathname.startsWith(r + '/')
  );

  if (isProtected && !token) {
    const url = new URL('/login', request.url);
    url.searchParams.set('redirect', pathname);
    return NextResponse.redirect(url);
  }
  if (token && pathname === '/login') {
    return NextResponse.redirect(new URL('/', request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

## Public Page (Server Component)

```ts
// src/app/page.tsx
import { createClient } from '@supabase/supabase-js';
import TopNav from '@/components/TopNav';

export const revalidate = 0;
export const dynamic = 'force-dynamic';

function getPublicClient() {
  // Service role bypasses RLS. Safe — only runs server-side, never sent to client.
  return createClient(
    'https://yourref.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}

export default async function HomePage() {
  const supabase = getPublicClient();
  const { data } = await supabase.from('items').select('*').order('name');

  return (
    <div className="min-h-screen">
      <TopNav />
      <main>{/* render items */}</main>
    </div>
  );
}
```

## TopNav with Cookie-based Session Recovery

```tsx
// src/components/TopNav.tsx
'use client';

import { useState, useEffect } from 'react';
import { getSupabaseClient } from '@/lib/supabase';

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]+)`));
  return match ? decodeURIComponent(match[2]) : null;
}

export default function TopNav() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const supabase = getSupabaseClient();

    async function loadProfile() {
      // Restore session from cookie when localStorage is empty
      const access = getCookie('sb-access-token');
      const refresh = getCookie('sb-refresh-token');
      if (access && refresh) {
        await supabase.auth.setSession({
          access_token: access,
          refresh_token: refresh,
        });
      }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        if (mounted) setLoading(false);
        return;
      }

      const { data } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', user.id)
        .single();

      if (mounted) {
        if (data) setProfile(data);
        setLoading(false);
      }
    }

    loadProfile();
    return () => { mounted = false; };
  }, []);

  // Render nav based on `profile` (null = anon, with role = logged in)
}
```

## Login Page with `?redirect=` Support

```tsx
'use client';
import { Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { signIn } from '@/lib/auth';

function LoginInner() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || '/';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const { data, error } = await signIn(email, password);
    if (error) return; // show error
    if (data?.session) {
      const max = data.session.expires_in || 3600;
      document.cookie = `sb-access-token=${data.session.access_token}; path=/; max-age=${max}; SameSite=Lax`;
      document.cookie = `sb-refresh-token=${data.session.refresh_token}; path=/; max-age=${60*60*24*30}; SameSite=Lax`;
    }
    window.location.href = redirectTo; // hard redirect, not router.push
  }

  return <form onSubmit={handleSubmit}>{/* ... */}</form>;
}

export default function LoginPage() {
  return <Suspense fallback={<div />}><LoginInner /></Suspense>;
}
```

`Suspense` is required because `useSearchParams` is a client hook that needs Suspense boundary in App Router.

## Protected Client Page with Role Check

For pages like `/admin` and `/kelola-bahan` that need `role === 'guru'`:

```tsx
'use client';

export default function AdminPage() {
  const router = useRouter();
  const [authChecking, setAuthChecking] = useState(true);
  const [isGuru, setIsGuru] = useState(false);

  useEffect(() => {
    const supabase = getSupabaseClient();

    async function check() {
      // Same cookie-restore pattern
      const access = getCookie('sb-access-token');
      const refresh = getCookie('sb-refresh-token');
      if (access && refresh) {
        await supabase.auth.setSession({ access_token: access, refresh_token: refresh });
      }

      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        router.replace('/login?redirect=/admin');
        return;
      }
      const { data } = await supabase
        .from('profiles').select('role').eq('id', user.id).single();
      if (data?.role === 'guru') setIsGuru(true);
      setAuthChecking(false);
    }
    check();
  }, [router]);

  if (authChecking) return <Loader />;
  if (!isGuru) return <AccessDenied />;
  return <AdminUI />;
}
```

## Mutation API Route

```ts
// src/app/api/pakai/route.ts
import { createClient } from '@supabase/supabase-js';
import { NextRequest, NextResponse } from 'next/server';

function getAdminClient() {
  return createClient(
    'https://yourref.supabase.co',
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { autoRefreshToken: false, persistSession: false } }
  );
}

export async function POST(req: NextRequest) {
  const supabase = getAdminClient();

  // 1. Verify caller via cookie
  const token = req.cookies.get('sb-access-token')?.value;
  if (!token) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const { data: { user }, error: authErr } = await supabase.auth.getUser(token);
  if (authErr || !user) return NextResponse.json({ error: 'Invalid session' }, { status: 401 });

  // 2. Validate input
  const { bahan_id, jumlah, keterangan } = await req.json();
  // ... validation

  // 3. Business rule: check stock
  const { data: bahan } = await supabase.from('bahan_kimia').select('*').eq('id', bahan_id).single();
  if (!bahan || bahan.stok_saat_ini < jumlah) {
    return NextResponse.json({ error: 'Stok tidak cukup' }, { status: 400 });
  }

  // 4. Mutate with verified user.id (cannot be spoofed by client)
  await supabase.from('pemakaian').insert({
    user_id: user.id, bahan_id, jumlah, keterangan,
  });
  await supabase.from('bahan_kimia').update({
    stok_saat_ini: bahan.stok_saat_ini - jumlah
  }).eq('id', bahan_id);

  return NextResponse.json({ success: true });
}
```

Client just does:
```ts
await fetch('/api/pakai', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ bahan_id, jumlah, keterangan }),
});
```

## Why Service Role on Server Instead of Public RLS Policies

Two valid approaches when you want public read:

**A. Public RLS policy** — `CREATE POLICY "anyone read items" ON items FOR SELECT USING (true);`
- Pro: anon key works directly, realtime works out of the box for anon.
- Con: every table needs a policy. Easy to forget. RLS easy to misconfigure (e.g. `USING (true)` vs `WITH CHECK (true)`).

**B. Service role on server** — what this template uses
- Pro: works without any RLS changes. Server is trusted. No risk of anon getting more access than intended.
- Con: realtime in client only works for logged-in users (anon channel subscriptions fail because of default RLS).

For an app where realtime browsing as anon isn't critical, **option B is simpler and safer**. For collaborative public apps where every viewer should see live updates, go with option A and write the policies carefully.
