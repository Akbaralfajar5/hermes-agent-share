# Supabase + Next.js 14 App Router Pattern

Complete reference for inventory/CRUD apps with Supabase auth, RLS, realtime, and role-based access.

## Package Versions (Tested)

```json
"@supabase/supabase-js": "^2.45.4",
"@supabase/ssr": "^0.5.1",
"next": "14.2.35"
```

## ⚠️ `@supabase/ssr` Type Conflict (Next.js 14 + `@types/react` v18)

`@supabase/ssr` uses `ResponseCookie` from `next/dist/compiled/@edge-runtime/cookies` which conflicts with `@types/react` v18 type definitions. Symptoms: build fails with type errors in `setAll()` callback.

**Workaround:** Skip `@supabase/ssr` entirely. Use `@supabase/supabase-js` directly:
- Browser client: `createClient()` singleton in `lib/supabase.ts`
- Server auth: read `sb-access-token` cookie manually via `cookies()` from `next/headers`
- Middleware: check cookie presence manually (no `createServerClient`)
- Split into `auth-server.ts` (server components only) and `auth-client.ts` (client components)


## Middleware (Required for Session Refresh)

```ts
// src/middleware.ts
import { createServerClient } from '@supabase/ssr';
import { NextResponse, type NextRequest } from 'next/server';

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll(); },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          );
        },
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();
  const { pathname } = request.nextUrl;

  if (pathname === '/login') {
    if (user) return NextResponse.redirect(new URL('/dashboard', request.url));
    return supabaseResponse;
  }

  if (!user && pathname !== '/login') {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return supabaseResponse;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
};
```

## Complete Schema SQL

Run in Supabase SQL editor (Dashboard → SQL Editor → New Query).

```sql
-- ============================================================
-- 1. PROFILES (extends auth.users)
-- ============================================================
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  nama TEXT NOT NULL,
  email TEXT,                          -- store email for display in admin panel
  role TEXT NOT NULL CHECK (role IN ('siswa', 'guru')) DEFAULT 'siswa',
  kelas TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view all profiles" ON profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Service role can insert profiles" ON profiles FOR INSERT WITH CHECK (true);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, nama, role, kelas)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'nama', NEW.email),
    COALESCE(NEW.raw_user_meta_data->>'role', 'siswa'),
    NEW.raw_user_meta_data->>'kelas'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- 2. BAHAN_KIMIA (inventory items)
-- ============================================================
CREATE TABLE bahan_kimia (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nama TEXT NOT NULL,
  satuan TEXT NOT NULL,
  stok_saat_ini NUMERIC NOT NULL DEFAULT 0,
  stok_minimum NUMERIC NOT NULL DEFAULT 0,
  kategori TEXT NOT NULL DEFAULT 'Umum',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE bahan_kimia ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view bahan_kimia" ON bahan_kimia FOR SELECT USING (true);
CREATE POLICY "Guru can insert bahan_kimia" ON bahan_kimia FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'guru'));
CREATE POLICY "Guru can update bahan_kimia" ON bahan_kimia FOR UPDATE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'guru'));
CREATE POLICY "Guru can delete bahan_kimia" ON bahan_kimia FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'guru'));

-- Enable realtime
ALTER PUBLICATION supabase_realtime ADD TABLE bahan_kimia;

-- ============================================================
-- 3. PEMAKAIAN (usage log)
-- ============================================================
CREATE TABLE pemakaian (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  bahan_id UUID NOT NULL REFERENCES bahan_kimia(id) ON DELETE CASCADE,
  jumlah NUMERIC NOT NULL,
  keterangan TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE pemakaian ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view pemakaian" ON pemakaian FOR SELECT USING (true);
CREATE POLICY "Authenticated users can insert pemakaian" ON pemakaian FOR INSERT
  WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Guru can delete pemakaian" ON pemakaian FOR DELETE
  USING (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'guru'));

-- Auto-deduct stock on insert
CREATE OR REPLACE FUNCTION deduct_stock()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE bahan_kimia
  SET stok_saat_ini = stok_saat_ini - NEW.jumlah
  WHERE id = NEW.bahan_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_pemakaian_insert
  AFTER INSERT ON pemakaian
  FOR EACH ROW EXECUTE FUNCTION deduct_stock();

-- ============================================================
-- 4. RESTOCK (stock additions)
-- ============================================================
CREATE TABLE restock (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  bahan_id UUID NOT NULL REFERENCES bahan_kimia(id) ON DELETE CASCADE,
  jumlah NUMERIC NOT NULL,
  keterangan TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE restock ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Anyone can view restock" ON restock FOR SELECT USING (true);
CREATE POLICY "Guru can insert restock" ON restock FOR INSERT
  WITH CHECK (EXISTS (SELECT 1 FROM profiles WHERE id = auth.uid() AND role = 'guru'));

-- Auto-add stock on restock insert
CREATE OR REPLACE FUNCTION add_stock()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE bahan_kimia
  SET stok_saat_ini = stok_saat_ini + NEW.jumlah
  WHERE id = NEW.bahan_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_restock_insert
  AFTER INSERT ON restock
  FOR EACH ROW EXECUTE FUNCTION add_stock();
```


```
Background:  #1A1A2E  (dark navy)
Sidebar bg:  #151525
Primary:     #2B4EA2  (blue)
Accent:      #E91E7B  (pink)
Green:       #2E8B3A
Gold:        #F5C518
Text:        white / rgba(255,255,255,0.6) muted
Cards:       rgba(255,255,255,0.05) bg + rgba(255,255,255,0.1) border
Low stock:   rgba(239,68,68,0.08) bg + #f87171 text
```

## Key Global CSS Classes

```css
.glass-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(10px); border-radius: 12px; }
.dark-input { background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: white; padding: 10px 14px; }
.dark-input:focus { border-color: #2B4EA2; background: rgba(43,78,162,0.1); }
.btn-primary { background: #2B4EA2; color: white; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
.btn-accent  { background: #E91E7B; color: white; border-radius: 8px; padding: 10px 20px; font-weight: 600; }
.badge-low-stock { background: rgba(239,68,68,0.2); color: #f87171; border: 1px solid rgba(239,68,68,0.4); border-radius: 20px; padding: 2px 10px; font-size: 0.7rem; }
.dark-table th { background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.7); font-size: 0.75rem; text-transform: uppercase; }
.dark-table td { border-bottom: 1px solid rgba(255,255,255,0.05); color: rgba(255,255,255,0.85); }
.dark-table tr.low-stock td { background: rgba(239,68,68,0.08); }
```

## Supabase Dashboard Setup Checklist

1. Create project at supabase.com
2. Run schema SQL above in SQL Editor
3. Enable Email auth in Authentication → Providers
4. (Optional) Disable email confirmation for school use: Auth → Settings → "Confirm email" OFF
5. Copy Project URL + anon key to `.env.local`
6. Test realtime: Dashboard → Table Editor → bahan_kimia → enable realtime toggle
7. **Create guru account manually:** Authentication → Users → Add user → fill email + password → confirm
8. **Set guru role via SQL:** `UPDATE profiles SET role = 'guru' WHERE email = 'email@sekolah.sch.id';`
   (The trigger creates all new users with role='siswa' by default — always needs this UPDATE)
9. **Set Auth redirect URLs:** Authentication → Settings → Site URL = `https://your-app.vercel.app`, Redirect URLs = `https://your-app.vercel.app/**`
10. **Add SUPABASE_SERVICE_ROLE_KEY to Vercel env vars** (Settings → API → service_role key) — required for admin user management routes

## Joined Queries

```ts
// Pemakaian with user + bahan info
const { data } = await supabase
  .from('pemakaian')
  .select('*, profiles(nama, kelas, role), bahan_kimia(nama, satuan, kategori)')
  .order('created_at', { ascending: false })
  .limit(200);
```

TypeScript: cast result as `unknown as Pemakaian[]` when using joined fields (Supabase types don't auto-infer joins).
